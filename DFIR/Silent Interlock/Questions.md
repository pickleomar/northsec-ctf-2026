# Silent Interlock Questions

Submit answers in the CTFd questions interface. Unless a prompt states otherwise, answers are case-insensitive and timestamps must be UTC in `YYYY-MM-DDTHH:MM:SSZ` format.

## Q01 (10 pts)
Which VPN account had the accepted authentication that later correlates to the OT access chain? Format: DOMAIN\user

## Q02 (10 pts)
What was the VPN session ID used for the OT access?

## Q03 (15 pts)
What was the first OT host reached after VPN login? Format: hostname

## Q04 (15 pts)
Which workstation was used for the unauthorized engineering action? Format: hostname

## Q05 (15 pts)
What was the compromised user's SID?

## Q06 (15 pts)
What was the maintenance ticket ID that was backfilled?

## Q07 (10 pts)
Which audit log source exposes the forged/backfilled maintenance event? Format: relative path

## Q08 (20 pts)
What was the exact UTC time the attacker first opened the engineering project? Format: YYYY-MM-DDTHH:MM:SSZ

## Q09 (15 pts)
Which PLC area was modified? Use the canonical area name from the project metadata.

## Q10 (20 pts)
What was the original SAFEPLC project VERSION_HASH for the modified PLC? Format: lowercase hex

## Q11 (20 pts)
What was the modified SAFEPLC project VERSION_HASH compiled for upload? Format: lowercase hex

## Q12 (30 pts)
Which exact SAFEPLC boolean condition was removed from CHM_DOSING_PUMP_P201_PERMISSIVE? Format: condition text only, e.g. NOT TAG_NAME

## Q13 (20 pts)
Which HMI alarm was suppressed? Format: alarm ID

## Q14 (20 pts)
Which canonical historian tag shows stale pump run-feedback data during the blind window? Format: tag name

## Q15 (20 pts)
What was the start time of the historian gap in UTC? Format: YYYY-MM-DDTHH:MM:SSZ

## Q16 (20 pts)
What was the end time of the historian gap in UTC? Format: YYYY-MM-DDTHH:MM:SSZ

## Q17 (30 pts)
Which exact OPC UA NodeId was written to hide the alarm state? Format: full NodeId string

## Q18 (35 pts)
What Modbus-style unit/register pair received the unauthorized dosing setpoint write? Format: unit:register

## Q19 (20 pts)
What was the unauthorized pump run duration in seconds?

## Q20 (20 pts)
What was the exact chemical dosing setpoint applied during the event? Use a decimal number only.

## Q21 (15 pts)
Which packet capture file contains the unauthorized dosing setpoint Modbus write? Format: filename only

## Q22 (45 pts)
What is the SHA256 of the reconstructed effective SAFEPLC project file? Format: lowercase hex

## Q25 (60 pts)
Final incident fingerprint. Compute sha256(vpn_session_id + "|" + compromised_sid + "|" + plc_area + "|" + removed_interlock_tag + "|" + historian_gap_start + "|" + historian_gap_end + "|" + reconstructed_project_sha256). Use the removed interlock tag name only, without NOT.
