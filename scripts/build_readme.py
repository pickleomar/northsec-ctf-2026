#!/usr/bin/env python3
"""
NSC // THE ARCHIVE — README generator for the NorthSec CTF 2026 challenge repo.

Scans the challenge folders, extracts metadata (author / difficulty / briefing /
writeup), and renders the root README.md from scripts/TEMPLATE.md.

Usage:
    python3 scripts/build_readme.py          # regenerate README.md
    python3 scripts/build_readme.py --check  # verify every dossier is classified
"""

import argparse
import html
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from urllib.parse import quote

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# REGISTRY — edit these if challenges are added / reclassified
# ---------------------------------------------------------------------------

CATEGORY_ORDER = ["CRYPTO", "PWN", "REVERSE", "WEB", "MISC", "DFIR", "WASM"]

CATEGORY_META = {
    "CRYPTO":  ("🔐", "cipher operations"),
    "PWN":     ("💥", "memory corruption & exploitation"),
    "REVERSE": ("🧬", "binary dissection"),
    "WEB":     ("🌐", "web exploitation"),
    "MISC":    ("🌀", "everything in between"),
    "DFIR":    ("🕵", "digital forensics & incident response"),
    "WASM":    ("⚙", "webassembly natives"),
}

QUALS = {
    "CRYPTO/KRASNYKANAL",
    "CRYPTO/ShinraTensei",
    "CRYPTO/Structures",
    "CRYPTO/The Enigmatic Vault",
    "DFIR/Last-Seen",
    "DFIR/Ransomware",
    "MISC/Coldtap",
    "MISC/Far-Side Window",
    "MISC/Gear 5",
    "MISC/Genesis",
    "MISC/R4VENOUS",
    "PWN/Archivist’s Ritual",
    "PWN/ksh",
    "PWN/necro-game",
    "REVERSE/casino_sfayga",
    "REVERSE/Handshake",
    "REVERSE/INSIDE-ME",
    "REVERSE/masjid__rahma",
    "REVERSE/masjid_rahma_revenge",
    "REVERSE/NOSTALGIA",
    "WEB/dar-mohssinin",
    "WEB/Escape-The-Matrix",
    "WEB/Ouazzane",
    "WEB/Shadow Sockets",
}

# Everything not listed in QUALS or FINALS below is flagged as UNCLASSIFIED.
FINALS = {
    "CRYPTO/GATOUZZ",
    "CRYPTO/TOTL",
    "CRYPTO/TRAVEL",
    "DFIR/Silent Interlock",
    "MISC/Cold Chain",
    "PWN/boom game",
    "PWN/cpp",
    "PWN/fsop",
    "REVERSE/ContextCollapse",
    "REVERSE/Safety Profile",
    "WASM/buzzk1ll",
    "WEB/EM",
    "WEB/enpcs",
    "WEB/Facbook-Tanjawi",
    "WEB/facebook",
    "WEB/ho9na",
    "WEB/s0ng0k0",
}

DISPLAY_NAMES = {
    "WEB/facebook": "mo7adata-revenge",  # inner challenge name
}

AUTHOR_OVERRIDES = {
    # "CATEGORY/folder": "Operative",
}

# Canonical casing for author handles discovered in mixed case (e.g. "fairalien").
AUTHOR_CANON = {
    "fairalien": "Fairalien",
    "zh3gh05t": "Zh3gh05t",
    "slamo": "slamo",
    "hoxon": "HoXoN",
    "blackmy7h": "BlackMy7h",
    "molzri3": "molzri3",
    "pickleomar": "pickleomar",
    "afk-yato": "afk-Yato",
    "scriptmagum": "Scriptmagum",
    "wiame5": "Wiame5",
    "bld933": "BLD933",
    "sdikiyousra": "SDIKIYOUSRA",
}

DIFFICULTY_OVERRIDES = {
    # "CATEGORY/folder": "easy" | "medium" | "med-hard" | "hard",
}

DESCRIPTION_OVERRIDES = {
    # Source READMEs sometimes contain organizer notes instead of a player brief.
    "MISC/Gear 5": "Some titles say more than they appear to. Look closer — character by character.",
}

DIFF_META = {
    "EASY":     ("🟢", "easy"),
    "MEDIUM":   ("🟡", "medium"),
    "MED-HARD": ("🟠", "med-hard"),
    "HARD":     ("🔴", "hard"),
}
DIFF_UNKNOWN = ("⚪", "n/a")

# ---------------------------------------------------------------------------
# EXTRACTION
# ---------------------------------------------------------------------------

WRITEUP_DIRS = {"writeup", "writeups", "solution"}
WRITEUP_NAMES = {"writeup.md", "solve.md", "solution.md", "sol.md"}

AUTHOR_RES = [
    re.compile(r"(?im)^\s*#{0,4}\s*[*_`\s]*author[*_`\s]*[:=]\s*(.+?)\s*$"),
    re.compile(r"(?i)[/|]{1,2}\s*[*_`\s]*author[*_`\s]*[:=]\s*([^\n|]{2,40}?)(?:\s*$|[/|])"),
]
DIFF_RE = re.compile(
    r"(?i)\b(?:difficulty|level)\b\s*\**\s*[:=]\s*\**\s*([a-z][a-z \-]{2,24})"
)
DESC_FIELD_RE = re.compile(r"(?i)^\s*#{0,4}\s*\**\s*description\**\s*[:=]\s*(.+?)\s*$")
META_PREFIX_RE = re.compile(
    r"(?i)^\s*#{0,4}\s*[*_`\s]*(?:chall[\s_]?name|author|flag|hint|hints|level|"
    r"difficulty|category|points|solves|files provided|challenge files|objective|"
    r"how to run|writeup|deployment|infra|flag format|description|scenario|link)"
    r"\b\**\s*[:=]"
)
SKIP_PREFIX = ("#", "-", "*", "|", ">", "!", "[", "`", "http", "www", "<", "!")
FLAG_RE = re.compile(r"(?i)\b(?:nsc|flag|ctf)\s*\{[^}]{0,150}\}")
TRAILING_AUTHOR_RE = re.compile(r"(?i)[/|,]?\s*author\s*:?\s*[\w\-]+\s*$")


def norm_diff(raw):
    r = raw.lower()
    if "medium" in r and "hard" in r:
        return "MED-HARD"
    if "hard" in r or "insane" in r:
        return "HARD"
    if "medium" in r or "med" in r:
        return "MEDIUM"
    if "easy" in r or "beginner" in r or "warmup" in r or "baby" in r:
        return "EASY"
    return None


def clean_author(raw):
    a = re.sub(r"[*_`>\[\]]", "", raw)
    a = re.sub(r"\s*\([^)]*\)", "", a)
    a = re.split(r"\s//|\||/\s", a)[0]
    a = a.strip(" .:-–—")
    if not (1 < len(a) <= 25):
        return None
    if "{" in a or "}" in a or "http" in a.lower():
        return None
    return a


def is_writeup_rel(rel):
    parts = [p.lower() for p in rel.split("/")]
    base = parts[-1]
    if base in WRITEUP_NAMES:
        return True
    if any(p in WRITEUP_DIRS for p in parts[:-1]):
        return True
    return "writeup" in base


def doc_files(chall_dir):
    """All .md / description .txt files as '/'-separated relative paths."""
    out = []
    for root, _dirs, files in os.walk(chall_dir):
        for f in files:
            low = f.lower()
            if low.endswith(".md") or low == "description.txt":
                rel = os.path.relpath(os.path.join(root, f), chall_dir)
                out.append(rel.replace(os.sep, "/"))
    return sorted(out)


def file_priority(rel):
    """Lower tuple = scanned earlier. Description files first, writeups last."""
    r = rel.lower()
    base = r.rsplit("/", 1)[-1]
    return (
        1 if is_writeup_rel(rel) else 0,
        rel.count("/"),
        0 if base.startswith(("readme", "description")) else 1,
        r,
    )


def read_lines(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read().splitlines()
    except OSError:
        return []


def extract_author(chall_dir, files):
    for rel in sorted(files, key=file_priority):
        lines = read_lines(os.path.join(chall_dir, rel.replace("/", os.sep)))
        for line in lines:
            for rx in AUTHOR_RES:
                m = rx.search(line)
                if m:
                    a = clean_author(m.group(1))
                    if a:
                        return a
    return None


def extract_difficulty(chall_dir, files):
    for rel in sorted(files, key=file_priority):
        if is_writeup_rel(rel):
            continue
        for line in read_lines(os.path.join(chall_dir, rel.replace("/", os.sep))):
            for m in DIFF_RE.finditer(line):
                d = norm_diff(m.group(1))
                if d:
                    return d
    return None


def extract_description(chall_dir, files, display_name):
    cands = [r for r in sorted(files, key=file_priority) if not is_writeup_rel(r)]
    for rel in cands:
        lines = read_lines(os.path.join(chall_dir, rel.replace("/", os.sep)))

        # 1) explicit "description: ..." field
        for line in lines:
            m = DESC_FIELD_RE.match(line)
            if m:
                text = clean_desc(m.group(1), display_name)
                if text:
                    return text

        # 2) first clean paragraph of prose
        text = first_paragraph(lines, display_name)
        if text:
            return text
    return None


def clean_desc(text, display_name):
    text = TRAILING_AUTHOR_RE.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = text.strip("`*_- ")
    if not text or len(text) < 4:
        return None
    if display_name and text.lower().rstrip(".!") == display_name.lower():
        return None
    text = FLAG_RE.sub("NSC{[REDACTED]}", text)
    return text


def first_paragraph(lines, display_name):
    collected, in_fence = [], False
    for raw in lines:
        line = raw.rstrip()
        ls = line.strip()
        if ls.startswith("```"):
            if collected:
                break
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not ls:
            if len(" ".join(collected)) >= 120:
                break
            continue
        if ls.startswith(SKIP_PREFIX) or re.match(r"^\d+[.)]", ls):
            if collected:
                break
            continue
        if META_PREFIX_RE.match(ls) or ls.endswith(":"):
            if collected:
                break
            continue
        if len(ls) <= 3:
            continue
        if display_name and ls.lower() == display_name.lower():
            continue
        collected.append(ls)
        if len(" ".join(collected)) >= 320:
            break
    text = " ".join(collected)
    if len(text) > 240:
        text = text[:240].rsplit(" ", 1)[0].rstrip(",;:") + "…"
    return clean_desc(text, display_name) if text else None


def find_writeup(chall_dir):
    """Walk every file (any extension); return the best writeup candidate."""
    cands = []
    for root, _dirs, files in os.walk(chall_dir):
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), chall_dir).replace(os.sep, "/")
            if is_writeup_rel(rel):
                cands.append(rel)
    if not cands:
        return None
    def wsort(r):
        dirname = r.rsplit("/", 1)[0].lower() if "/" in r else ""
        return (
            0 if r.lower().endswith(".md") else 1,
            0 if dirname in WRITEUP_DIRS else 1,
            r.count("/"),
            r,
        )
    cands.sort(key=wsort)
    return cands[0]


# ---------------------------------------------------------------------------
# DISCOVERY
# ---------------------------------------------------------------------------


def discover():
    records = []
    for cat in CATEGORY_ORDER:
        cat_dir = os.path.join(BASE, cat)
        if not os.path.isdir(cat_dir):
            continue
        for folder in sorted(os.listdir(cat_dir), key=str.casefold):
            chall_dir = os.path.join(cat_dir, folder)
            if not os.path.isdir(chall_dir):
                continue
            key = f"{cat}/{folder}"
            files = doc_files(chall_dir)
            display = DISPLAY_NAMES.get(key, folder)
            if key in QUALS:
                round_name = "QUALS"
            elif key in FINALS:
                round_name = "FINALS"
            else:
                round_name = None
            author = AUTHOR_OVERRIDES.get(key) or extract_author(chall_dir, files)
            if author:
                author = AUTHOR_CANON.get(author.casefold(), author)
            if key in DESCRIPTION_OVERRIDES:
                desc = DESCRIPTION_OVERRIDES[key]
            else:
                desc = extract_description(chall_dir, files, display)
            records.append({
                "key": key,
                "cat": cat,
                "folder": folder,
                "display": display,
                "round": round_name,
                "author": author,
                "diff": DIFFICULTY_OVERRIDES.get(key) or extract_difficulty(chall_dir, files),
                "desc": desc,
                "writeup": find_writeup(chall_dir),
                "link": "./" + quote(f"{cat}/{folder}", safe="/-._~"),
            })
    return records


# ---------------------------------------------------------------------------
# RENDERING
# ---------------------------------------------------------------------------

BANNER_LETTERS = {
    "N": ["███╗   ██╗", "████╗  ██║", "██╔██╗ ██║", "██║╚██╗██║", "██║ ╚████║", "╚═╝  ╚═══╝"],
    "O": ["███████╗ ", "██╔════╝ ", "███████╗ ", "██╔════╝ ", "███████╗ ", "╚══════╝ "],
    "R": ["██████╗ ", "██╔══██╗", "██████╔╝", "██╔══██╗", "██║  ██║", "╚═╝  ╚═╝"],
    "T": ["████████╗", "╚══██╔══╝", "   ██║   ", "   ██║   ", "   ██║   ", "   ╚═╝   "],
    "H": ["██╗  ██╗", "██║  ██║", "███████║", "██╔══██║", "██║  ██║", "╚═╝  ╚═╝"],
    "S": ["███████╗", "██╔════╝", "███████╗", "╚════██║", "███████║", "╚══════╝"],
    "E": ["███████╗", "██╔════╝", "█████╗  ", "██╔══╝  ", "███████╗", "╚══════╝"],
    "C": [" ██████╗", "██╔════╝", "██║     ", "██║     ", "╚██████╗", " ╚═════╝"],
}


def render_banner():
    letters = [BANNER_LETTERS[ch] for ch in "NORTHSEC"]
    rows = ["".join(lit[r] for lit in letters) for r in range(6)]
    width = len(rows[0])
    sub = "N O R T H S E C   C T F   2 0 2 6   //   T H E   A R C H I V E".center(width)
    bar_t, bar_b = "▄" * width, "▀" * width
    return "\n".join(rows + ["", bar_t, sub, bar_b])


def badge(label, value, color):
    url = (
        "https://img.shields.io/badge/"
        f"{quote(label)}-{quote(value)}-{color}"
        "?style=flat-square&labelColor=0d1117"
    )
    return f"[![{label}]({url})](#02-navigation)"


def render_badges(stats):
    out = [
        badge("challenges", str(stats["total"]), "00e676"),
        badge("qualifications", str(stats["quals"]), "69f0ae"),
        badge("finals", str(stats["finals"]), "ff5252"),
        badge("categories", str(stats["cats"]), "40c4ff"),
        badge("operatives", str(stats["authors"]), "e040fb"),
        badge("flag format", "NSC{...}", "ffd740"),
    ]
    return " ".join(out)


def render_bootlog(stats):
    return "\n".join([
        "nsec@archive:~$ sudo ./mount --archive=northsec-ctf-2026",
        "[ OK ] mounted /dev/nsc2026 on /archive (read-only)",
        f"[ OK ] recovered {stats['total']} dossiers across {stats['cats']} categories",
        f"[ OK ] unlocked 🟢 qualification round :: {stats['quals']} dossiers",
        f"[ OK ] unlocked 🔴 finals round :: {stats['finals']} dossiers",
        f"[ OK ] indexed {stats['authors']} operatives in /archive/hall-of-fame",
        f"[ OK ] declassified {stats['writeups']} writeups :: sealed behind collapsibles",
        "[WARN] spoiler guard ACTIVE — expand briefings at your own risk",
        f"[ OK ] integrity check passed :: {stats['total']}/{stats['total']} dossiers accounted for",
        "nsec@archive:~$ cat README.md",
    ])


def box(lines, width=64):
    top = "╔" + "═" * (width - 2) + "╗"
    bot = "╚" + "═" * (width - 2) + "╝"
    body = ["║" + l[: width - 2].center(width - 2) + "║" for l in lines]
    return "\n".join([top] + body + [bot])


def threat_cell(rec):
    if rec["diff"] and rec["diff"] in DIFF_META:
        e, label = DIFF_META[rec["diff"]]
        return f"{e} `{label}`"
    e, label = DIFF_UNKNOWN
    return f"{e} `{label}`"


def details_block(rec):
    name = html.escape(rec["display"])
    author = (
        f"<i>{html.escape(rec['author'])}</i>"
        if rec["author"]
        else "<i>operative unknown</i>"
    )
    threat = threat_cell(rec)
    if rec["desc"]:
        brief = f"> {html.escape(rec['desc'], quote=False)}"
    else:
        brief = "> `// briefing classified — open the dossier to investigate`"
    access = [f"- 📂 dossier → [`{rec['key']}/`]({rec['link']})"]
    if rec["writeup"]:
        wlink = rec["link"] + "/" + quote(rec["writeup"], safe="/-._~")
        access.append(
            f"- 🔓 writeup → [`{rec['writeup']}`]({wlink}) · <i>solution inside</i>"
        )
    else:
        access.append("- 🔒 writeup → none on file")
    return "\n".join([
        "<details>",
        f"<summary>▸ <b>{name}</b> — {author} · {threat}</summary>",
        "<br>",
        "",
        "**BRIEFING**",
        "",
        brief,
        "",
        "**ACCESS**",
        "",
        *access,
        "",
        "</details>",
    ])


def render_round(records, round_name, title, subtitle):
    recs = [r for r in records if r["round"] == round_name]
    n_cats = len({r["cat"] for r in recs})
    header = box([
        title,
        f"{len(recs)} dossiers · {n_cats} categories · {subtitle}",
    ])
    parts = [f"```text\n{header}\n```", ""]
    for cat in CATEGORY_ORDER:
        cat_recs = [r for r in recs if r["cat"] == cat]
        if not cat_recs:
            continue
        emoji, flavor = CATEGORY_META[cat]
        plural = "dossiers" if len(cat_recs) != 1 else "dossier"
        parts.append(f"### {cat} [{round_name}]")
        parts.append("")
        parts.append(f"`// {emoji} {flavor} — {len(cat_recs)} {plural} recovered`")
        parts.append("")
        parts.append("| DOSSIER | OPERATIVE | THREAT | WRITEUP |")
        parts.append("|:---|:---|:---:|:---:|")
        for r in cat_recs:
            author = f"`{r['author']}`" if r["author"] else "`???`"
            wcell = "🔒" if r["writeup"] else "—"
            parts.append(
                f"| [{html.escape(r['display'])}]({r['link']}) | {author} "
                f"| {threat_cell(r)} | {wcell} |"
            )
        parts.append("")
        for r in cat_recs:
            parts.append(details_block(r))
            parts.append("")
    return "\n".join(parts).rstrip()


def bar(count, max_count, width=24):
    filled = round(width * count / max_count) if max_count else 0
    filled = max(filled, 1 if count else 0)
    return "█" * filled + "░" * (width - filled)


def render_unclassified(records):
    recs = [r for r in records if r["round"] is None]
    if not recs:
        return ""
    parts = [
        "```text",
        box(["⚠ UNCLASSIFIED DOSSIERS DETECTED",
             "add them to QUALS / FINALS in scripts/build_readme.py"]),
        "```",
        "",
        "| DOSSIER | OPERATIVE | THREAT | WRITEUP |",
        "|:---|:---|:---:|:---:|",
    ]
    for r in recs:
        author = f"`{r['author']}`" if r["author"] else "`???`"
        wcell = "🔒" if r["writeup"] else "—"
        parts.append(
            f"| [{html.escape(r['display'])}]({r['link']}) | {author} "
            f"| {threat_cell(r)} | {wcell} |"
        )
    return "\n".join(parts) + "\n"


def render_stats(records, stats):
    lines = []
    cat_counts = Counter(r["cat"] for r in records)
    mx = max(cat_counts.values())
    lines.append("DOSSIER DISTRIBUTION // BY CATEGORY")
    for cat, n in cat_counts.most_common():
        lines.append(f"{cat.lower():<8} {bar(n, mx)}  {n:>2}")
    lines.append("")
    lines.append("OPERATION SPLIT // BY ROUND")
    qm = max(stats["quals"], stats["finals"])
    lines.append(f"🟢 quals  {bar(stats['quals'], qm)}  {stats['quals']:>2}")
    lines.append(f"🔴 finals {bar(stats['finals'], qm)}  {stats['finals']:>2}")
    lines.append("")
    lines.append("THREAT LEVELS // DIFFICULTY")
    diff_counts = Counter(
        r["diff"] if r["diff"] else "N/A" for r in records
    )
    order = ["EASY", "MEDIUM", "MED-HARD", "HARD", "N/A"]
    dm = max(diff_counts.values())
    for d in order:
        n = diff_counts.get(d, 0)
        e, label = DIFF_META.get(d, DIFF_UNKNOWN)
        lines.append(f"{e} {label:<8} {bar(n, dm)}  {n:>2}")
    lines.append("")
    lines.append("DECLASSIFIED // WRITEUP COVERAGE")
    n_w = stats["writeups"]
    lines.append(
        f"{bar(n_w, stats['total'], width=30)}  {n_w} / {stats['total']}"
        f" ({n_w / stats['total']:.0%})"
    )
    return "\n".join(lines)


def render_hall_of_fame(records):
    known = {}
    unknown_cats = []
    for r in records:
        if r["author"]:
            entry = known.setdefault(r["author"], {"n": 0, "cats": set()})
            entry["n"] += 1
            entry["cats"].add(r["cat"])
        else:
            unknown_cats.append(r["cat"])
    rows = []
    ranked = sorted(known.items(), key=lambda kv: (-kv[1]["n"], kv[0].casefold()))
    for i, (name, e) in enumerate(ranked, 1):
        cats = " · ".join(c.lower() for c in CATEGORY_ORDER if c in e["cats"])
        rows.append(f"| `{i:02d}` | `{name}` | {e['n']} | {cats} |")
    if unknown_cats:
        cats = " · ".join(
            f"{c.lower()}" for c in CATEGORY_ORDER
            if c in unknown_cats
        )
        rows.append(f"| `??` | `???` *(unattributed)* | {len(unknown_cats)} | {cats} |")
    head = [
        "| RANK | OPERATIVE | DOSSIERS | DEPLOYMENTS |",
        "|:---:|:---|:---:|:---|",
    ]
    return "\n".join(head + rows)


def render_nav(stats):
    return "\n".join([
        f"| [`/archive/rounds/qualifications`](#03-the-qualifications-round) "
        f"| 🟢 {stats['quals']} dossiers | `open` |",
        f"| [`/archive/rounds/finals`](#04-the-finals-round) "
        f"| 🔴 {stats['finals']} dossiers | `open` |",
        "| [`/archive/stats`](#05-statistics) | 📊 distribution & coverage | `open` |",
        "| [`/archive/hall-of-fame`](#06-hall-of-fame) | 🏆 the operatives | `open` |",
        "| [`/archive/manual`](#07-field-manual) | 📖 how to use this vault | `open` |",
    ])


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------


def load_template():
    path = os.path.join(BASE, "scripts", "TEMPLATE.md")
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def main():
    ap = argparse.ArgumentParser(description="NSC // THE ARCHIVE README generator")
    ap.add_argument("--check", action="store_true",
                    help="verify every dossier is classified; exit 1 otherwise")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the README to stdout instead of writing it")
    args = ap.parse_args()

    records = discover()
    unclassified = [r for r in records if r["round"] is None]

    stats = {
        "total": len(records),
        "quals": sum(1 for r in records if r["round"] == "QUALS"),
        "finals": sum(1 for r in records if r["round"] == "FINALS"),
        "cats": len({r["cat"] for r in records}),
        "authors": len({r["author"] for r in records if r["author"]}),
        "writeups": sum(1 for r in records if r["writeup"]),
    }

    missing = (QUALS | FINALS) - {r["key"] for r in records}
    if missing:
        print("!! registry lists challenges that do not exist:", file=sys.stderr)
        for k in sorted(missing):
            print(f"   - {k}", file=sys.stderr)

    if args.check:
        ok = not unclassified and not missing and records
        print(
            f"check: {len(records)} dossiers — "
            f"{stats['quals']} quals / {stats['finals']} finals — "
            f"{len(unclassified)} unclassified, {len(missing)} missing"
        )
        sys.exit(0 if ok else 1)

    subs = {
        "{{BANNER}}": render_banner(),
        "{{BADGES}}": render_badges(stats),
        "{{BOOTLOG}}": render_bootlog(stats),
        "{{NAV_ROWS}}": render_nav(stats),
        "{{ROUND_QUALS}}": render_round(
            records, "QUALS", "ROUND 01 :: THE QUALIFICATIONS",
            "the road to the finals",
        ),
        "{{ROUND_FINALS}}": render_round(
            records, "FINALS", "ROUND 02 :: THE FINALS",
            "last teams standing",
        ),
        "{{STATS_BLOCK}}": render_stats(records, stats),
        "{{HALL_OF_FAME}}": render_hall_of_fame(records),
        "{{ROUND_UNCLASSIFIED}}": render_unclassified(records),
        "{{TOTAL}}": str(stats["total"]),
        "{{N_QUALS}}": str(stats["quals"]),
        "{{N_FINALS}}": str(stats["finals"]),
        "{{N_CATS}}": str(stats["cats"]),
        "{{N_AUTHORS}}": str(stats["authors"]),
        "{{N_WRITEUPS}}": str(stats["writeups"]),
        "{{GEN_DATE}}": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }

    out = load_template()
    for k, v in subs.items():
        out = out.replace(k, v)

    if args.dry_run:
        print(out)
    else:
        with open(os.path.join(BASE, "README.md"), "w", encoding="utf-8") as fh:
            fh.write(out)
        print(
            f"README.md regenerated — {stats['total']} dossiers "
            f"({stats['quals']} quals / {stats['finals']} finals), "
            f"{stats['writeups']} writeups, {stats['authors']} operatives."
        )


if __name__ == "__main__":
    main()
