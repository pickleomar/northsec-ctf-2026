# Challenge : Last-Seen 
## Author: Fairalien

# Last Seen Write Up
## Unzip the folder



```bash
└─$ unzip challenge.zip
```

## Check the backup roots

```bash
└─$ ls -la  MobileSync/Backup
total 20
drwxrwxr-x  5 fairalien fairalien 4096 Apr  8 16:16 .
drwxrwxr-x  3 fairalien fairalien 4096 Apr  8 16:16 ..
drwxrwxr-x 18 fairalien fairalien 4096 Apr  8 16:16 9f1a5c8f4ed2c7a1cb4a7db6c1c55e139ad8a2b4
drwxrwxr-x 16 fairalien fairalien 4096 Apr  8 16:16 c37a8d9b60f1aa52bd99a466eb0f6b8c274e13f1
drwxrwxr-x 18 fairalien fairalien 4096 Apr  8 16:16 f24be8d6e733bc91d0d4c92811bfbac97ef0a7d2
```

we got 3 backups, so the next step is to identify which one is the correct backup for our case

## Identify the correct backup

we can do it manually by checking info.plist file of each backup 

```bash
└─$ plistutil -i 9f1a5c8f4ed2c7a1cb4a7db6c1c55e139ad8a2b4/Info.plist 
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
        <key>BuildVersion</key>
        <string>21G93</string>
        <key>Device Name</key>
        <string>badr-iphone</string>
        <key>Display Name</key>
        <string>badr-iphone</string>
        <key>GUID</key>
        <string>5A3CAE37-3367-4037-B7E3-FC14977B575C</string>
        <key>IsEncrypted</key>
        <false/>
        <key>Last Backup Date</key>
        <date>2025-01-03T14:16:45Z</date>
        <key>Product Name</key>
        <string>iPhone 14 Pro</string>
        <key>Product Type</key>
        <string>iPhone15,2</string>
        <key>Product Version</key>
        <string>17.6.1</string>
        <key>Serial Number</key>
        <string>F2LZ9DFR0QX1</string>
        <key>Unique Identifier</key>
        <string>9f1a5c8f4ed2c7a1cb4a7db6c1c55e139ad8a2b4</string>
        <key>Phone Number</key>
        <string>+212600111222</string>
        <key>IMEI</key>
        <string>352986114762543</string>
        <key>MEID</key>
        <string>35298611476254</string>
</dict>
</plist>
```

from the 3 info.plist this one looks like the most current phone so the correct back up is: `9f1a5c8f4ed2c7a1cb4a7db6c1c55e139ad8a2b4`

and current device : `badr-iphone`

## Resolve the hashed artifact paths with `Manifest.db`

we can use sqlitebrowser or sqlite3 

<img width="1187" height="508" alt="image" src="https://github.com/user-attachments/assets/715c5939-e49c-4083-bde7-e96cd7d72752" />

like this we can easily map the artifacts to their file id

## Check the context artifacts first

to understand the context let’s check the aritfacts that can give us some context 

### Notes

<img width="941" height="215" alt="image" src="https://github.com/user-attachments/assets/7b7d56ce-c5de-4753-98e1-568f6c07ff0f" />

Relevant note:

- `before sunset. if he says upper path, don't wait below`
- `Ask Y. if the upper entrance is still open`

This tells us:

- there is a meeting before sunset
- the important person is likely someone whose name starts with **Y**

### Calendar

it has two tables: Location and CalendarItem

<img width="385" height="172" alt="image" src="https://github.com/user-attachments/assets/0357ad26-6fc0-480c-818c-137b84b38c98" />

<img width="229" height="185" alt="image" src="https://github.com/user-attachments/assets/fe963701-d94e-4a8a-b37a-53668bc98e8e" />

Relevant event:

- `Coffee` at `Café Hafa`
- starts `2025-01-01 17:30:00`
- ends `2025-01-01 18:30:00`

### Safari history

<img width="624" height="267" alt="image" src="https://github.com/user-attachments/assets/c6670f5e-cf29-4f85-90d6-d612ab3d3ff6" />

Important hits:

- `2025-01-01 17:18:00` → Cafe Hafa
- `2025-01-01 17:24:00` → sunset time tangier
- `2025-01-01 18:14:10` → taxi marshan tangier

This is the key narrative:

- Badr planned to go to Café Hafa
- after arriving, he later searched for a taxi to Marshan

## Confirm the actual arrival point from Wi-Fi

we can verify his last arrival point from wifi by checking the last joined wifi that will probably be his arrival point

```bash
└─$ plistutil -i c6/c663901a1df544dbbf002c6775da1bc5e271e6ec 
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
        <key>Version</key>
        <integer>2500</integer>
        <key>List of known networks</key>
        <array>
                <dict>
                        <key>SSID_STR</key>
                        <string>CAFE-HAFA-GUEST</string>
                        <key>LastJoined</key>
                        <date>2025-01-01T17:52:41Z</date>
                        <key>LastAutoJoined</key>
                        <date>2025-01-01T17:53:10Z</date>
                        <key>UpdatedAt</key>
                        <date>2025-01-01T17:56:00Z</date>
                        <key>SecurityMode</key>
                        <string>Open</string>
                        <key>Captive</key>
                        <false/>
                </dict>
                <dict>
                        <key>SSID_STR</key>
                        <string>Airport-WiFi</string>
                        <key>LastJoined</key>
                        <date>2024-12-22T08:14:00Z</date>
                        <key>LastAutoJoined</key>
                        <date>2024-12-22T08:15:00Z</date>
                        <key>UpdatedAt</key>
                        <date>2025-01-01T19:20:00Z</date>
                        <key>SecurityMode</key>
                        <string>Open</string>
                        <key>Captive</key>
                        <true/>
                </dict>
                <dict>
                        <key>SSID_STR</key>
                        <string>TangierCowork</string>
                        <key>LastJoined</key>
                        <date>2025-01-01T11:06:00Z</date>
                        <key>LastAutoJoined</key>
                        <date>2025-01-01T11:06:20Z</date>
                        <key>UpdatedAt</key>
                        <date>2025-01-01T11:07:00Z</date>
                        <key>SecurityMode</key>
                        <string>WPA2</string>
                        <key>Captive</key>
                        <false/>
                </dict>
                <dict>
                        <key>SSID_STR</key>
                        <string>Orange-Home-5G</string>
                        <key>LastJoined</key>
                        <date>2024-12-31T23:40:00Z</date>
                        <key>LastAutoJoined</key>
                        <date>2024-12-31T23:40:10Z</date>
                        <key>UpdatedAt</key>
                        <date>2024-12-31T23:41:00Z</date>
                        <key>SecurityMode</key>
                        <string>WPA2</string>
                        <key>Captive</key>
                        <false/>
                </dict>
        </array>
</dict>
</plist>
```

Important entries:

- `CAFE-HAFA-GUESTLastJoined = 2025-01-01 17:52:41`
- `Airport-WiFiUpdatedAt = 2025-01-01 19:20:00`

Do not fall for `Airport-WiFi`. Its `UpdatedAt` is later, but its `LastJoined` is older.

So the last joined wi-fi is: CAFE-HAFA-GUEST

This gives us:

- **Location** = `cafe hafa`
- SSID: `CAFE-HAFA-GUEST`

## Identify the coordinator from SMS

<img width="1111" height="386" alt="image" src="https://github.com/user-attachments/assets/40a421f5-24a6-4b49-9a15-d7bb6a99d58d" />

from the messages we can clearly conclude that the coordinator is the number with handle_id 1

<img width="462" height="210" alt="image" src="https://github.com/user-attachments/assets/e0f35c42-c5f4-4ad9-9f23-42949018e7b6" />

the number with that handle id is: +212687654321

## Map that number to a real contact

<img width="369" height="241" alt="image" src="https://github.com/user-attachments/assets/d57004ef-b97e-4513-9c36-0fcc5a1040d9" />

<img width="329" height="280" alt="image" src="https://github.com/user-attachments/assets/2f2b7fdd-f2e9-4c49-b928-caa2e64a9c6d" />

from the id we can conclude that Youssef is the owner of that number so the coordinator is : `Youssef`

This gives us:

- **Contact** = `Youssef`

## Check the call history after arrival

<img width="985" height="230" alt="image" src="https://github.com/user-attachments/assets/f4759748-5efd-4862-9990-fbb9f404684b" />

Relevant rows:

- `2025-01-01 17:10:00` → `+212644539290`, 402 sec, answered, cellular
- `2025-01-01 18:07:34` → `+212687654321`, 184 sec, answered, cellular
- `2025-01-01 18:08:40` → `+212699112233`, 611 sec, answered, `CALLTYPE = 8`
- `2025-01-01 18:12:00` → `+33612345678`, 520 sec, unanswered

The relevant call is **not** the global longest call in the database. It is the answered cellular call tied to the coordinator after arrival.

```bash
2025-01-01 18:07:34  +212687654321  answered  cellular
```

## Safari Search After Arrival

- `2025-01-01 17:18:00` → Cafe Hafa
- `2025-01-01 17:24:00` → sunset time tangier
- `2025-01-01 18:14:10` → taxi marshan tangier

from before we have these clue and since the call was at 18:07:34 then safari search that was after the call is: taxi marshan tangier

## Conclusion

Now combine the evidence:

1. Notes mention meeting before sunset and the upper path
2. Calendar shows a meetup at Café Hafa
3. Safari shows Cafe Hafa lookup before the meeting
4. Wi-Fi proves arrival at `CAFE-HAFA-GUEST`
5. SMS shows Youssef coordinating the meetup
6. An answered cellular call with Youssef happens after arrival
7. Right after that, Safari shows `taxi marshan tangier`

## flag

to get the flag u should collect all the answers in this format:

```bash
Device|Contact|SSID|CallTime|PostCallSearch
```

and get its sha256 hash and wrap it in NSC{}

so from all the investigation we did the flag would be 

```bash
badr-iphone|Youssef|CAFE-HAFA-GUEST|2025-01-01T18:07:34Z|taxi marshan tangier
```

let’s hash it

```bash
└─$ echo -n 'badr-iphone|Youssef|CAFE-HAFA-GUEST|2025-01-01T18:07:34Z|taxi marshan tangier' | sha256sum
f0c32a3b758affced247a0525f4dbe89f7c9f3a48bfdf9fbb9eba4553df7e3bb  -

```

so the flag would be:
`NSC{f0c32a3b758affced247a0525f4dbe89f7c9f3a48bfdf9fbb9eba4553df7e3bb}`
