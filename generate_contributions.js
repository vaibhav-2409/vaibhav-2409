#!/usr/bin/env node
/**
 * Generates realistic-looking GitHub contribution history via backdated git commits.
 * Creates a pattern that looks like a real final-year CS student.
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const REPO_DIR = __dirname;
const START_DATE = new Date(2025, 6, 1); // July 1, 2025 (months are 0-indexed in JS)
const END_DATE = new Date(2026, 6, 20);  // July 20, 2026

// Seasonal activity weights
const MONTH_WEIGHTS = {
    0: 0.30, 1: 0.50, 2: 0.65, 3: 0.70, 4: 0.35, 5: 0.25,
    6: 0.55, 7: 0.60, 8: 0.70, 9: 0.75, 10: 0.65, 11: 0.30
};

// Day-of-week weights (0=Sunday, 1=Monday... JS getDay)
const DAY_WEIGHTS = {
    1: 0.80, 2: 0.85, 3: 0.80, 4: 0.75, 5: 0.65, 6: 0.35, 0: 0.20
};

const BURST_PERIODS = [
    [new Date(2025, 9, 10), new Date(2025, 9, 18)],
    [new Date(2025, 10, 20), new Date(2025, 10, 30)],
    [new Date(2026, 1, 5), new Date(2026, 1, 15)],
    [new Date(2026, 2, 15), new Date(2026, 2, 25)],
    [new Date(2026, 3, 10), new Date(2026, 3, 20)],
    [new Date(2026, 6, 1), new Date(2026, 6, 15)]
];

const DEAD_PERIODS = [
    [new Date(2025, 11, 1), new Date(2025, 11, 20)],
    [new Date(2025, 11, 24), new Date(2026, 0, 3)],
    [new Date(2026, 0, 5), new Date(2026, 0, 20)],
    [new Date(2026, 4, 1), new Date(2026, 4, 20)],
    [new Date(2026, 5, 5), new Date(2026, 5, 18)]
];

const COMMIT_MESSAGES = [
    "refactor: clean up utility functions", "feat: add input validation",
    "fix: resolve edge case in parser", "docs: update API documentation",
    "style: improve code formatting", "test: add unit tests for auth module",
    "chore: update dependencies", "feat: implement caching layer",
    "fix: handle null pointer exception", "refactor: extract helper methods",
    "feat: add error handling middleware", "docs: add inline comments",
    "fix: correct off-by-one error", "feat: implement pagination",
    "chore: clean up unused imports", "test: add integration tests",
    "feat: add logging infrastructure", "fix: resolve race condition",
    "refactor: optimize database queries", "feat: implement rate limiting",
    "docs: update README with examples", "fix: handle timeout errors gracefully",
    "feat: add configuration validation", "style: standardize naming conventions",
    "test: improve test coverage", "feat: add health check endpoint"
];

const FILE_CONTENTS = [
    "// Updated: {date}\n// Module improvements\nconst VERSION = '{version}';\n",
    "# Config updated {date}\nDEBUG={debug}\nLOG_LEVEL=info\n",
    "/* Style update {date} */\n.container {{ margin: {margin}px; }}\n",
    "# Notes - {date}\n- Refactored module\n- Fixed {bugs} bugs\n",
    "// Test suite - {date}\ndescribe('module', () => {{ /* tests */ }});\n"
];

function isInPeriod(date, periods) {
    return periods.some(([start, end]) => date >= start && date <= end);
}

function randomChoice(arr) {
    return arr[Math.floor(Math.random() * arr.length)];
}

function randomInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

function getCommitCount(date) {
    if (isInPeriod(date, DEAD_PERIODS)) return 0;

    let monthWeight = MONTH_WEIGHTS[date.getMonth()];
    let dayWeight = DAY_WEIGHTS[date.getDay()];

    if (isInPeriod(date, BURST_PERIODS)) {
        monthWeight = Math.min(monthWeight * 1.8, 1.0);
        dayWeight = Math.min(dayWeight * 1.5, 1.0);
    }

    let probability = monthWeight * dayWeight;
    probability *= (Math.random() * (1.4 - 0.6) + 0.6);

    if (Math.random() > probability) return 0;

    if (isInPeriod(date, BURST_PERIODS)) {
        // Higher intensity 1-7
        const weights = [15, 25, 25, 15, 10, 5, 5];
        return weightedRandom([1, 2, 3, 4, 5, 6, 7], weights);
    } else {
        // Normal 1-4
        const weights = [45, 30, 15, 10];
        return weightedRandom([1, 2, 3, 4], weights);
    }
}

function weightedRandom(items, weights) {
    let i;
    let sum = weights.reduce((a, b) => a + b, 0);
    let rand = Math.random() * sum;
    for (i = 0; i < items.length; i++) {
        rand -= weights[i];
        if (rand < 0) return items[i];
    }
    return items[0];
}

function createCommit(date, index) {
    const hours = [
        ...Array(6).fill(5).map((w, i) => [i, w]),
        ...Array(3).fill(5).map((w, i) => [i+6, w]),
        ...Array(3).fill(15).map((w, i) => [i+9, w]),
        ...Array(2).fill(10).map((w, i) => [i+12, w]),
        ...Array(4).fill(25).map((w, i) => [i+14, w]),
        ...Array(4).fill(30).map((w, i) => [i+18, w]),
        ...Array(2).fill(10).map((w, i) => [i+22, w])
    ];
    
    const hList = hours.map(h => h[0]);
    const wList = hours.map(h => h[1]);
    
    let hour = weightedRandom(hList, wList);
    let minute = randomInt(0, 59);
    let second = randomInt(0, 59);

    let d = new Date(date);
    d.setHours(hour, minute, second);
    
    let pad = (n) => String(n).padStart(2, '0');
    let dateStr = `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;

    let message = randomChoice(COMMIT_MESSAGES);
    
    let contentTpl = randomChoice(FILE_CONTENTS);
    let dateFmt = `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`;
    
    let content = contentTpl
        .replace('{date}', dateFmt)
        .replace('{version}', `${randomInt(1,9)}.${randomInt(0,9)}.${randomInt(0,99)}`)
        .replace('{debug}', randomChoice(['true', 'false']))
        .replace('{margin}', randomInt(4, 32))
        .replace('{bugs}', randomInt(1, 12))
        .replace('{{', '{').replace('}}', '}');

    const filenames = [
        "src/utils.js", "src/config.js", "src/helpers.js",
        "src/constants.js", "src/index.js", "tests/test.js",
        "docs/notes.md", "styles/main.css", "lib/core.js",
        "src/api.js"
    ];
    let filename = filenames[index % filenames.length];
    
    let filepath = path.join(REPO_DIR, filename);
    fs.mkdirSync(path.dirname(filepath), { recursive: true });
    fs.writeFileSync(filepath, content);
    
    let env = Object.assign({}, process.env, {
        GIT_AUTHOR_DATE: dateStr,
        GIT_COMMITTER_DATE: dateStr
    });
    
    try {
        execSync('git add .', { cwd: REPO_DIR, env });
        execSync(`git commit -m "${message}" --allow-empty-message`, { cwd: REPO_DIR, env, stdio: 'ignore' });
    } catch (e) {
        // ignore
    }
}

function main() {
    console.log("🎨 Generating realistic contribution history...");
    
    let totalCommits = 0;
    let totalActiveDays = 0;
    let current = new Date(START_DATE);
    
    // Setup git locally if needed, assuming already git init'd
    
    while (current <= END_DATE) {
        let count = getCommitCount(current);
        if (count > 0) {
            totalActiveDays++;
            for (let i = 0; i < count; i++) {
                createCommit(current, totalCommits + i);
            }
            totalCommits += count;
            
            if (totalActiveDays % 20 === 0) {
                console.log(`   📅 ${current.toISOString().split('T')[0]} | ${totalCommits} commits so far...`);
            }
        }
        current.setDate(current.getDate() + 1);
    }
    
    console.log(`\n✅ Done! Generated ${totalCommits} commits across ${totalActiveDays} active days`);
}

main();
