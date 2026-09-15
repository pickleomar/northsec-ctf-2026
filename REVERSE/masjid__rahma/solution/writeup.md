Author : slamo

0x01: Introduction

Masjid Rahma was a reverse engineering challenge from NorthSec CTF. It featured a Ramadan-themed "Masjid OS" interface. While the theme was creative, the binary was packed with anti-debugging traps and a "rabbit hole" interface designed to distract the researcher.
0x02: Initial Reconnaissance

The first step was identifying the file type and security protections:
Bash

$ file masjid_rahma
masjid_rahma: ELF 64-bit LSB pie executable, x86-64, version 1 (SYSV), stripped

$ checksec --file=masjid_rahma
RELRO           STACK CANARY      NX            PIE             Symbols
Full RELRO      No canary found   NX enabled    PIE enabled     No Symbols

Key Findings:

    Stripped: No function names or debug symbols are present, requiring raw address analysis.

    PIE & NX: Modern protections are active, making runtime exploitation harder.

    Decoy Flag: Running strings revealed NSC{RAK_NADI_AKHI_MOU2MINE}, but the presence of ptrace and debugger warnings suggested this was a red herring.

0x03: Static Analysis & The Trap

The binary simulates "Masjid OS," which requires a specific sequence of "spiritual commands" to reach a decryption state. However, using radare2, I identified an anti-debugging check using ptrace. If a debugger is detected, the program prevents the user from reaching the real flag.
Reconstructing the Logic

Because the binary was stripped, I used r2 to reconstruct the program structure. I identified two interesting functions: main and fcn.00001e60.

The Blueprint Discovered:

    Ciphertext Location: The encrypted flag data is stored at offset 0x2a60.

    The Secret Key: A 64-bit hex value is hardcoded in the assembly: 0xfeedc0de12345678.

    The Algorithm: A sliding XOR loop. The binary iterates through the encrypted bytes and XORs each one with the corresponding byte of the 8-byte key.

0x04: The Solution

Rather than playing by the "Masjid OS" rules or fighting ptrace in GDB, I wrote a Python script to bypass the simulation entirely. By treating the binary as a raw data file, I "carved" the flag out directly.
The Decryption Script (solve.py)

0x05: Conclusion

The challenge was a classic "Rabbit Hole." By ignoring the intended UI and the anti-debugging traps, the problem was reduced to a simple data-extraction task. This transformed a complex reverse engineering puzzle into a straightforward XOR decryption.
