# ☁️ Google Cloud Cohort — Progress Leaderboard

An interactive, real-time leaderboard dashboard for tracking students' Google Cloud Skills Boost badges, quests, and curriculum milestones. Built with real participant data from Cummins College.

---

## 🚀 Quick Start (View Right Now)

You can open the interactive dashboard immediately in your browser:
- **Double click** [`index.html`](file:///c:/Users/Shreya/Documents/ProgressTracking/index.html) to open it in Chrome, Edge, or Brave.
- Or run a local preview server:
  ```powershell
  python -m http.server 3000
  ```
  Then visit `http://localhost:3000`.

---

## 📊 Live Cohort Snapshot

- **Total Participants**: 109
- **Active Profile Links Verified**: 97
- **Total Badges Completed**: 111
- **Participants with Completed Milestones (10/10)**: 5
- **Students with at least 1 badge**: 20

### 🏆 Current Top Leaders (10/10 Milestone Achievers)
1. **Rucha Walvekar** (10 badges — completed Oct 26)
2. **Tanisha Prabhakar Paunikar** (10 badges — completed Oct 27)
3. **Mrunal Deore** (10 badges — completed Oct 29)
4. **Ria Bogawat** (10 badges — completed Oct 29)
5. **Aashita Rai** (10 badges — completed Oct 29)
*Followed closely by **Siddhi Milind Indapurkar** (9 badges) and **Tina Pawar** (9 badges).*

---

## 🛠️ How to Refresh or Add Students

1. **Add / Edit Student Data**:
   Update [`students.csv`](file:///c:/Users/Shreya/Documents/ProgressTracking/students.csv) with any new names or updated public profile URLs.

2. **Run Scraper**:
   Execute the fast multithreaded scraper:
   ```powershell
   python scraper.py
   ```
   *In ~15 seconds, the scraper will:*
   - Fetch badges and dates for all 109 profiles.
   - Re-rank students and detect completed milestone quests.
   - Update `leaderboard_data.json`.
   - Rebuild `index.html`.
   - Update `leaderboard_summary.csv`.

---

## 🌐 Free Automated Hosting (GitHub Pages)

To make this dashboard accessible to all students and faculty via a public link:
1. Push this folder to a GitHub repository:
   ```bash
   git init
   git add .
   git commit -m "Initial commit of cohort leaderboard"
   git remote add origin https://github.com/<your-username>/<repo-name>.git
   git push -u origin main
   ```
2. In GitHub, go to **Settings > Pages > Build and deployment > Source**: select **GitHub Actions** (or deploy from `gh-pages` branch).
3. The included workflow `.github/workflows/update_leaderboard.yml` will automatically re-scrape every 4 hours and keep the leaderboard fresh with zero manual work!

---

## 📁 Project Structure

| File | Purpose |
| :--- | :--- |
| [`index.html`](file:///c:/Users/Shreya/Documents/ProgressTracking/index.html) | Interactive web dashboard (Tailwind CSS, search, filters, podium, badge modal, checklist) |
| [`students.csv`](file:///c:/Users/Shreya/Documents/ProgressTracking/students.csv) | Master cohort participant list with Skills Boost URLs |
| [`scraper.py`](file:///c:/Users/Shreya/Documents/ProgressTracking/scraper.py) | High-speed multi-threaded scraper (extracts badges, dates, avatars) |
| [`leaderboard_data.json`](file:///c:/Users/Shreya/Documents/ProgressTracking/leaderboard_data.json) | Structured JSON dataset containing full badge breakdown per student |
| [`leaderboard_summary.csv`](file:///c:/Users/Shreya/Documents/ProgressTracking/leaderboard_summary.csv) | Exported spreadsheet for Excel/Google Sheets reporting |
| [`build_dashboard.py`](file:///c:/Users/Shreya/Documents/ProgressTracking/build_dashboard.py) | Compiles the dashboard HTML with embedded data fallback |
| [`.github/workflows/`](file:///c:/Users/Shreya/Documents/ProgressTracking/.github/workflows/update_leaderboard.yml) | Scheduled GitHub Actions automation |
