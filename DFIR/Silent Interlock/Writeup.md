# Silent Interlock Writeup
## Author: Fairalien
## Timeline

- 2026-04-17T21:06:13Z: `MARROWGATE\mara.ellis` authenticates to VPN from `198.51.100.77`.
- 2026-04-17T21:08:02Z: VPN session reaches `JUMP-01`.
- 2026-04-17T21:12:26Z: RDP proxy opens `ENG-WS01`.
- 2026-04-17T21:18:44Z: SafeLogicStudio opens the chemical dosing project.
- 2026-04-17T21:35:41Z: `PLC-CHEM` logic version changes.
- 2026-04-17T21:36:52Z: OPC UA write suppresses `ALM-CHM-0427`.
- 2026-04-17T21:37:04Z: Modbus write applies the dosing setpoint.
- 2026-04-17T21:37:10Z to 2026-04-17T21:48:10Z: pump runs while bypass valve is open.
- 2026-04-17T21:52:43Z: maintenance ticket is backfilled after the event.

## Initial Access

Correlate VPN, RADIUS, MFA, AD logon, jump-host auth, firewall, and EDR network records.
The decoy failed MFA and later contractor VPN session are unrelated.

## Engineering Workstation

`ENG-WS01` contains the RDP logon, RecentFiles/JumpLists entries, SafeLogicStudio process
creation, autosaves, compile logs, and upload records.

## PLC Logic Drift

Compare the before snapshot, after partial snapshot, diff cache, and reconstructed project
fragments. The removed condition is `NOT CHM_BYPASS_VALVE_OPEN`.

## HMI / Historian

HMI-01 accepted an OPC UA alarm suppression write, then held stale green status. The
historian blind window is recovered by aligning quality flags, ring records, recovered
segments, and PLC scan trace.

## Forged Ticket

`MW-2026-0417-CHM-1842` has an effective creation time before the event, but the audit
sequence and ENG-WS01 browser/file events show it was inserted after the upset.

## Answers

- q01: `MARROWGATE\mara.ellis`
- q02: `vpn-20260417-884216`
- q03: `JUMP-01`
- q04: `ENG-WS01`
- q05: `S-1-5-21-4107334210-2511681102-3907789116-1127`
- q06: `MW-2026-0417-CHM-1842`
- q07: `tickets/ticket_audit.log`
- q08: `2026-04-17T21:18:44Z`
- q09: `chemical_dosing`
- q10: `be1f6a21af9502446067d957f5dc29455bedaae8cfd1e256dbcf63aec110f807`
- q11: `8751fb65a949ed3421dff2c20f5ce2f9548845d5475414ec7b8ca062e49db205`
- q12: `NOT CHM_BYPASS_VALVE_OPEN`
- q13: `ALM-CHM-0427`
- q14: `CHM.PMP-201.RUN_FB`
- q15: `2026-04-17T21:37:10Z`
- q16: `2026-04-17T21:48:10Z`
- q17: `ns=4;s=HMI/Alarms/ALM-CHM-0427/Suppressed`
- q18: `7:40127`
- q19: `660`
- q20: `37.5`
- q21: `eng-span-001.pcapng.zst`
- q22: `7b974d5aebf47ae54d28fc31c7a1da7942f7d096b4a580a051bcd96e40a3aee3`
- q25: `237eb6bc7e52e7ca5874ca35d68254b018dc84a991e4407d68a5a0bdc78970cc`
