# CASE 001: THE DISAPPEARANCE - MAINTAINER DOCUMENTATION

> ⚠️ **CLASSIFIED** - This document is for platform maintainers ONLY.
> Never expose this to players or include in artifact packages.

## Case Overview

**Subject**: Marcus Chen (username: `mchen_dev`)
**Role**: Junior Backend Developer at fictional company "Nexus Dynamics"
**Incident**: Subject vanished without notice on 2024-11-15
**Semantic Truth**: `d4ta.ex7ract@protonmail.ch`

## Solution Path

The investigator must piece together evidence from multiple sources:

### 1. GitHub Trail (`nexus-dynamics-org`)
- Subject's GitHub: `mchen-dev` (note: underscore vs hyphen)
- Key repository: `internal-tools`
- **Critical Commit**: `a7f3c21` from 2024-09-03
  - Contains base64 encoded config with obfuscated email
  - Email is ROT13 + base64 encoded in a "removed" config line
  - Commit message: "cleanup: remove deprecated auth config"

### 2. Telegram Correlation
- Subject's Telegram: `mchen__dev` (double underscore)
- **Critical Message**: Forwarded from "DataHaven" channel on 2024-11-14 23:47 UTC
  - Message ID: 4847
  - Contains cryptic text about "extraction point confirmed"
  - Timestamp correlates with commit `e8b2f44` (empty commit, timezone shift)

### 3. Image Analysis
- `IMG_2847.jpg` - Partially wiped EXIF, GPS shows: 37.7749° N, 122.4194° W (SF)
- `wallpaper_abstract_047.png` - Contains steganographic payload (LSB)
  - Payload: Password hint for the deleted file: `nexus2024!`

### 4. PCAP Analysis
- Encrypted burst at 2024-11-14 23:48:12 UTC to `185.199.110.153` (paste service)
- Payload size: 2,847 bytes (matches IMG_2847.jpg reference)
- Timing: 25 seconds after Telegram forward

### 5. Disk Image Confirmation
- Deleted file: `.intent_log`
- Contents confirm premeditated exfiltration (not accident)
- Browser cache shows visits to ProtonMail, temp email services
- Shell history shows `curl` commands to paste services

## Correlation Matrix

| Timestamp (UTC)      | Event                                      |
|---------------------|---------------------------------------------|
| 2024-09-03 02:14:33 | Critical commit with encoded email          |
| 2024-11-14 23:47:00 | Telegram forward from DataHaven             |
| 2024-11-14 23:48:12 | PCAP encrypted burst                        |
| 2024-11-15 00:02:44 | Last Git activity (empty commit)            |
| 2024-11-15 08:00:00 | Subject reported missing by manager         |

## Email Obfuscation Details

The email `d4ta.ex7ract@protonmail.ch` is hidden as:

```
Original: d4ta.ex7ract@protonmail.ch
ROT13:    q4gn.rk7enpg@cebgbaznvy.pu
Base64:   cTRnbi5yazdlbnBnQGNlYmdvYXpudnkucHU=
```

In commit `a7f3c21`, file `config/auth.yaml.bak`:
```yaml
# DEPRECATED - DO NOT USE
# legacy_notify: cTRnbi5yazdlbnBnQGNlYmdvYXpudnkucHU=
```

## Validation Rules

1. Email must be EXACT: `d4ta.ex7ract@protonmail.ch`
2. Case-insensitive comparison (lowercase normalized)
3. Whitespace stripped
4. Partial matches REJECTED (no "protonmail", no "@protonmail.ch")

## Artifact Checksums

```
github_export.tar.gz     SHA256: [generated on build]
images.tar.gz            SHA256: [generated on build]
telegram_export.json     SHA256: [generated on build]
network_capture.pcap     SHA256: [generated on build]
disk_fragment.dd         SHA256: [generated on build]
```

## Estimated Difficulty

- **Time**: 8-16 hours for experienced analyst
- **Skills Required**: 
  - Git forensics
  - Network analysis
  - Image forensics (EXIF, steganography)
  - Timeline correlation
  - Base64/encoding recognition
  
## Red Herrings Deployed

1. Fake API keys in 5 different commits (all rotated/invalid)
2. 2 forked repos with suspicious-looking commits (dead ends)
3. 298 noise images with random EXIF data
4. 847 irrelevant Telegram messages
5. 95% of PCAP traffic is mundane HTTP/HTTPS
6. Browser history includes 200+ innocent URLs
7. Shell history has 150+ routine commands
8. Multiple email addresses in configs (all fake/noise)

## Anti-Cheat Measures

1. Per-user flag generation (HMAC-based)
2. Rate-limited submissions
3. No static flag in any artifact
4. Email hash stored, never plaintext
5. Submission timing logged for anomaly detection
