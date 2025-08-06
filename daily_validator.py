import os
import json
import uuid
import time
import base64
import shutil
import openai
import requests
import tempfile
import cv2
import difflib
import moviepy.editor as mp
from dotenv import load_dotenv
from datetime import datetime
from supabase import create_client, Client
from yt_dlp import YoutubeDL
from pathlib import Path
import numpy as np

load_dotenv()

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
APIFY_ACTOR_ID = "clockworks~free-tiktok-scraper"
openai.api_key = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

with open("hooks.json", "r", encoding="utf-8") as f:
    hook_data = json.load(f)

LONG_TEXT_HOOKS = hook_data["long_text_hooks"]
SHORT_TEXT_HOOKS = hook_data["short_text_hooks"]

def fetch_videos_from_apify(username):
    input_payload = {
        "profiles": [username],
        "resultsPerPage": 10,
        "excludePinnedPosts": True,
        "scrapePinnedPosts": False,
        "profileSorting": "latest"
    }
    headers = {"Authorization": f"Bearer {APIFY_API_TOKEN}"}
    trigger_url = f"https://api.apify.com/v2/acts/{APIFY_ACTOR_ID}/runs?token={APIFY_API_TOKEN}"
    run_response = requests.post(trigger_url, json=input_payload, headers=headers).json()
    run_id = run_response["data"]["id"]

    while True:
        status_resp = requests.get(f"https://api.apify.com/v2/actor-runs/{run_id}", headers=headers).json()
        status = status_resp["data"]["status"]
        if status in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
            break
        time.sleep(5)

    if status != "SUCCEEDED":
        print(f"Apify run failed for {username}")
        return []

    dataset_id = status_resp["data"]["defaultDatasetId"]
    items = requests.get(f"https://api.apify.com/v2/datasets/{dataset_id}/items?clean=true").json()
    now_ts = time.time()
    return [
        item for item in items
        if not item.get("isPinned") and "webVideoUrl" in item and item["createTime"] >= now_ts - 86400
    ]


def download_video(url, output_path):
    ydl_opts = {
        "format": "mp4",
        "outtmpl": str(output_path),
        "quiet": True
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def detect_face(image_path):
    img = cv2.imread(str(image_path))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4)
    return len(faces) > 0

def extract_metadata(video_path):
    clip = mp.VideoFileClip(str(video_path))
    duration = clip.duration
    temp_dir = Path(tempfile.mkdtemp())

    # Sample more frames across duration
    timestamps = [1, 2, 3, 4, 5]
    if duration > 6:
        timestamps += [6, 7, 8]

    frames = []
    face_presence = {}
    for t in timestamps:
        frame_path = temp_dir / f"frame_{t}.png"
        try:
            clip.save_frame(str(frame_path), t)
            frames.append(frame_path)
            if t in [3, 4, 5]:
                face_presence[t] = detect_face(frame_path)
        except Exception:
            continue

    clip.reader.close()
    if clip.audio:
        clip.audio.reader.close_proc()

    return duration, frames, face_presence

def ask_gpt_and_find_hook(duration, frames):
    extracted_texts = []
    for frame in frames:
        with open(frame, "rb") as f:
            image_bytes = f.read()
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")

        try:
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": (
                            "Please extract all overlay or subtitle text from this video frame. "
                            "Just return the visible words/text as plain text. No description or analysis."
                        )},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encoded_image}"}}
                    ]
                }],
                temperature=0.2
            )
            extracted_texts.append(response.choices[0].message.content.strip())
        except Exception:
            extracted_texts.append("")

    # Join all frame results
    joined_text = " ".join(extracted_texts).strip().lower()

    # Try to match exactly
    exact_short = any(h.lower() == joined_text for h in SHORT_TEXT_HOOKS)
    exact_long = any(h.lower() == joined_text for h in LONG_TEXT_HOOKS)

    # Try fuzzy match
    fuzzy_short = difflib.get_close_matches(joined_text, [h.lower() for h in SHORT_TEXT_HOOKS], n=1, cutoff=0.8)
    fuzzy_long = difflib.get_close_matches(joined_text, [h.lower() for h in LONG_TEXT_HOOKS], n=1, cutoff=0.8)

    matched_short = exact_short or bool(fuzzy_short)
    matched_long = exact_long or bool(fuzzy_long)

    return extracted_texts, joined_text, matched_short, matched_long

def store_result(username, url, duration, extracted_texts, joined_text, matched_short, matched_long, face_presence, upload_time):
    result = {
        "id": str(uuid.uuid4()),
        "username": username,
        "tiktok_url": url,
        "duration": duration,
        "validation_type": "",
        "status": "",
        "reason": "",
        "hook_text": joined_text,
        "created_at": upload_time
    }

    if 12 <= duration <= 18:
        result["validation_type"] = "Short Text + In-App Footage"
        face_ok = face_presence.get(3) and face_presence.get(4) and face_presence.get(5)
        passed = matched_short and face_ok
        reason = []
        if not matched_short: reason.append("hook not matched")
        if not face_ok: reason.append("face not detected at 3, 4, 5s")
        result["status"] = "pass" if passed else "fail"
        result["reason"] = ", ".join(reason)
    elif 6 <= duration <= 9:
        result["validation_type"] = "Long Text"
        passed = matched_long
        result["status"] = "pass" if passed else "fail"
        result["reason"] = "hook matched" if passed else "hook not matched"
    else:
        result["validation_type"] = "Unknown"
        result["status"] = "fail"
        result["reason"] = "duration out of expected range"
    supabase.table("validated_videos").insert(result).execute()

def validate_tiktok_profile(username):
    print(f"Validating {username}...")
    videos = fetch_videos_from_apify(username)
    if not videos:
        print(f"No recent non-pinned videos found for {username}")
        return

    for item in videos:
        url = item["webVideoUrl"]
        upload_time = datetime.utcfromtimestamp(item["createTime"]).isoformat()
        temp_path = Path(tempfile.mkdtemp()) / f"{username}.mp4"
        download_video(url, temp_path)
        duration, frames, face_presence = extract_metadata(temp_path)
        extracted_texts, joined_text, matched_short, matched_long = ask_gpt_and_find_hook(duration, frames)
        store_result(username, url, duration, extracted_texts, joined_text, matched_short, matched_long, face_presence, upload_time)
        shutil.rmtree(temp_path.parent)


def load_usernames(path="usernames.txt"):
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

if __name__ == "__main__":
    usernames = load_usernames()
    for user in usernames:
        validate_tiktok_profile(user)