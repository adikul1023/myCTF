# Case 001: The Disappearance - Solution Walkthrough

> **CONFIDENTIAL**: This document is for CTF administrators only.
> Do NOT share with participants.

---

## Quick Reference

| Item | Value |
|------|-------|
| **Semantic Truth** | `d4ta.ex7ract@protonmail.ch:acb10e` |
| **Email Only** | `d4ta.ex7ract@protonmail.ch` |
| **Hash Prefix** | `acb10e` (SHA256 first 6 chars) |
| **Encrypted Form** | `U2FsdGVkX1+KzyITACK2aAnUm2JJfWia3o9tKZ2KX8V8mzilBkE2gSRdo4Q5dfIF` |
| **Encoding** | AES-256-CBC → ROT13 |
| **Decryption Key** | `nexus2024!` (from Challenge 3) |
| **Location** | `internal-tools/config/auth.yaml.bak` → `dev_settings.test_recipients[2]` |
| **Critical Commit** | `a7f3c21e8b9d4f6a2c1e0d8b7a6f5e4d3c2b1a0f` |
| **Stego Password** | `nexus2024!` |
| **Critical Timestamp** | `2024-11-14 23:48:12 UTC` |
| **External Contact** | `DataHaven` |

---

## Solution Path

### Challenge 1: Initial Assessment (75 points)
**Question**: Which repository contains evidence of credential cleanup?

**Solution**:
1. Review the GitHub organization export
2. Check `org_metadata.json` - notice Marcus has "inactive" status
3. Examine each repository's `commits.json` - **WARNING**: Contains 15+ commits with "cleanup" in the message
4. Filter for commits that:
   - Delete .bak files (backup files often contain secrets)
   - Have suspicious file deletion patterns (0 additions, high deletions)
   - Are authored by Marcus Chen around Sept 2024
5. Find the `internal-tools` repo has commit `a7f3c21` with:
   - Message: "cleanup: remove deprecated auth config"
   - Files: `auth.yaml`, `auth.yaml.bak`, `docs/auth-config.md`
   - Deletions: 47 lines (but .bak file still exists - incomplete cleanup!)
6. Cross-reference with bash_history.txt showing `git rm config/auth.yaml.bak` was attempted but failed

**Answer**: `internal-tools`

**Difficulty Factors**:
- 15+ noise cleanup commits across all repos
- Must recognize .bak file significance
- Requires correlation with shell history

---

### Challenge 2: Timeline Analysis (125 points)
**Question**: What was the exact UTC timestamp of the suspicious network burst?

**Solution**:
1. Open `network_traffic.pcap` in Wireshark (~500MB, 98K packets)
2. Apply display filter: `tls.handshake.extensions_server_name`
3. Look for anomalous destinations - most traffic is to known corporate sites
4. Identify connection to `104.21.67.185:443` with SNI `paste.sh`
5. Note the TCP stream shows:
   - POST request with 847KB upload
   - Connection only lasts 2.8 seconds (high bandwidth)
   - This is the ONLY connection to Cloudflare IP ending in .185
6. Extract timestamp from frame: `frame.time == "Nov 14, 2024 23:48:12 UTC"`
7. Verify by checking `tcp.stream eq 4847` shows large upload

**Answer**: `2024-11-14 23:48:12`

**Verification**: This timestamp is 72 seconds after the Telegram forward (23:47:00)

**Difficulty Factors**:
- ~500MB PCAP with 98K packets requires filtering
- No helper JSON - must use Wireshark skills
- Must recognize Cloudflare IP ranges
- Must distinguish legitimate vs suspicious TLS traffic

---

### Challenge 3: Hidden in Plain Sight (150 points)
**Question**: What is the password hidden in the steganographic payload?

**Solution**:
1. Analyze 312 images - NO manifest.json helper file provided
2. Identify steganography candidates:
   - Abstract/pattern images are common stego carriers
   - Check file sizes - stego images may be larger than expected
   - Use `exiftool` to check for metadata anomalies
3. Run automated stego detection:
   ```bash
   for img in *.png; do steghide info $img 2>/dev/null && echo "Found: $img"; done
   ```
4. Find `wallpaper_abstract_047.png` contains embedded data
5. Extract payload:
   ```bash
   steghide extract -sf wallpaper_abstract_047.png -p ""
   ```
6. Output: `nexus2024!`

**Answer**: `nexus2024!`

**Difficulty Factors**:
- No manifest hints - must scan all 312 images
- Must know steganography tools (steghide, zsteg, stegdetect)
- 14 images have modified EXIF as red herrings
- File naming suggests wallpaper, but pattern makes it suspicious

---

### Challenge 4: External Contact (100 points)
**Question**: Identify the Telegram handle of the external contact who coordinated the extraction.

**Solution**:
1. Parse `telegram_export/result.json` (850+ messages)
2. Filter for messages with `forwarded_from` field - **8 different contacts forward messages**
3. Forwarded contacts found:
   - `TechNewsDaily` (47 messages about crypto/security)
   - `SecOpsBot` (12 automated alerts)
   - `DataHaven` (1 message)
   - `CloudArchitect` (3 architecture discussions)
   - `DevMemes` (28 memes)
   - `OpenSourceDigest` (19 project updates)
   - `InfraAlerts` (8 monitoring alerts)
   - `HackerNewsBot` (15 links)
4. Analyze context and timestamps - find message ID 4847:
   - Date: Nov 14, 2024 23:47:00 (72 seconds BEFORE network burst)
   - From: `mchen__dev` (Marcus)
   - Forwarded from: `DataHaven`
   - Text: "Package ready. Confirm receipt within 24h."
   - This is the ONLY forwarded message from DataHaven
5. Correlation: This message timestamp → 72s later → paste.sh upload

**Answer**: `DataHaven`

**Difficulty Factors**:
- 8 different forwarded contacts (132 total forwarded messages)
- Must correlate timestamp with network traffic from Challenge 2
- Most forwarded messages are legitimate dev/tech content
- "DataHaven" name is suspicious but only 1 message to analyze

---

### Challenge 5: The Dead Drop - FINAL (300 points)
**Question**: What external email address was Marcus using to coordinate the data exfiltration?

**Solution Path**:

#### Step 1: Find the Hidden File
1. Navigate to `internal-tools/config/`
2. Find `auth.yaml.bak` (the backup file referenced in Challenge 1 cleanup commit)
3. Note the comment "Author: mchen" - this is Marcus's file

#### Step 2: Identify the Encrypted String
```yaml
dev_settings:
  test_recipients:
    # Base64 encoded to avoid email scrapers in logs
    - "YWRtaW5AbmV4dXNkeW4uY29t"      # admin@nexusdyn.com
    - "dGVzdEBuZXh1c2R5bi5jb20="      # test@nexusdyn.com
    - "U2FsdGVkX1+KzyITACK2aAnUm2JJfWia3o9tKZ2KX8V8mzilBkE2gSRdo4Q5dfIF"  # personal test addr - REMOVE
```

The third entry has no inline comment explaining it - suspicious. The prefix `U2FsdGVkX1` indicates OpenSSL encryption.

#### Step 3: Decrypt with Password from Challenge 3
**CRITICAL**: This challenge requires solving Challenge 3 first!

```bash
# Password from Challenge 3: nexus2024!
echo "U2FsdGVkX1+KzyITACK2aAnUm2JJfWia3o9tKZ2KX8V8mzilBkE2gSRdo4Q5dfIF" | \
  openssl enc -aes-256-cbc -a -d -pbkdf2 -k "nexus2024!"
```

Result: `q4gn.rk7enpg@cebgbaznvy.pu`

#### Step 4: Recognize and Decode ROT13
```python
import codecs

rotated = "q4gn.rk7enpg@cebgbaznvy.pu"
email = codecs.decode(rotated, 'rot_13')
# Result: d4ta.ex7ract@protonmail.ch
```

#### Step 5: Validate with Hash Prefix
The platform requires the first 6 characters of SHA256 hash to prevent guessing:

```python
import hashlib
email = "d4ta.ex7ract@protonmail.ch"
hash_prefix = hashlib.sha256(email.encode()).hexdigest()[:6]
# Result: acb10e
```

Submit: `d4ta.ex7ract@protonmail.ch:acb10e`

#### Step 6: Submit the Flag
The semantic truth is `d4ta.ex7ract@protonmail.ch:acb10e`

Players submit their personalized HMAC flag generated from this value.

**Difficulty Factors**:
- Requires password from Challenge 3 (interdependency)
- Three-layer encoding: AES-256-CBC → ROT13 → final answer
- Must recognize OpenSSL salted format
- Hash prefix validation prevents brute force
- No hints that stego password is the decryption key

---

## Correlation Matrix

All timestamps are UTC:

| Event | Timestamp | Source |
|-------|-----------|--------|
| Suspicious commit (credential cleanup) | 2024-09-03 02:14:33 | GitHub commits.json |
| ProtonMail login spike begins | 2024-11-08 | Browser history |
| DataHaven message forwarded | 2024-11-14 23:47:00 | Telegram export |
| Encrypted burst to paste.sh | 2024-11-14 23:48:12 | PCAP analysis |
| Last GitHub activity | 2024-11-15 00:02:44 | GitHub commits.json |
| Empty commit (timezone +8) | 2024-11-15 00:02:44 | GitHub commits.json |
| Disappearance reported | 2024-11-15 08:00:00 | Case briefing |

---

## Red Herrings Deployed

1. **15+ Cleanup Commits**: Across all repos with legitimate messages like "cleanup: remove unused imports", "cleanup: refactor tests", etc.
2. **Fake API Keys**: 23 realistic-looking API keys in commit messages and config files (8% of commits)
3. **Fork Repositories**: `python-crypto-utils-fork` and `data-exporter-fork` suggest crypto/exfil but contain nothing
4. **298 Noise Images**: Various screenshots, memes, wallpapers with random metadata
5. **14 Images with Modified EXIF**: GPS coordinates, camera models, timestamps - all irrelevant
6. **847 Irrelevant Messages**: Tech chat noise in Telegram export
7. **132 Forwarded Messages**: From 8 different contacts (TechNewsDaily, SecOpsBot, DevMemes, etc.)
8. **IMG_2847.jpg GPS**: Points to San Francisco but is irrelevant to the solution
9. **Timezone Inconsistencies**: Empty commit at +8 offset suggests international travel (red herring)
10. **Multiple Fake Emails**: 18 different test/admin emails across config files
11. **847K PCAP Packets**: 99.97%+ legitimate corporate traffic to GitHub, Slack, Google
12. **False Stego Positives**: 6 PNG files respond to `steghide info` with "could not extract" errors
13. **Encrypted Notes File**: `deleted_.notes.gpg` suggests relevance but is unrelated to solution
14. **Base64 Lookalikes**: 8 config values that look like base64 but decode to garbage

---

## Anti-Cheat Verification

### Flag Uniqueness
Each player's flag is generated via:
```
FLAG{HMAC-SHA256(user_salt || case_id || challenge_id, semantic_truth)}
```

### Timestamp Validation
Flags expire after 60 minutes. The `flag_salt` rotates every 24 hours.

### Pattern Detection
- Submission rate limited to 5/minute
- Answer similarity checking enabled
- Multiple accounts from same IP tracked

---

## Common Player Mistakes

1. **Missing the backup file**: Players focus on current `auth.yaml` instead of `.bak`
2. **Stopping at first cleanup commit**: 15+ cleanup commits exist, must correlate with .bak file deletion
3. **Using capture_spec.json**: No helper file exists - must analyze actual 3.2GB PCAP
4. **Not installing Wireshark**: Cannot solve Challenge 2 without proper tools
5. **Missing stego without manifest**: No hints provided - must scan all 312 images
6. **Trying all 8 forwarded contacts**: Must correlate Telegram timestamp with PCAP timestamp
7. **Attempting Challenge 5 without Challenge 3**: The decryption key is the stego password
8. **Partial decoding**: Some players decrypt AES but miss the ROT13 layer
9. **Forgetting hash validation**: Must append `:7a4e9f` to the email address
10. **Wrong timestamp format**: Must include seconds, UTC timezone
11. **Confusing subject with contact**: Marcus (mchen_dev) is the subject, DataHaven is the contact
12. **Using AI to decode without context**: AI can decode strings but can't find which string to decode
13. **Brute-forcing email domains**: Hash validation prevents guessing common email patterns

---

## Scoring Summary

| Challenge | Base Points | First Blood | Max Time Bonus |
|-----------|-------------|-------------|----------------|
| Initial Assessment | 75 | +75 | +18 |
| Timeline Analysis | 125 | +75 | +30 |
| Hidden in Plain Sight | 150 | +75 | +35 |
| External Contact | 100 | +75 | +25 |
| The Dead Drop | 300 | +100 | +75 |
| **Total Possible** | **750** | **+400** | **+183** |

**Maximum Score**: 1333 points (with all first bloods and perfect time bonuses)

**Difficulty Rating**: ⭐⭐⭐⭐⭐ (Expert/Advanced)

**Estimated Completion Time**:
- Expert DFIR analysts: 2-4 hours
- Intermediate with AI assistance: 3-6 hours  
- Beginner: 6-12 hours or DNF

---

## Deployment Checklist

- [ ] Generate ~500MB PCAP file with 98K packets (not JSON spec)
- [ ] Remove all helper files (manifest.json, capture_spec.json)
- [ ] Encrypt the third test_recipients entry with AES-256-CBC
- [ ] Add 15+ noise cleanup commits across repositories
- [ ] Add 132 forwarded messages from 8 different Telegram contacts
- [ ] Add 14 images with fake EXIF GPS coordinates
- [ ] Generate 6 false positive stego images
- [ ] Upload artifacts to MinIO storage (PCAP via CDN/external link)
- [ ] Update validators.py for hash prefix validation
- [ ] Run `seed_case.py seed` to register case in database
- [ ] Verify all hints are accessible (but reduced in helpfulness)
- [ ] Test flag generation with test user including hash validation
- [ ] Run `seed_case.py activate` to make case live
- [ ] Monitor first submissions for any issues
- [ ] Set up rate limiting for Challenge 5 (max 10 attempts/hour)

---

*Last updated: Generated during case creation*
