# Far-Side Window
## Author : Fairalien

`#space #ccsds #telecommand #crc #protocol-recovery`

## Challenge

The artefacts are a relay-satellite downlink capture and engineering notes. The service opens a short uplink window, gives a 32-bit nonce, and expects one valid hex telecommand frame.

The notes give the important SIM-REL-3 shortcut:

```text
TAG = CRC16/X25(session_nonce || tc_header_and_data || auth_seed)
CLR_SAFE opcode = 0x52
CLR_SAFE argument = current SAFE_LATCH from HK
successful uplink must increment the last accepted TC counter
```

## Downlink Recovery

The binary starts on transfer-frame boundaries. Sync marker `1a cffc 1d` repeats every 60 bytes, so the frame size is 60 bytes.

For each transfer frame:

- bytes `4:6` contain the primary word; bits `15..6` recover the spacecraft id
- bytes `10:58` contain the packet zone
- APID `0x121` carries housekeeping, including `SAFE_LATCH` and the last accepted TC counter
- APID `0x1a1` carries the auth seed

Recovered state:

```text
spacecraft_id = 673 / 0x2a1
SAFE_LATCH   = 0x5a3c
last_counter = 0x0137
auth_seed    = 0xa55e
```

## Telecommand Format

The accepted frame is 12 bytes:

```text
primary_word || tc_counter || segment_header || opcode || argument || auth_tag || frame_crc
```

Fields:

```text
primary_word    = (spacecraft_id << 6) | (vcid=0 << 3) | (frame_type=2 << 1) | bypass=1
tc_counter      = last_counter + 1
segment_header  = 0xc1
opcode          = 0x52
argument        = SAFE_LATCH
auth_tag        = CRC16/X25(nonce || first_8_frame_bytes || auth_seed)
frame_crc       = CRC16/CCITT-FALSE(first_10_frame_bytes)
```

For test nonce `0x12345678`, the valid frame is:

```text
A8450138C1525A3C860BD48D
```

## PoC

The standalone recovery/uplink builder is:

```text
WRITEUP/far_side_window_recovery.py
```

It can build a frame for a captured nonce:

```bash
./WRITEUP/far_side_window_recovery.py --downlink ./Challenge/relay_downlink.bin --nonce 12345678
```

It can also complete the service interaction directly:

```bash
./WRITEUP/far_side_window_recovery.py --downlink ./Challenge/relay_downlink.bin --connect HOST PORT
```

Successful service response:

```text
TC ACCEPTED
SAFE MODE CLEARED
NSC{4R73M15_11_F4R_51D3_W1ND0W}
```
