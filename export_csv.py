import json
import csv

with open("leaderboard_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

students = data["students"]

fieldnames = [
    "Rank",
    "Full Name",
    "Assigned Mentor",
    "Email Address",
    "Phone Number",
    "Status",
    "Badge Count",
    "Google Skills Profile Name",
    "Google Skills Public Profile URL",
    "Badges Earned List"
]

with open("leaderboard_summary.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for s in students:
        badge_titles = "; ".join([b["title"] for b in s.get("badges", [])])
        writer.writerow({
            "Rank": s.get("rank", "-"),
            "Full Name": s.get("name", ""),
            "Assigned Mentor": s.get("mentor", "Unassigned"),
            "Email Address": s.get("email", ""),
            "Phone Number": s.get("phone", ""),
            "Status": s.get("status", ""),
            "Badge Count": s.get("badge_count", 0),
            "Google Skills Profile Name": s.get("profile_name", ""),
            "Google Skills Public Profile URL": s.get("url", ""),
            "Badges Earned List": badge_titles
        })

print("Successfully exported leaderboard_summary.csv with Mentor assignments!")
