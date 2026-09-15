<div align="center">

```text
▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄
   N O R T H S E C   C T F   2 0 2 6   //   T H E   A R C H I V E   
▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
```

[![Published challenges](https://img.shields.io/badge/challenges-41-00e676?style=flat-square&labelColor=0d1117)](#02-navigation) [![qualifications](https://img.shields.io/badge/qualifications-24-69f0ae?style=flat-square&labelColor=0d1117)](#02-navigation) [![finals](https://img.shields.io/badge/finals-17-ff5252?style=flat-square&labelColor=0d1117)](#02-navigation) [![categories](https://img.shields.io/badge/categories-7-40c4ff?style=flat-square&labelColor=0d1117)](#02-navigation) [![operatives](https://img.shields.io/badge/operatives-12-e040fb?style=flat-square&labelColor=0d1117)](#02-navigation) [![flag format](https://img.shields.io/badge/flag%20format-NSC%7B...%7D-ffd740?style=flat-square&labelColor=0d1117)](#02-navigation)

**NORTHSEC CTF 2026 · THE OFFICIAL CHALLENGE ARCHIVE**

*Every dossier from the operation — the 🟢 qualifications and the 🔴 finals — sealed in one vault.*

</div>

> [!WARNING]
> **SPOILER GUARD ACTIVE** — briefings are collapsed, writeups are classified, flags are redacted from this index. Expand at your own risk.

---

## 01. BOOT SEQUENCE

```text
nsec@archive:~$ sudo ./mount --archive=northsec-ctf-2026
[ OK ] mounted /dev/nsc2026 on /archive (read-only)
[ OK ] recovered 41 dossiers across 7 categories
[ OK ] unlocked 🟢 qualification round :: 24 dossiers
[ OK ] unlocked 🔴 finals round :: 17 dossiers
[ OK ] indexed 12 operatives in /archive/hall-of-fame
[ OK ] declassified 22 writeups :: sealed behind collapsibles
[WARN] spoiler guard ACTIVE — expand briefings at your own risk
[ OK ] integrity check passed :: 41/41 dossiers accounted for
nsec@archive:~$ cat README.md
```

## 02. NAVIGATION

```text
nsec@archive:~$ ls -R /archive
```

| NODE | CONTENT | STATUS |
|:---|:---|:---:|
| [`/archive/rounds/qualifications`](#03-the-qualifications-round) | 🟢 24 dossiers | `open` |
| [`/archive/rounds/finals`](#04-the-finals-round) | 🔴 17 dossiers | `open` |
| [`/archive/stats`](#05-statistics) | 📊 distribution & coverage | `open` |
| [`/archive/hall-of-fame`](#06-hall-of-fame) | 🏆 the operatives | `open` |
| [`/archive/manual`](#07-field-manual) | 📖 how to use this vault | `open` |

---

## 03. THE QUALIFICATIONS ROUND

```text
╔══════════════════════════════════════════════════════════════╗
║                ROUND 01 :: THE QUALIFICATIONS                ║
║     24 dossiers · 6 categories · the road to the finals      ║
╚══════════════════════════════════════════════════════════════╝
```

### CRYPTO [QUALS]

`// 🔐 cipher operations — 4 dossiers recovered`

| DOSSIER | OPERATIVE | THREAT | WRITEUP |
|:---|:---|:---:|:---:|
| [KRASNYKANAL](./CRYPTO/KRASNYKANAL) | `Zh3gh05t` | 🟡 `medium` | 🔒 |
| [ShinraTensei](./CRYPTO/ShinraTensei) | `Zh3gh05t` | 🟢 `easy` | 🔒 |
| [Structures](./CRYPTO/Structures) | `Zh3gh05t` | 🟢 `easy` | 🔒 |
| [The Enigmatic Vault](./CRYPTO/The%20Enigmatic%20Vault) | `Wiame5` | 🟡 `medium` | 🔒 |

<details>
<summary>▸ <b>KRASNYKANAL</b> — <i>Zh3gh05t</i> · 🟡 `medium`</summary>
<br>

**BRIEFING**

> You intercept a Russian communication channel. Putin has issued an ultimatum. Can you uncover the message before it sparks war?

**ACCESS**

- 📂 dossier → [`CRYPTO/KRASNYKANAL/`](./CRYPTO/KRASNYKANAL)
- 🔓 writeup → [`WRITEUP/README.md`](./CRYPTO/KRASNYKANAL/WRITEUP/README.md) · <i>solution inside</i>

</details>

<details>
<summary>▸ <b>ShinraTensei</b> — <i>Zh3gh05t</i> · 🟢 `easy`</summary>
<br>

**BRIEFING**

> someone should love pain to predict the future.

**ACCESS**

- 📂 dossier → [`CRYPTO/ShinraTensei/`](./CRYPTO/ShinraTensei)
- 🔓 writeup → [`WRITEUP/README.md`](./CRYPTO/ShinraTensei/WRITEUP/README.md) · <i>solution inside</i>

</details>

<details>
<summary>▸ <b>Structures</b> — <i>Zh3gh05t</i> · 🟢 `easy`</summary>
<br>

**BRIEFING**

> Alien has a message for us

**ACCESS**

- 📂 dossier → [`CRYPTO/Structures/`](./CRYPTO/Structures)
- 🔓 writeup → [`WRITEUP/README.md`](./CRYPTO/Structures/WRITEUP/README.md) · <i>solution inside</i>

</details>

<details>
<summary>▸ <b>The Enigmatic Vault</b> — <i>Wiame5</i> · 🟡 `medium`</summary>
<br>

**BRIEFING**

> You've intercepted an encrypted message from a mysterious organization. Intelligence suggests they use multiple layers of encryption to protect their secrets. Your mission: decrypt the message and find the flag.

**ACCESS**

- 📂 dossier → [`CRYPTO/The Enigmatic Vault/`](./CRYPTO/The%20Enigmatic%20Vault)
- 🔓 writeup → [`WRITEUP/README.md`](./CRYPTO/The%20Enigmatic%20Vault/WRITEUP/README.md) · <i>solution inside</i>

</details>

### PWN [QUALS]

`// 💥 memory corruption & exploitation — 3 dossiers recovered`

| DOSSIER | OPERATIVE | THREAT | WRITEUP |
|:---|:---|:---:|:---:|
| [Archivist’s Ritual](./PWN/Archivist%E2%80%99s%20Ritual) | `afk-Yato` | ⚪ `n/a` | 🔒 |
| [ksh](./PWN/ksh) | `BLD933` | ⚪ `n/a` | 🔒 |
| [necro-game](./PWN/necro-game) | `afk-Yato` | ⚪ `n/a` | 🔒 |

<details>
<summary>▸ <b>Archivist’s Ritual</b> — <i>afk-Yato</i> · ⚪ `n/a`</summary>
<br>

**BRIEFING**

> The Archivist guards ancient knowledge through a strange interface of rituals and channels. Scrolls may be summoned, channels may be sealed, and the oracle may whisper truths… or lies.

**ACCESS**

- 📂 dossier → [`PWN/Archivist’s Ritual/`](./PWN/Archivist%E2%80%99s%20Ritual)
- 🔓 writeup → [`WRITEUP/writeup.md`](./PWN/Archivist%E2%80%99s%20Ritual/WRITEUP/writeup.md) · <i>solution inside</i>

</details>

<details>
<summary>▸ <b>ksh</b> — <i>BLD933</i> · ⚪ `n/a`</summary>
<br>

**BRIEFING**

> `// briefing classified — open the dossier to investigate`

**ACCESS**

- 📂 dossier → [`PWN/ksh/`](./PWN/ksh)
- 🔓 writeup → [`WRITEUP/writeup.md`](./PWN/ksh/WRITEUP/writeup.md) · <i>solution inside</i>

</details>

<details>
<summary>▸ <b>necro-game</b> — <i>afk-Yato</i> · ⚪ `n/a`</summary>
<br>

**BRIEFING**

> `// briefing classified — open the dossier to investigate`

**ACCESS**

- 📂 dossier → [`PWN/necro-game/`](./PWN/necro-game)
- 🔓 writeup → [`WRITEUP/writeup.md`](./PWN/necro-game/WRITEUP/writeup.md) · <i>solution inside</i>

</details>

### REVERSE [QUALS]

`// 🧬 binary dissection — 6 dossiers recovered`

| DOSSIER | OPERATIVE | THREAT | WRITEUP |
|:---|:---|:---:|:---:|
| [casino_sfayga](./REVERSE/casino_sfayga) | `slamo` | ⚪ `n/a` | — |
| [Handshake](./REVERSE/Handshake) | `Fairalien` | ⚪ `n/a` | 🔒 |
| [INSIDE-ME](./REVERSE/INSIDE-ME) | `HoXoN` | 🟡 `medium` | — |
| [masjid__rahma](./REVERSE/masjid__rahma) | `slamo` | ⚪ `n/a` | 🔒 |
| [masjid_rahma_revenge](./REVERSE/masjid_rahma_revenge) | `slamo` | ⚪ `n/a` | — |
| [NOSTALGIA](./REVERSE/NOSTALGIA) | `HoXoN` | 🟢 `easy` | — |

<details>
<summary>▸ <b>casino_sfayga</b> — <i>slamo</i> · ⚪ `n/a`</summary>
<br>

**BRIEFING**

> ala one ala two blackjack tban rbhato l3ab 10 trbah 20 l3ab 20 trbah 50 l3ab 50 trbah 100 ala one ala two

**ACCESS**

- 📂 dossier → [`REVERSE/casino_sfayga/`](./REVERSE/casino_sfayga)
- 🔒 writeup → none on file

</details>

<details>
<summary>▸ <b>Handshake</b> — <i>Fairalien</i> · ⚪ `n/a`</summary>
<br>

**BRIEFING**

> find the intended way or else you'll be punished !

**ACCESS**

- 📂 dossier → [`REVERSE/Handshake/`](./REVERSE/Handshake)
- 🔓 writeup → [`Writeup.md`](./REVERSE/Handshake/Writeup.md) · <i>solution inside</i>

</details>

<details>
<summary>▸ <b>INSIDE-ME</b> — <i>HoXoN</i> · 🟡 `medium`</summary>
<br>

**BRIEFING**

> We found this high-performance calculator tool on a suspicious server. It claims to be optimized for speed, but our system admins noticed it's behaving strangely... oddly resource-heavy for simple addition.

**ACCESS**

- 📂 dossier → [`REVERSE/INSIDE-ME/`](./REVERSE/INSIDE-ME)
- 🔒 writeup → none on file

</details>

<details>
<summary>▸ <b>masjid__rahma</b> — <i>slamo</i> · ⚪ `n/a`</summary>
<br>

**BRIEFING**

> the imam told me that you are the talib that will take care of masjid rahma this week but i don't trust new people so i hide the flag so only pure people get it

**ACCESS**

- 📂 dossier → [`REVERSE/masjid__rahma/`](./REVERSE/masjid__rahma)
- 🔓 writeup → [`solution/writeup.md`](./REVERSE/masjid__rahma/solution/writeup.md) · <i>solution inside</i>

</details>

<details>
<summary>▸ <b>masjid_rahma_revenge</b> — <i>slamo</i> · ⚪ `n/a`</summary>
<br>

**BRIEFING**

> The Imam says you are the talib to guard Masjid Rahma this week, but after last time, I have no trust left. I have buried the truth where only a soul of perfect devotion can find it one wrong step, and the gates will remain closed forever/…

**ACCESS**

- 📂 dossier → [`REVERSE/masjid_rahma_revenge/`](./REVERSE/masjid_rahma_revenge)
- 🔒 writeup → none on file

</details>

<details>
<summary>▸ <b>NOSTALGIA</b> — <i>HoXoN</i> · 🟢 `easy`</summary>
<br>

**BRIEFING**

> We recovered an old floppy disk image from a dusty box in a Tokyo server room. It claims to hold a secret flag, but every time we run it on our standard terminals, we get "ACCESS DENIED".

**ACCESS**

- 📂 dossier → [`REVERSE/NOSTALGIA/`](./REVERSE/NOSTALGIA)
- 🔒 writeup → none on file

</details>

### WEB [QUALS]

`// 🌐 web exploitation — 4 dossiers recovered`

| DOSSIER | OPERATIVE | THREAT | WRITEUP |
|:---|:---|:---:|:---:|
| [dar-mohssinin](./WEB/dar-mohssinin) | `BlackMy7h` | ⚪ `n/a` | 🔒 |
| [Escape-The-Matrix](./WEB/Escape-The-Matrix) | `pickleomar` | ⚪ `n/a` | 🔒 |
| [Ouazzane](./WEB/Ouazzane) | `molzri3` | ⚪ `n/a` | — |
| [Shadow Sockets](./WEB/Shadow%20Sockets) | `BlackMy7h` | ⚪ `n/a` | — |

<details>
<summary>▸ <b>dar-mohssinin</b> — <i>BlackMy7h</i> · ⚪ `n/a`</summary>
<br>

**BRIEFING**

> `// briefing classified — open the dossier to investigate`

**ACCESS**

- 📂 dossier → [`WEB/dar-mohssinin/`](./WEB/dar-mohssinin)
- 🔓 writeup → [`SOLVE.md`](./WEB/dar-mohssinin/SOLVE.md) · <i>solution inside</i>

</details>

<details>
<summary>▸ <b>Escape-The-Matrix</b> — <i>pickleomar</i> · ⚪ `n/a`</summary>
<br>

**BRIEFING**

> There is a matrix and it should be escaped

**ACCESS**

- 📂 dossier → [`WEB/Escape-The-Matrix/`](./WEB/Escape-The-Matrix)
- 🔓 writeup → [`WRITEUP/Writeup.md`](./WEB/Escape-The-Matrix/WRITEUP/Writeup.md) · <i>solution inside</i>

</details>

<details>
<summary>▸ <b>Ouazzane</b> — <i>molzri3</i> · ⚪ `n/a`</summary>
<br>

**BRIEFING**

> I visited Ouazzane last spring — it was wonderful! I loved the vibe: no smog, no bad air, just fresh and cool breathing air. Welcome to Dardmana!

**ACCESS**

- 📂 dossier → [`WEB/Ouazzane/`](./WEB/Ouazzane)
- 🔒 writeup → none on file

</details>

<details>
<summary>▸ <b>Shadow Sockets</b> — <i>BlackMy7h</i> · ⚪ `n/a`</summary>
<br>

**BRIEFING**

> A realistic, multi-stage web security challenge that simulates infiltrating an abandoned cybercrime analytics dashboard. Players must navigate through honeypots, decode obfuscated protocols, and reconstruct split credentials to capture the…

**ACCESS**

- 📂 dossier → [`WEB/Shadow Sockets/`](./WEB/Shadow%20Sockets)
- 🔒 writeup → none on file

</details>

### MISC [QUALS]

`// 🌀 everything in between — 5 dossiers recovered`

| DOSSIER | OPERATIVE | THREAT | WRITEUP |
|:---|:---|:---:|:---:|
| [Coldtap](./MISC/Coldtap) | `Fairalien` | ⚪ `n/a` | 🔒 |
| [Far-Side Window](./MISC/Far-Side%20Window) | `Fairalien` | ⚪ `n/a` | 🔒 |
| [Gear 5](./MISC/Gear%205) | `Fairalien` | ⚪ `n/a` | 🔒 |
| [Genesis](./MISC/Genesis) | `Fairalien` | ⚪ `n/a` | — |
| [R4VENOUS](./MISC/R4VENOUS) | `???` | ⚪ `n/a` | 🔒 |

<details>
<summary>▸ <b>Coldtap</b> — <i>Fairalien</i> · ⚪ `n/a`</summary>
<br>

**BRIEFING**

> Sponsors at a conference received NFC hardware wallet badges that were supposed to prove booth attendance and unlock swag on-chain.

**ACCESS**

- 📂 dossier → [`MISC/Coldtap/`](./MISC/Coldtap)
- 🔓 writeup → [`WRITEUP/README.md`](./MISC/Coldtap/WRITEUP/README.md) · <i>solution inside</i>

</details>

<details>
<summary>▸ <b>Far-Side Window</b> — <i>Fairalien</i> · ⚪ `n/a`</summary>
<br>

**BRIEFING**

> During an Artemis II support test, the relay satellite LRS-7 went into safe mode after a bad command update. The team only saved two things from the last communication window: a downlink capture and a short engineering note.

**ACCESS**

- 📂 dossier → [`MISC/Far-Side Window/`](./MISC/Far-Side%20Window)
- 🔓 writeup → [`WRITEUP/README.md`](./MISC/Far-Side%20Window/WRITEUP/README.md) · <i>solution inside</i>

</details>

<details>
<summary>▸ <b>Gear 5</b> — <i>Fairalien</i> · ⚪ `n/a`</summary>
<br>

**BRIEFING**

> Some titles say more than they appear to. Look closer — character by character.

**ACCESS**

- 📂 dossier → [`MISC/Gear 5/`](./MISC/Gear%205)
- 🔓 writeup → [`WRITEUP/README.md`](./MISC/Gear%205/WRITEUP/README.md) · <i>solution inside</i>

</details>

<details>
<summary>▸ <b>Genesis</b> — <i>Fairalien</i> · ⚪ `n/a`</summary>
<br>

**BRIEFING**

> Thalassa Synthetics went dark 211 days ago. A sealed vial labeled SPECIMEN_0 was recovered from a drift canister in the North Atlantic last week. Sequencing returned the attached circular chromosome, 47,382 bp, minimal E. coli chassis, six…

**ACCESS**

- 📂 dossier → [`MISC/Genesis/`](./MISC/Genesis)
- 🔒 writeup → none on file

</details>

<details>
<summary>▸ <b>R4VENOUS</b> — <i>operative unknown</i> · ⚪ `n/a`</summary>
<br>

**BRIEFING**

> An operative known only as R4VENOUS went dark in late 2021. No formal exit. No forwarding address. Just silence. A conference flyer was recovered from a dead drop in Casablanca. Intel suggests he didn't disappear — he left a trail.…

**ACCESS**

- 📂 dossier → [`MISC/R4VENOUS/`](./MISC/R4VENOUS)
- 🔓 writeup → [`WRITEUP/writeup.pdf`](./MISC/R4VENOUS/WRITEUP/writeup.pdf) · <i>solution inside</i>

</details>

### DFIR [QUALS]

`// 🕵 digital forensics & incident response — 2 dossiers recovered`

| DOSSIER | OPERATIVE | THREAT | WRITEUP |
|:---|:---|:---:|:---:|
| [Last-Seen](./DFIR/Last-Seen) | `Fairalien` | ⚪ `n/a` | 🔒 |
| [Ransomware](./DFIR/Ransomware) | `SDIKIYOUSRA` | ⚪ `n/a` | 🔒 |

<details>
<summary>▸ <b>Last-Seen</b> — <i>Fairalien</i> · ⚪ `n/a`</summary>
<br>

**BRIEFING**

> Badr disappeared after heading to a meeting. Police recovered a copy of the `MobileSync/Backup` directory from his MacBook. Now your turn to investigate.

**ACCESS**

- 📂 dossier → [`DFIR/Last-Seen/`](./DFIR/Last-Seen)
- 🔓 writeup → [`Writeup.md`](./DFIR/Last-Seen/Writeup.md) · <i>solution inside</i>

</details>

<details>
<summary>▸ <b>Ransomware</b> — <i>SDIKIYOUSRA</i> · ⚪ `n/a`</summary>
<br>

**BRIEFING**

> `// briefing classified — open the dossier to investigate`

**ACCESS**

- 📂 dossier → [`DFIR/Ransomware/`](./DFIR/Ransomware)
- 🔓 writeup → [`writeup.md`](./DFIR/Ransomware/writeup.md) · <i>solution inside</i>

</details>

---

## 04. THE FINALS ROUND

```text
╔══════════════════════════════════════════════════════════════╗
║                    ROUND 02 :: THE FINALS                    ║
║       17 dossiers · 7 categories · last teams standing       ║
╚══════════════════════════════════════════════════════════════╝
```

### CRYPTO [FINALS]

`// 🔐 cipher operations — 3 dossiers recovered`

| DOSSIER | OPERATIVE | THREAT | WRITEUP |
|:---|:---|:---:|:---:|
| [GATOUZZ](./CRYPTO/GATOUZZ) | `Zh3gh05t` | 🟡 `medium` | — |
| [TOTL](./CRYPTO/TOTL) | `Zh3gh05t` | 🟢 `easy` | — |
| [TRAVEL](./CRYPTO/TRAVEL) | `Scriptmagum` | 🔴 `hard` | — |

<details>
<summary>▸ <b>GATOUZZ</b> — <i>Zh3gh05t</i> · 🟡 `medium`</summary>
<br>

**BRIEFING**

> simple math problem

**ACCESS**

- 📂 dossier → [`CRYPTO/GATOUZZ/`](./CRYPTO/GATOUZZ)
- 🔒 writeup → none on file

</details>

<details>
<summary>▸ <b>TOTL</b> — <i>Zh3gh05t</i> · 🟢 `easy`</summary>
<br>

**BRIEFING**

> entry level ,be confident

**ACCESS**

- 📂 dossier → [`CRYPTO/TOTL/`](./CRYPTO/TOTL)
- 🔒 writeup → none on file

</details>

<details>
<summary>▸ <b>TRAVEL</b> — <i>Scriptmagum</i> · 🔴 `hard`</summary>
<br>

**BRIEFING**

> some one said give up is not a solution, really ??

**ACCESS**

- 📂 dossier → [`CRYPTO/TRAVEL/`](./CRYPTO/TRAVEL)
- 🔒 writeup → none on file

</details>

### PWN [FINALS]

`// 💥 memory corruption & exploitation — 3 dossiers recovered`

| DOSSIER | OPERATIVE | THREAT | WRITEUP |
|:---|:---|:---:|:---:|
| [boom game](./PWN/boom%20game) | `afk-Yato` | ⚪ `n/a` | 🔒 |
| [cpp](./PWN/cpp) | `afk-Yato` | ⚪ `n/a` | 🔒 |
| [fsop](./PWN/fsop) | `afk-Yato` | ⚪ `n/a` | 🔒 |

<details>
<summary>▸ <b>boom game</b> — <i>afk-Yato</i> · ⚪ `n/a`</summary>
<br>

**BRIEFING**

> `// briefing classified — open the dossier to investigate`

**ACCESS**

- 📂 dossier → [`PWN/boom game/`](./PWN/boom%20game)
- 🔓 writeup → [`WRITEUP/writeup.md`](./PWN/boom%20game/WRITEUP/writeup.md) · <i>solution inside</i>

</details>

<details>
<summary>▸ <b>cpp</b> — <i>afk-Yato</i> · ⚪ `n/a`</summary>
<br>

**BRIEFING**

> `// briefing classified — open the dossier to investigate`

**ACCESS**

- 📂 dossier → [`PWN/cpp/`](./PWN/cpp)
- 🔓 writeup → [`WRITEUP/writeup.md`](./PWN/cpp/WRITEUP/writeup.md) · <i>solution inside</i>

</details>

<details>
<summary>▸ <b>fsop</b> — <i>afk-Yato</i> · ⚪ `n/a`</summary>
<br>

**BRIEFING**

> `// briefing classified — open the dossier to investigate`

**ACCESS**

- 📂 dossier → [`PWN/fsop/`](./PWN/fsop)
- 🔓 writeup → [`WRITEUP/writeup.md`](./PWN/fsop/WRITEUP/writeup.md) · <i>solution inside</i>

</details>

### REVERSE [FINALS]

`// 🧬 binary dissection — 2 dossiers recovered`

| DOSSIER | OPERATIVE | THREAT | WRITEUP |
|:---|:---|:---:|:---:|
| [ContextCollapse](./REVERSE/ContextCollapse) | `Fairalien` | ⚪ `n/a` | — |
| [Safety Profile](./REVERSE/Safety%20Profile) | `Fairalien` | ⚪ `n/a` | — |

<details>
<summary>▸ <b>ContextCollapse</b> — <i>Fairalien</i> · ⚪ `n/a`</summary>
<br>

**BRIEFING**

> No Description (^_^)

**ACCESS**

- 📂 dossier → [`REVERSE/ContextCollapse/`](./REVERSE/ContextCollapse)
- 🔒 writeup → none on file

</details>

<details>
<summary>▸ <b>Safety Profile</b> — <i>Fairalien</i> · ⚪ `n/a`</summary>
<br>

**BRIEFING**

> A field technician recovered a firmware update verifier from a discontinued HydraMesh industrial sensor gateway. The tool validates proprietary OTA update bundles before installation and enforces a device-specific safety profile for…

**ACCESS**

- 📂 dossier → [`REVERSE/Safety Profile/`](./REVERSE/Safety%20Profile)
- 🔒 writeup → none on file

</details>

### WEB [FINALS]

`// 🌐 web exploitation — 6 dossiers recovered`

| DOSSIER | OPERATIVE | THREAT | WRITEUP |
|:---|:---|:---:|:---:|
| [EM](./WEB/EM) | `molzri3` | ⚪ `n/a` | — |
| [enpcs](./WEB/enpcs) | `pickleomar` | ⚪ `n/a` | 🔒 |
| [Facbook-Tanjawi](./WEB/Facbook-Tanjawi) | `???` | ⚪ `n/a` | — |
| [mo7adata-revenge](./WEB/facebook) | `???` | ⚪ `n/a` | — |
| [ho9na](./WEB/ho9na) | `???` | ⚪ `n/a` | — |
| [s0ng0k0](./WEB/s0ng0k0) | `???` | 🟠 `med-hard` | — |

<details>
<summary>▸ <b>EM</b> — <i>molzri3</i> · ⚪ `n/a`</summary>
<br>

**BRIEFING**

> HATE , HATE , HATE flag in the local file in /flag.txt no coded provided should be fine without your claud code

**ACCESS**

- 📂 dossier → [`WEB/EM/`](./WEB/EM)
- 🔒 writeup → none on file

</details>

<details>
<summary>▸ <b>enpcs</b> — <i>pickleomar</i> · ⚪ `n/a`</summary>
<br>

**BRIEFING**

> What appears to be truth is often only the result of rules, timing, and information we chose to trust. Change one, and reality begins to look different. Change them all, and even the truth can become a falsehood.

**ACCESS**

- 📂 dossier → [`WEB/enpcs/`](./WEB/enpcs)
- 🔓 writeup → [`WRITEUP/writeup.md`](./WEB/enpcs/WRITEUP/writeup.md) · <i>solution inside</i>

</details>

<details>
<summary>▸ <b>Facbook-Tanjawi</b> — <i>operative unknown</i> · ⚪ `n/a`</summary>
<br>

**BRIEFING**

> `// briefing classified — open the dossier to investigate`

**ACCESS**

- 📂 dossier → [`WEB/Facbook-Tanjawi/`](./WEB/Facbook-Tanjawi)
- 🔒 writeup → none on file

</details>

<details>
<summary>▸ <b>mo7adata-revenge</b> — <i>operative unknown</i> · ⚪ `n/a`</summary>
<br>

**BRIEFING**

> `// briefing classified — open the dossier to investigate`

**ACCESS**

- 📂 dossier → [`WEB/facebook/`](./WEB/facebook)
- 🔒 writeup → none on file

</details>

<details>
<summary>▸ <b>ho9na</b> — <i>operative unknown</i> · ⚪ `n/a`</summary>
<br>

**BRIEFING**

> `// briefing classified — open the dossier to investigate`

**ACCESS**

- 📂 dossier → [`WEB/ho9na/`](./WEB/ho9na)
- 🔒 writeup → none on file

</details>

<details>
<summary>▸ <b>s0ng0k0</b> — <i>operative unknown</i> · 🟠 `med-hard`</summary>
<br>

**BRIEFING**

> A realistic enterprise-style vulnerability challenge teaching blind Out-of-Band deserialization exploitation through Python pickle attacks.

**ACCESS**

- 📂 dossier → [`WEB/s0ng0k0/`](./WEB/s0ng0k0)
- 🔒 writeup → none on file

</details>

### MISC [FINALS]

`// 🌀 everything in between — 1 dossier recovered`

| DOSSIER | OPERATIVE | THREAT | WRITEUP |
|:---|:---|:---:|:---:|
| [Cold Chain](./MISC/Cold%20Chain) | `Fairalien` | ⚪ `n/a` | — |

<details>
<summary>▸ <b>Cold Chain</b> — <i>Fairalien</i> · ⚪ `n/a`</summary>
<br>

**BRIEFING**

> A refrigerated pharmaceutical warehouse lost its routing table during a controller outage. The conveyors still run, but the diagnostic console only exposes noisy calibration telemetry. Your job is to reconstruct enough of the warehouse to…

**ACCESS**

- 📂 dossier → [`MISC/Cold Chain/`](./MISC/Cold%20Chain)
- 🔒 writeup → none on file

</details>

### DFIR [FINALS]

`// 🕵 digital forensics & incident response — 1 dossier recovered`

| DOSSIER | OPERATIVE | THREAT | WRITEUP |
|:---|:---|:---:|:---:|
| [Silent Interlock](./DFIR/Silent%20Interlock) | `Fairalien` | ⚪ `n/a` | 🔒 |

<details>
<summary>▸ <b>Silent Interlock</b> — <i>Fairalien</i> · ⚪ `n/a`</summary>
<br>

**BRIEFING**

> Marrowgate WTP experienced an unexplained process upset during a planned maintenance window. There is no remote service, no local checker, and no embedded flag. Investigate the provided forensic evidence and submit answers through the CTFd…

**ACCESS**

- 📂 dossier → [`DFIR/Silent Interlock/`](./DFIR/Silent%20Interlock)
- 🔓 writeup → [`Writeup.md`](./DFIR/Silent%20Interlock/Writeup.md) · <i>solution inside</i>

</details>

### WASM [FINALS]

`// ⚙ webassembly natives — 1 dossier recovered`

| DOSSIER | OPERATIVE | THREAT | WRITEUP |
|:---|:---|:---:|:---:|
| [buzzk1ll](./WASM/buzzk1ll) | `BlackMy7h` | ⚪ `n/a` | — |

<details>
<summary>▸ <b>buzzk1ll</b> — <i>BlackMy7h</i> · ⚪ `n/a`</summary>
<br>

**BRIEFING**

> Open the challenge URL in a browser and recover the real flag.

**ACCESS**

- 📂 dossier → [`WASM/buzzk1ll/`](./WASM/buzzk1ll)
- 🔒 writeup → none on file

</details>

---

## 05. STATISTICS

```text
DOSSIER DISTRIBUTION // BY CATEGORY
web      ████████████████████████  10
reverse  ███████████████████░░░░░   8
crypto   █████████████████░░░░░░░   7
pwn      ██████████████░░░░░░░░░░   6
misc     ██████████████░░░░░░░░░░   6
dfir     ███████░░░░░░░░░░░░░░░░░   3
wasm     ██░░░░░░░░░░░░░░░░░░░░░░   1

OPERATION SPLIT // BY ROUND
🟢 quals  ████████████████████████  24
🔴 finals █████████████████░░░░░░░  17

THREAT LEVELS // DIFFICULTY
🟢 easy     ███░░░░░░░░░░░░░░░░░░░░░   4
🟡 medium   ███░░░░░░░░░░░░░░░░░░░░░   4
🟠 med-hard █░░░░░░░░░░░░░░░░░░░░░░░   1
🔴 hard     █░░░░░░░░░░░░░░░░░░░░░░░   1
⚪ n/a      ████████████████████████  31

DECLASSIFIED // WRITEUP COVERAGE
████████████████░░░░░░░░░░░░░░  22 / 41 (54%)
```

---

## 06. HALL OF FAME

```text
nsec@archive:~$ cat /archive/hall-of-fame
```

| RANK | OPERATIVE | DOSSIERS | DEPLOYMENTS |
|:---:|:---|:---:|:---|
| `01` | [Fairalien](https://github.com/alaeddine03) | 10 | reverse · misc · dfir |
| `02` | [afk-Yato](https://github.com/afk-Yato) | 5 | pwn |
| `03` | [Zh3gh05t](https://github.com/Zh3gh05t) | 5 | crypto |
| `04` | [BlackMy7h](https://github.com/BlackMy7h) | 3 | web · wasm |
| `05` | [slamo](https://github.com/slamo1566) | 3 | reverse |
| `06` | [HoXoN](https://github.com/hassanbencheikh) | 2 | reverse |
| `07` | [molzri3](https://github.com/molzri3) | 2 | web |
| `08` | [pickleomar](https://github.com/pickleomar) | 2 | web |
| `09` | [BLD933](https://github.com/BLD933) | 1 | pwn |
| `10` | [Scriptmagum](https://github.com/Scriptmagum) | 1 | crypto |
| `11` | [SDIKIYOUSRA](https://github.com/SDIKIYOUSRA) | 1 | dfir |
| `12` | [Wiame5](https://github.com/Wiame5) | 1 | crypto |
| `??` | `???` *(unattributed)* | 5 | web · misc |

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

