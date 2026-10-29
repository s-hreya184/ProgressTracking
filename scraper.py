import csv
import json
import os
import re
import socket
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

# Optimization for Windows DNS resolution
_orig_getaddrinfo = socket.getaddrinfo


def _custom_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    if "skills.google" in host:
        return _orig_getaddrinfo("35.201.118.42", port, family, type, proto, flags)
    return _orig_getaddrinfo(host, port, family, type, proto, flags)


socket.getaddrinfo = _custom_getaddrinfo

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def clean_url(raw_url: str) -> str:
    if not raw_url:
        return ""
    url = raw_url.strip()
    if not url.startswith("http"):
        return ""
    parsed = urlparse(url)
    cleaned = urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))
    return cleaned.rstrip("/")


def parse_profile(html_content: str):
    soup = BeautifulSoup(html_content, "html.parser")

    # Name
    h1 = soup.find("h1")
    profile_name = h1.get_text(strip=True) if h1 else ""

    # Avatar
    avatar_elem = soup.select_one(".public-profile-header__avatar img, .ql-avatar img, img[alt*='Avatar']")
    avatar_url = avatar_elem["src"] if avatar_elem and avatar_elem.get("src") else ""

    # Badges
    badges = []
    badge_cards = soup.select(".profile-badge")
    for card in badge_cards:
        title_elem = card.select_one(".ql-title-medium, h3, .badge-title")
        title = title_elem.get_text(strip=True) if title_elem else ""

        date_elem = card.select_one(".ql-body-medium, .badge-date")
        date_text = date_elem.get_text(strip=True) if date_elem else ""
        date_text = re.sub(r"^Earned\s+", "", date_text).strip()

        img_elem = card.find("img")
        img_url = img_elem["src"] if img_elem and img_elem.get("src") else ""

        a_elem = card.find("a", href=True)
        link = a_elem["href"] if a_elem else ""

        if title:
            badges.append({
                "title": title,
                "date": date_text,
                "image": img_url,
                "link": link,
            })

    text_lower = soup.get_text().lower()
    is_private = "profile is private" in text_lower or "page not found" in text_lower

    return {
        "profile_name": profile_name,
        "avatar_url": avatar_url,
        "badges": badges,
        "badge_count": len(badges),
        "is_private": is_private,
    }


def fetch_student(student: dict, session: requests.Session, cache: dict = None):
    reg_name = student.get("Full Name", "").strip()
    email = student.get("Email Address", "").strip()
    phone = student.get("Phone Number", "").strip()
    raw_url = student.get("Google Skills Public Profile URL", "").strip()
    mentor = (
        student.get("Assigned Mentor")
        or student.get("Mentor")
        or student.get("Team Member")
        or student.get("Facilitator")
        or "Unassigned"
    ).strip()

    cleaned_url = clean_url(raw_url)

    record = {
        "name": reg_name,
        "email": email,
        "phone": phone,
        "mentor": mentor,
        "url": cleaned_url,
        "profile_name": "",
        "avatar_url": "",
        "badge_count": 0,
        "badges": [],
        "status": "pending",
        "error": None,
    }

    if not cleaned_url:
        record["status"] = "missing_url"
        return record

    if cache and email in cache and cache[email].get("url") == cleaned_url:
        cached = cache[email]
        record["profile_name"] = cached.get("profile_name", "")
        record["avatar_url"] = cached.get("avatar_url", "")
        record["badge_count"] = cached.get("badge_count", 0)
        record["badges"] = cached.get("badges", [])
        record["status"] = cached.get("status", "active")
        record["error"] = cached.get("error")
        return record

    max_retries = 2
    for attempt in range(max_retries):
        try:
            resp = session.get(cleaned_url, headers=HEADERS, timeout=12)
            if resp.status_code == 200:
                parsed = parse_profile(resp.text)
                if parsed["is_private"]:
                    record["status"] = "private"
                else:
                    record["status"] = "active"
                    record["profile_name"] = parsed["profile_name"]
                    record["avatar_url"] = parsed["avatar_url"]
                    record["badges"] = parsed["badges"]
                    record["badge_count"] = parsed["badge_count"]
                return record
            elif resp.status_code == 404:
                record["status"] = "not_found"
                return record
            else:
                record["error"] = f"HTTP {resp.status_code}"
        except Exception as e:
            if attempt == max_retries - 1:
                record["status"] = "error"
                record["error"] = str(e)
            time.sleep(1)

    return record


def run_scraper(input_csv="students.csv", output_json="leaderboard_data.json", use_cache=False):
    sheet_url = os.environ.get("GOOGLE_SHEET_CSV_URL")
    if sheet_url:
        print(f"Fetching latest student list from Google Sheets: {sheet_url}")
        try:
            r = requests.get(sheet_url, timeout=10)
            if r.status_code == 200:
                with open(input_csv, "w", encoding="utf-8") as f:
                    f.write(r.text)
                print("Updated students.csv from Google Sheets!")
        except Exception as e:
            print(f"Warning: Could not fetch from Google Sheets: {e}")

    print(f"Reading students from {input_csv}...")
    with open(input_csv, mode="r", encoding="utf-8") as f:
        students = list(csv.DictReader(f))

    print(f"Loaded {len(students)} student records.")

    cache = {}
    if use_cache and os.path.exists(output_json):
        try:
            with open(output_json, "r", encoding="utf-8") as f:
                old_data = json.load(f)
                for s in old_data.get("students", []):
                    if s.get("email"):
                        cache[s["email"]] = s
            print(f"Loaded cache with {len(cache)} students.")
        except Exception as e:
            print(f"Cache load skipped: {e}")

    start_time = time.time()
    results = []

    def worker(student_data):
        session = requests.Session()
        return fetch_student(student_data, session, cache=cache)

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(worker, s): s for s in students}
        completed = 0
        for future in as_completed(futures):
            res = future.result()
            results.append(res)
            completed += 1
            if completed % 20 == 0 or completed == len(students):
                print(f"Progress: {completed}/{len(students)} profiles processed...")

    results.sort(key=lambda x: (-x["badge_count"], x["name"].lower()))

    current_rank = 1
    for i, r in enumerate(results):
        if r["status"] == "active" and r["badge_count"] > 0:
            if i > 0 and results[i - 1]["badge_count"] == r["badge_count"]:
                r["rank"] = results[i - 1]["rank"]
            else:
                r["rank"] = current_rank
            current_rank += 1
        else:
            r["rank"] = "-"

    elapsed = time.time() - start_time
    print(f"Scraping completed in {elapsed:.2f} seconds.")

    active_count = sum(1 for r in results if r["status"] == "active")
    missing_count = sum(1 for r in results if r["status"] == "missing_url")
    error_count = sum(1 for r in results if r["status"] in ("error", "not_found", "private"))
    total_badges = sum(r["badge_count"] for r in results)

    all_badges_map = {}
    for r in results:
        for b in r["badges"]:
            b_title = b["title"]
            if b_title not in all_badges_map:
                all_badges_map[b_title] = {
                    "title": b_title,
                    "image": b["image"],
                    "count": 0,
                }
            all_badges_map[b_title]["count"] += 1

    unique_cohort_badges = sorted(all_badges_map.values(), key=lambda x: -x["count"])

    mentor_map = {}
    for r in results:
        m = r.get("mentor", "Unassigned") or "Unassigned"
        if m not in mentor_map:
            mentor_map[m] = {
                "name": m,
                "total_mentees": 0,
                "total_badges": 0,
                "completed_milestone": 0,
                "in_progress": 0,
                "not_started": 0,
                "missing_url": 0,
            }
        mentor_map[m]["total_mentees"] += 1
        mentor_map[m]["total_badges"] += r["badge_count"]
        if r["status"] == "missing_url":
            mentor_map[m]["missing_url"] += 1
        elif r["badge_count"] >= 10:
            mentor_map[m]["completed_milestone"] += 1
        elif r["badge_count"] > 0:
            mentor_map[m]["in_progress"] += 1
        else:
            mentor_map[m]["not_started"] += 1

    for m in mentor_map.values():
        if m["total_mentees"] > 0:
            m["completion_rate"] = round((m["completed_milestone"] / m["total_mentees"]) * 100, 1)
        else:
            m["completion_rate"] = 0

    mentor_stats = sorted(mentor_map.values(), key=lambda x: (-x["total_badges"], x["name"]))

    payload = {
        "metadata": {
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "total_participants": len(results),
            "active_profiles": active_count,
            "missing_urls": missing_count,
            "issues": error_count,
            "total_badges_earned": total_badges,
            "elapsed_seconds": round(elapsed, 1),
        },
        "mentors": mentor_stats,
        "cohort_badges": unique_cohort_badges,
        "students": results,
    }

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"Results saved to {output_json}!")
    print(f"Summary: {active_count} active profiles, {total_badges} total badges earned.")

    try:
        import subprocess
        print("Regenerating interactive web dashboard (index.html)...")
        subprocess.run([sys.executable, "build_dashboard.py"], check=True)
        print("Exporting updated leaderboard_summary.csv...")
        subprocess.run([sys.executable, "export_csv.py"], check=True)
        print("All assets successfully updated!")
    except Exception as e:
        print(f"Notice: Could not auto-run build scripts: {e}")


if __name__ == "__main__":
    use_cache_flag = "--cached" in sys.argv
    run_scraper(use_cache=use_cache_flag)
