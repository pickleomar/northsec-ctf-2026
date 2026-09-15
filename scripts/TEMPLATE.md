<div align="center">

```text
{{BANNER}}
```

{{BADGES}}

**NORTHSEC CTF 2026 · THE OFFICIAL CHALLENGE ARCHIVE**

*Every dossier from the operation — the 🟢 qualifications and the 🔴 finals — sealed in one vault.*

</div>

> [!WARNING]
> **SPOILER GUARD ACTIVE** — briefings are collapsed, writeups are classified, flags are redacted from this index. Expand at your own risk.

---

## 01. BOOT SEQUENCE

```text
{{BOOTLOG}}
```

## 02. NAVIGATION

```text
nsec@archive:~$ ls -R /archive
```

| NODE | CONTENT | STATUS |
|:---|:---|:---:|
{{NAV_ROWS}}

---

## 03. THE QUALIFICATIONS ROUND

{{ROUND_QUALS}}

---

## 04. THE FINALS ROUND

{{ROUND_FINALS}}

{{ROUND_UNCLASSIFIED}}---

## 05. STATISTICS

```text
{{STATS_BLOCK}}
```

---

## 06. HALL OF FAME

```text
nsec@archive:~$ cat /archive/hall-of-fame
```

{{HALL_OF_FAME}}

---

## 07. FIELD MANUAL

```text
man nsc-archive
```

**▸ FLAG FORMAT** — every flag follows the pattern `NSC{...}`. Dossier-local `flag.txt` files are placeholders for local replays; some deployments regenerate dynamic flags at boot.

**▸ DOSSIER STRUCTURE** — each dossier is a self-contained folder. Player-facing files live in `CHALLENGE/` (or equivalent), solutions are sealed in `WRITEUP/`.

**▸ RUNNING A DOSSIER** — most networked challenges ship their own infrastructure:

```bash
cd ./WEB/s0ng0k0 && docker compose up --build   # example — check the dossier for specifics
```

**▸ SPOILER ETIQUETTE** — 🔒 writeups stay sealed behind collapsibles; 🔓 links declassify them. What you declassify is on you.

**▸ REGENERATING THIS ARCHIVE** — this README is generated, never hand-edit it:

```bash
python3 scripts/build_readme.py          # rebuild README.md from scripts/TEMPLATE.md
python3 scripts/build_readme.py --check  # verify every dossier is classified
```

---

<div align="center">

<sub>archive synced {{GEN_DATE}} · {{TOTAL}} dossiers · {{N_QUALS}} quals / {{N_FINALS}} finals · {{N_WRITEUPS}} declassified writeups · {{N_AUTHORS}} operatives</sub>

<br>

<sub>built with <code>scripts/build_readme.py</code> — light it up again anytime</sub>

</div>
