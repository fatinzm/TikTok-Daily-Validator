# 🕵️‍♀️ Daily TikTok Scraper & Validator

This project automatically scrapes TikTok videos from specific profiles every 24 hours, downloads non-pinned posts uploaded in the last 24 hours, validates them using OpenAI GPT-4o, and stores the results in a Supabase database.

## 📦 Features

- ✅ Scrape TikTok videos using Apify (`free-tiktok-scraper` actor)
- ✅ Exclude pinned posts
- ✅ Download all videos published in the last 24 hours
- ✅ Detect face presence in key frames
- ✅ Extract text overlays using GPT-4o
- ✅ Match against predefined **hook phrases** (short & long formats)
- ✅ Validate video format:
  - **Short Text + In-App Footage** (12–18s, face at 3–5s, app footage, hook text)
  - **Long Text** (6–9s, fast background action, large readable text)
- ✅ Store results in Supabase
- ✅ Clean up videos after processing
- ✅ Schedule to run daily at a specified time

---

## 📁 Project Structure

```
📦 scraper/
 ┣ 📄 daily_validator.py           # Main script for daily video scraping & validation
 ┣ 📄 scheduler.py                 # (Optional) Local scheduler script using `schedule` library
 ┣ 📄 hooks.json                   # Contains predefined hook examples for validation
 ┣ 📄 usernames.txt                # List of TikTok usernames to scrape
 ┗ 📄 .env                         # Your environment variables
```

---

## 🛠 Requirements

- Python 3.10+
- [Supabase project](https://supabase.com/)
- Apify API token
- OpenAI API key (GPT-4o access)

Install dependencies:
```bash
pip install -r requirements.txt
```

---

## 🔐 Environment Variables (`.env`)

```
OPENAI_API_KEY=your-openai-key
SUPABASE_URL=your-supabase-url
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
APIFY_API_TOKEN=your-apify-token
```

---

## 🕓 Schedule Daily Runs (Optional)

To run the validator every day at 09:00 automatically:

```bash
python scheduler.py
```

You can edit the time in `scheduler.py` using:
```python
schedule.every().day.at("09:00").do(run_validator)
```

---

## 📊 Supabase Table Schema (`validated_videos`)

| Column         | Type    | Description                                 |
|----------------|---------|---------------------------------------------|
| id             | UUID    | Unique ID for the record                    |
| username       | Text    | TikTok profile name                         |
| tiktok_url     | Text    | Link to the validated video                 |
| duration       | Float   | Duration in seconds                         |
| validation_type| Text    | Format: `Short Text + In-App` or `Long Text`|
| status         | Text    | `pass` or `fail`                            |
| reason         | Text    | Reason for failure or success               |
| hook_text      | Text    | Extracted overlay text                      |
| created_at     | Timestamp | Video post time (not scrape time)         |

---

## 📌 Notes

- Frame extraction and GPT-4o logic are optimized for better overlay text recognition.
- Make sure your `usernames.txt` and `hooks.json` are up to date for accurate validation.

---

## 🤖 Credits

Built using:
- [Apify TikTok Scraper](https://apify.com/clockworks/free-tiktok-scraper)
- [OpenAI GPT-4o](https://platform.openai.com/docs/)
- [Supabase](https://supabase.com/)
- [MoviePy](https://zulko.github.io/moviepy/)
- [YT-DLP](https://github.com/yt-dlp/yt-dlp)

---

## 📬 Contact

Made with ❤️ for Faircado.  
Questions or issues? Ping @fati
