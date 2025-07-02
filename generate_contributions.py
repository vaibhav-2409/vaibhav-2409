#!/usr/bin/env python3
"""
Generates realistic-looking GitHub contribution history via backdated git commits.
Creates a pattern that looks like a real final-year CS student:
- More active on weekdays, lighter on weekends
- Occasional bursts (hackathons, project deadlines)  
- Some completely empty weeks (exams, vacations)
- Varying intensity throughout the year
"""

import os
import random
import subprocess
from datetime import datetime, timedelta

# ─── Configuration ───────────────────────────────────────────────────
REPO_DIR = os.path.dirname(os.path.abspath(__file__))
START_DATE = datetime(2025, 7, 1)   # ~1 year of history
END_DATE = datetime(2026, 7, 20)    # Up to yesterday

# Seasonal activity weights (month -> base probability of committing)
# Simulates exam periods, vacations, project crunch times
MONTH_WEIGHTS = {
    1: 0.30,   # Jan: Exam season, low activity
    2: 0.50,   # Feb: Post-exams, moderate
    3: 0.65,   # Mar: Project season picking up
    4: 0.70,   # Apr: Active development
    5: 0.35,   # May: End-sem exams
    6: 0.25,   # Jun: Summer break start (low)
    7: 0.55,   # Jul: Summer projects / internship
    8: 0.60,   # Aug: Back to work
    9: 0.70,   # Sep: Semester projects active
    10: 0.75,  # Oct: Hackathon season, very active
    11: 0.65,  # Nov: Project submissions
    12: 0.30,  # Dec: End-sem exams + holiday
}

# Day-of-week weights (0=Monday, 6=Sunday)
DAY_WEIGHTS = {
    0: 0.80,   # Monday
    1: 0.85,   # Tuesday (most productive)
    2: 0.80,   # Wednesday
    3: 0.75,   # Thursday
    4: 0.65,   # Friday (winding down)
    5: 0.35,   # Saturday (occasional)
    6: 0.20,   # Sunday (rare)
}

# Define "burst weeks" — simulate hackathons/deadlines with higher activity
BURST_PERIODS = [
    (datetime(2025, 10, 10), datetime(2025, 10, 18)),   # Hackathon
    (datetime(2025, 11, 20), datetime(2025, 11, 30)),   # Project deadline
    (datetime(2026, 2, 5), datetime(2026, 2, 15)),      # New project kickoff
    (datetime(2026, 3, 15), datetime(2026, 3, 25)),     # Major feature push
    (datetime(2026, 4, 10), datetime(2026, 4, 20)),     # Alerion AI sprint
    (datetime(2026, 7, 1), datetime(2026, 7, 15)),      # Recent active period
]

# Define "dead zones" — exam weeks, vacations with zero commits
DEAD_PERIODS = [
    (datetime(2025, 12, 1), datetime(2025, 12, 20)),    # End-sem exams
    (datetime(2025, 12, 24), datetime(2026, 1, 3)),     # Holiday break
    (datetime(2026, 1, 5), datetime(2026, 1, 20)),      # Exam prep
    (datetime(2026, 5, 1), datetime(2026, 5, 20)),      # End-sem exams
    (datetime(2026, 6, 5), datetime(2026, 6, 18)),      # Break
]

# Commit message templates for realism
COMMIT_MESSAGES = [
    "refactor: clean up utility functions",
    "feat: add input validation",
    "fix: resolve edge case in parser",
    "docs: update API documentation",
    "style: improve code formatting",
    "test: add unit tests for auth module",
    "chore: update dependencies",
    "feat: implement caching layer",
    "fix: handle null pointer exception",
    "refactor: extract helper methods",
    "feat: add error handling middleware",
    "docs: add inline comments",
    "fix: correct off-by-one error",
    "feat: implement pagination",
    "chore: clean up unused imports",
    "test: add integration tests",
    "feat: add logging infrastructure",
    "fix: resolve race condition",
    "refactor: optimize database queries",
    "feat: implement rate limiting",
    "docs: update README with examples",
    "fix: handle timeout errors gracefully",
    "feat: add configuration validation",
    "style: standardize naming conventions",
    "test: improve test coverage",
    "feat: add health check endpoint",
    "fix: memory leak in event handler",
    "refactor: simplify control flow",
    "chore: configure CI pipeline",
    "feat: implement WebSocket handler",
    "fix: correct data serialization",
    "docs: add architecture diagram",
    "feat: add search functionality",
    "test: add edge case tests",
    "refactor: modularize components",
    "feat: implement data export",
    "fix: resolve CORS issues",
    "chore: update build configuration",
    "feat: add user preferences",
    "fix: handle concurrent requests",
]

# Dummy file content templates
FILE_CONTENTS = [
    "// Updated: {date}\n// Module improvements\nconst VERSION = '{version}';\n",
    "# Config updated {date}\nDEBUG={debug}\nLOG_LEVEL=info\n",
    "/* Style update {date} */\n.container {{ margin: {margin}px; }}\n",
    "# Notes - {date}\n- Refactored module\n- Fixed {bugs} bugs\n",
    "// Test suite - {date}\ndescribe('module', () => {{ /* tests */ }});\n",
]


def is_in_period(date, periods):
    """Check if date falls within any of the given periods."""
    for start, end in periods:
        if start <= date <= end:
            return True
    return False


def get_commit_count(date):
    """Determine how many commits to make on a given date."""
    # Dead periods = 0 commits
    if is_in_period(date, DEAD_PERIODS):
        return 0

    month_weight = MONTH_WEIGHTS.get(date.month, 0.5)
    day_weight = DAY_WEIGHTS.get(date.weekday(), 0.5)

    # Burst periods boost activity
    if is_in_period(date, BURST_PERIODS):
        month_weight = min(month_weight * 1.8, 1.0)
        day_weight = min(day_weight * 1.5, 1.0)

    # Combined probability
    probability = month_weight * day_weight

    # Add some randomness
    probability *= random.uniform(0.6, 1.4)

    # Roll the dice
    if random.random() > probability:
        return 0

    # Determine commit count based on intensity
    if is_in_period(date, BURST_PERIODS):
        # Burst: 1-7 commits
        weights = [15, 25, 25, 15, 10, 5, 5]
        return random.choices(range(1, 8), weights=weights)[0]
    else:
        # Normal: 1-4 commits, heavily weighted toward 1-2
        weights = [45, 30, 15, 10]
        return random.choices(range(1, 5), weights=weights)[0]


def create_commit(date, index):
    """Create a single backdated commit."""
    # Random time during the day (weighted toward evening for a student)
    hour_weights = {
        range(0, 6): 5,     # Late night
        range(6, 9): 5,     # Early morning (rare)
        range(9, 12): 15,   # Morning
        range(12, 14): 10,  # Lunch
        range(14, 18): 25,  # Afternoon
        range(18, 22): 30,  # Evening (peak)
        range(22, 24): 10,  # Night
    }

    # Pick hour with weights
    hours = []
    weights = []
    for hr_range, weight in hour_weights.items():
        for h in hr_range:
            hours.append(h)
            weights.append(weight)

    hour = random.choices(hours, weights=weights)[0]
    minute = random.randint(0, 59)
    second = random.randint(0, 59)

    commit_date = date.replace(hour=hour, minute=minute, second=second)
    date_str = commit_date.strftime("%Y-%m-%dT%H:%M:%S")

    # Pick a random commit message
    message = random.choice(COMMIT_MESSAGES)

    # Modify a file to create a real diff
    content_template = random.choice(FILE_CONTENTS)
    content = content_template.format(
        date=date.strftime("%Y-%m-%d"),
        version=f"{random.randint(1,9)}.{random.randint(0,9)}.{random.randint(0,99)}",
        debug=random.choice(["true", "false"]),
        margin=random.randint(4, 32),
        bugs=random.randint(1, 12),
    )

    # Use rotating file names so diffs are varied
    filenames = [
        "src/utils.js", "src/config.js", "src/helpers.js",
        "src/constants.js", "src/index.js", "tests/test.js",
        "docs/notes.md", "styles/main.css", "lib/core.js",
        "src/api.js",
    ]
    filename = filenames[index % len(filenames)]

    filepath = os.path.join(REPO_DIR, filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, "w") as f:
        f.write(content)

    env = os.environ.copy()
    env["GIT_AUTHOR_DATE"] = date_str
    env["GIT_COMMITTER_DATE"] = date_str

    subprocess.run(["git", "add", "."], cwd=REPO_DIR, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", message, "--allow-empty-message"],
        cwd=REPO_DIR,
        env=env,
        capture_output=True,
    )


def main():
    print("🎨 Generating realistic contribution history...")
    print(f"   Period: {START_DATE.strftime('%Y-%m-%d')} → {END_DATE.strftime('%Y-%m-%d')}")
    print()

    total_commits = 0
    total_active_days = 0
    current = START_DATE

    while current <= END_DATE:
        count = get_commit_count(current)

        if count > 0:
            total_active_days += 1
            for i in range(count):
                create_commit(current, total_commits + i)
            total_commits += count

            # Progress indicator
            if total_active_days % 20 == 0:
                print(f"   📅 {current.strftime('%Y-%m-%d')} | {total_commits} commits so far...")

        current += timedelta(days=1)

    total_days = (END_DATE - START_DATE).days
    print()
    print(f"✅ Done! Generated {total_commits} commits across {total_active_days} active days")
    print(f"   📊 {total_days} total days | {total_active_days} active | {total_days - total_active_days} inactive")
    print(f"   📈 Average: {total_commits / max(total_active_days, 1):.1f} commits per active day")
    print()
    print("🚀 Now push with: git push -u origin main")


if __name__ == "__main__":
    random.seed(2409)  # Fixed seed for reproducibility
    main()
