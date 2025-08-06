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

┣ 📄 daily_validator.py # Main script for daily video scraping & validation
┣ 📄 scheduler.py # (Optional) Local scheduler script using schedule library
┣ 📄 hooks.json # Contains predefined hook examples for validation
┣ 📄 usernames.txt # List of TikTok usernames to scrape
┗ 📄 .env # Your environment variables
