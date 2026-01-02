# Case 001: The Disappearance - Skills Assessment Matrix

**CONFIDENTIAL - INTERNAL DOCUMENTATION**  
**For CTF Administrators and Educators Only**

---

## Overview

Case 001 is designed as an **intermediate-level** digital forensics investigation that tests a comprehensive suite of DFIR (Digital Forensics and Incident Response) skills through a realistic insider threat scenario.

---

## Skills Taxonomy

### 🔴 Core Technical Skills (Required for Completion)

#### 1. **Digital Forensics Fundamentals**
- **Artifact Correlation**: Ability to correlate timestamps across multiple evidence sources (GitHub commits, Telegram messages, PCAP traffic, bash history)
- **Timeline Reconstruction**: Building a coherent narrative from fragmented temporal data
- **Evidence Preservation**: Understanding that artifacts must be analyzed without modification
- **Chain of Custody**: Recognizing that each artifact type represents a different collection point

**Assessment Points**:
- Can the player identify the 72-second delta between Telegram forward (23:47:00) and network burst (23:48:12)?
- Do they recognize the causal relationship between artifacts?
- Can they distinguish between correlation and causation?

#### 2. **File System Forensics**
- **Deleted File Recovery**: Understanding that deleted files may be recoverable from unallocated space
- **File Carving**: Concept that fragments of files persist after deletion
- **Metadata Analysis**: MAC (Modified, Accessed, Created) timestamps tell a story
- **Partial Recovery**: Real forensics rarely recovers 100% of data

**Assessment Points**:
- Do they recognize `deleted_.intent_log.txt` as a recovered file?
- Can they interpret the "38% recovery" notation realistically?
- Do they understand why the file is PGP-encrypted with corrupted blocks?

#### 3. **Network Traffic Analysis**
- **Protocol Analysis**: Understanding TLS 1.3 traffic characteristics
- **SNI (Server Name Indication)**: Identifying destination services from encrypted traffic
- **Anomaly Detection**: Recognizing outlier behavior in traffic patterns
- **Payload Size Analysis**: Inferring content type from upload/download volumes

**Assessment Points**:
- Can they identify the paste.sh connection as anomalous?
- Do they correlate the 847KB upload size with config file exfiltration?
- Can they interpret "only connection to this IP in entire capture" as significant?

#### 4. **Git Forensics**
- **Commit History Analysis**: Mining commit logs for suspicious activity
- **Backup File Discovery**: Understanding developers leave .bak files
- **Author Attribution**: Tracking who made specific changes
- **Diff Analysis**: Understanding what was deleted in "cleanup" commits

**Assessment Points**:
- Can they navigate 150-300 commits per repository to find the critical one?
- Do they recognize commit `a7f3c21` with message "cleanup: remove deprecated auth config" as suspicious?
- Can they locate the backup file that wasn't deleted?

#### 5. **OSINT & Social Engineering Awareness**
- **Chat Log Analysis**: Extracting signal from noise in communication channels
- **Forwarded Message Significance**: Understanding forwarded content suggests external coordination
- **Handle vs. Real Name**: Distinguishing between usernames and identities
- **Operational Security**: Recognizing that "DataHaven" is an operational contact

**Assessment Points**:
- Can they filter 850+ messages to find message #4847?
- Do they recognize "Package ready. Confirm receipt within 24h." as coded language?
- Can they identify the forwarded_from field as the critical data point?

---

### 🟠 Intermediate Technical Skills (Enhances Investigation)

#### 6. **Cryptography & Encoding**
- **Base64 Recognition**: Identifying base64-encoded strings by pattern
- **ROT13 Cipher**: Basic substitution cipher understanding
- **Multi-Stage Encoding**: Chaining encoding methods (ROT13 → Base64)
- **Encoding Context**: Understanding why developers encode (scraper avoidance, not security)

**Assessment Points**:
- Can they recognize `cTRnbi5yazdlbnBnQGNlYmdiYXpudnkucHU=` as base64?
- Do they decode to get `q4gn.rk7enpg@cebgbaznvy.pu` and recognize ROT13?
- Can they decode to final answer `d4ta.ex7ract@protonmail.ch`?

#### 7. **EXIF Metadata Manipulation**
- **GPS Coordinate Extraction**: Reading EXIF location data
- **Partial Wipe Detection**: Recognizing when EXIF fields are selectively deleted
- **Device Identification**: Using Make/Model to profile the subject
- **Timestamp Analysis**: Understanding DateTimeOriginal vs. file timestamps

**Assessment Points**:
- Can they extract GPS coordinates from IMG_2847.jpg?
- Do they recognize the San Francisco location (37.7749, -122.4194)?
- Can they identify that DateTimeOriginal and Software fields were intentionally wiped?

#### 8. **Steganography Detection**
- **LSB Steganography**: Understanding Least Significant Bit embedding
- **Tool Proficiency**: Using steghide, zsteg, or similar tools
- **File Selection**: Identifying which files are likely stego carriers (abstract images)
- **Payload Extraction**: Recovering hidden data from cover media

**Assessment Points**:
- Can they identify wallpaper_abstract_047.png as suspicious among 312 images?
- Do they use appropriate tools (steghide, stegdetect) to find the payload?
- Can they extract `nexus2024!` successfully?

#### 9. **Shell Command Analysis**
- **Bash History Forensics**: Understanding command chronology
- **Anti-Forensics Detection**: Recognizing shred, rm -f, and cleanup attempts
- **Pipeline Understanding**: Interpreting command chains (tar | openssl | curl)
- **Evidence of Intent**: Commands reveal planning and execution

**Assessment Points**:
- Can they interpret the command sequence at the end of bash_history.txt?
- Do they recognize `tar -czf export.tar.gz ~/projects/internal-tools/config/` as data staging?
- Can they understand `openssl enc -aes-256-cbc` is encryption before exfil?
- Do they see `shred -vfz -n 3` as evidence of anti-forensics?

#### 10. **Browser History Forensics**
- **Pattern Recognition**: Identifying spikes in specific site visits
- **Service Identification**: Recognizing ProtonMail, paste.sh, temp-mail.org as OPSEC tools
- **Visit Count Analysis**: Higher visit counts = repeated use = significance
- **Temporal Clustering**: Multiple visits to same service in short timeframe

**Assessment Points**:
- Can they identify 15 visits to protonmail.com/login as significant?
- Do they recognize paste.sh visits 2 hours before the network burst?
- Can they interpret temp-mail.org visits as burner email setup?

---

### 🟡 Advanced Analytical Skills (Expert Level)

#### 11. **Behavioral Analysis**
- **Insider Threat Profiling**: Recognizing patterns of malicious insider behavior
- **Premeditation Evidence**: Identifying planning vs. impulsive actions
- **OPSEC Awareness**: Understanding subject's operational security measures
- **Psychological Indicators**: Interpreting artifacts through behavioral lens

**Assessment Points**:
- Do they recognize this is premeditated (browser history shows ProtonMail setup weeks earlier)?
- Can they identify the OPSEC measures (encoding, encryption, shredding)?
- Do they understand the significance of timezone shifts in final commit (travel preparation)?

#### 12. **Multi-Source Intelligence Fusion**
- **Cross-Artifact Validation**: Using multiple sources to confirm single finding
- **Contradiction Resolution**: Handling conflicting information across artifacts
- **Confidence Assessment**: Understanding which evidence is stronger
- **Holistic Reasoning**: Building complete picture from incomplete data

**Assessment Points**:
- Can they validate the timeline using GitHub + Telegram + PCAP together?
- Do they use the encoded email in Git to validate browser ProtonMail activity?
- Can they correlate the stego password with the encrypted notes file?

#### 13. **Red Herring Filtering**
- **Signal-to-Noise Discrimination**: Identifying relevant vs. irrelevant data
- **Misdirection Detection**: Recognizing planted false leads
- **Confirmation Bias Resistance**: Not anchoring on first suspicious finding
- **Volume Management**: Handling large datasets (312 images, 850 messages, 300 commits)

**Assessment Points**:
- Do they waste time on the 2 fork repositories (red herrings)?
- Can they ignore the 298 noise images and focus on the 2 critical ones?
- Do they avoid chasing the 5 fake API keys scattered in commits?
- Can they distinguish Marcus's suspicious activity from normal dev work?

#### 14. **Reporting & Documentation**
- **Evidence Organization**: Structuring findings logically
- **Chain of Reasoning**: Explaining how conclusions were reached
- **Confidence Levels**: Distinguishing certain vs. probable findings
- **Professional Communication**: Writing for technical and non-technical audiences

**Assessment Points** (if written reports are required):
- Can they produce a timeline with supporting evidence?
- Do they cite specific artifacts (commit hashes, message IDs, timestamps)?
- Can they explain the exfiltration method clearly?
- Do they distinguish between confirmed facts and inferences?

---

## Cognitive Skills Assessment

### **Critical Thinking**
- **Pattern Recognition**: Identifying the "test_recipients" array pattern with 3 base64 strings
- **Anomaly Detection**: Recognizing that 1 of 3 base64 strings has no inline comment
- **Hypothesis Testing**: Testing if the uncommented string is significant
- **Logical Deduction**: Inferring that the hidden email is the coordination channel

### **Problem Solving**
- **Decomposition**: Breaking the case into 5 distinct challenge areas
- **Sequential Reasoning**: Understanding Challenge 5 requires solving Challenges 1-4
- **Tool Selection**: Choosing appropriate tools for each artifact type
- **Iteration**: Trying multiple approaches when initial methods fail

### **Attention to Detail**
- **Precision**: Finding message ID 4847 out of 850 messages
- **Context Awareness**: Recognizing "forwarded_from" as more significant than "from"
- **Subtle Clues**: Noticing the empty commit message near disappearance
- **Metadata Reading**: Checking file recovery percentage (38%) in the notes file

### **Research & Learning**
- **Tool Discovery**: Finding and learning steghide, exiftool if unfamiliar
- **Documentation Reading**: Understanding tool syntax and options
- **Community Resources**: Searching for steganography detection guides
- **Adaptation**: Applying known techniques to new scenarios

---

## Difficulty Calibration

### **Challenge 1: Initial Assessment** (50 points)
**Skill Level**: Beginner  
**Primary Skill**: Git forensics basics  
**Time Estimate**: 5-10 minutes  
**Success Rate**: 85-90%

Players who understand Git commit logs and can search for keywords like "cleanup" or "deprecated" will succeed quickly.

### **Challenge 2: Timeline Analysis** (75 points)
**Skill Level**: Beginner-Intermediate  
**Primary Skill**: Network traffic analysis  
**Time Estimate**: 15-20 minutes  
**Success Rate**: 70-80%

Requires basic Wireshark or PCAP analysis skills. The capture_spec.json provides critical_traffic with explicit timestamp, so tool mastery isn't required.

### **Challenge 3: Hidden in Plain Sight** (100 points)
**Skill Level**: Intermediate  
**Primary Skill**: Steganography detection  
**Time Estimate**: 30-45 minutes  
**Success Rate**: 50-65%

This is the first real skill gate. Players unfamiliar with steganography must research tools and methods. The manifest.json provides a hint with the "stego_payload" notation.

### **Challenge 4: External Contact** (75 points)
**Skill Level**: Intermediate  
**Primary Skill**: Chat log analysis  
**Time Estimate**: 20-30 minutes  
**Success Rate**: 60-75%

Requires patience to filter 850+ messages. Players who use `jq` or Python to filter will succeed faster than those manually scrolling.

### **Challenge 5: The Dead Drop** (200 points)
**Skill Level**: Advanced  
**Primary Skill**: Multi-stage decoding, artifact correlation  
**Time Estimate**: 60-90 minutes  
**Success Rate**: 30-45%

This is the capstone challenge requiring:
1. Finding the auth.yaml.bak file (correlation with Challenge 1)
2. Identifying the suspicious base64 string (pattern recognition)
3. Decoding base64 (technical skill)
4. Recognizing ROT13 from gibberish output (cryptography knowledge)
5. Decoding ROT13 (technical skill)
6. Submitting the personalized HMAC flag (platform understanding)

---

## Learning Outcomes

Upon completing Case 001, players will have demonstrated ability to:

✅ **Conduct multi-artifact digital forensic investigations**  
✅ **Correlate temporal data across disparate sources**  
✅ **Identify and decode obfuscated data**  
✅ **Analyze network traffic for anomalous behavior**  
✅ **Extract metadata from various file types**  
✅ **Detect and extract steganographic payloads**  
✅ **Analyze shell command history for malicious activity**  
✅ **Filter signal from noise in large datasets**  
✅ **Reconstruct incident timelines from fragmented evidence**  
✅ **Apply OSINT techniques to chat communications**

---

## Pedagogical Design Principles

### **1. Realistic Scenario**
- Insider threat is a common real-world scenario
- Evidence is fragmented and requires correlation
- Anti-forensics attempts are present but imperfect
- No "smoking gun" - requires building a case

### **2. Progressive Difficulty**
- Early challenges build confidence (50-75 points)
- Middle challenges introduce new techniques (100 points)
- Final challenge integrates all skills (200 points)

### **3. Multiple Solution Paths**
- Players can tackle challenges in different orders
- Some hints are available at cost (pedagogical scaffolding)
- Artifacts validate each other (multiple confirmation routes)

### **4. Authentic Tool Usage**
- Real forensic tools (exiftool, steghide, Wireshark concepts)
- Real file formats (PCAP, Git repos, Telegram JSON)
- Real OSINT targets (ProtonMail, paste.sh are actual services)

### **5. Failure Tolerance**
- Red herrings teach discrimination skills
- Large datasets teach filtering techniques
- Multiple challenges allow partial credit
- Hints prevent complete blocking

---

## Assessment Rubric for Educators

If using Case 001 in an educational context:

| Skill Category | Weight | Assessment Method |
|----------------|--------|-------------------|
| Technical Proficiency | 40% | Challenge completion, tool usage |
| Analytical Thinking | 25% | Solution path efficiency, hint usage |
| Attention to Detail | 15% | Finding subtle clues, avoiding red herrings |
| Documentation | 10% | Written explanations (if required) |
| Time Management | 10% | Completion speed, prioritization |

---

## Differentiation Strategies

### **For Beginners**:
- Emphasize the hints system
- Provide supplementary "how to use exiftool/steghide" guides
- Allow collaboration or team-based completion
- Focus on learning objectives over time completion

### **For Advanced Players**:
- Disable hints for maximum points
- Add time pressure (timed competition mode)
- Require written forensic reports with evidence citations
- Compare solution paths for efficiency

### **For Mixed Groups**:
- Team roles: one person handles network, another handles Git, etc.
- Peer teaching: experienced players explain techniques
- Progressive disclosure: unlock harder challenges only after easier ones

---

## Common Failure Modes & Interventions

### **Failure Mode 1: Overwhelmed by Volume**
- **Symptom**: Player gives up after seeing 312 images or 850 messages
- **Intervention**: Hint system nudges toward specific artifacts
- **Lesson**: Real forensics involves filtering large datasets

### **Failure Mode 2: Tool Unfamiliarity**
- **Symptom**: Player stuck on Challenge 3 (steganography)
- **Intervention**: Hint mentions "steghide" by name
- **Lesson**: Investigators must research and learn tools on-the-fly

### **Failure Mode 3: Missing Correlation**
- **Symptom**: Player finds encoded email but doesn't recognize it as final answer
- **Intervention**: Challenge description emphasizes "external email address"
- **Lesson**: Evidence must be interpreted in context of investigation goals

### **Failure Mode 4: Chasing Red Herrings**
- **Symptom**: Player spends excessive time on fork repositories or fake API keys
- **Intervention**: Time-based hints unlock after 30 minutes on wrong path
- **Lesson**: Discrimination skills separate experienced from novice investigators

---

## Metrics for Success

Case 001 is considered successful if:

- **Completion Rate**: 60-75% of intermediate-level players complete at least 3/5 challenges
- **Time Distribution**: Median completion time is 90-120 minutes
- **Hint Usage**: Average 2-3 hints per player (indicates good difficulty calibration)
- **First Blood**: First completion within 45-60 minutes (indicates solvability)
- **Satisfaction**: Post-case survey shows 80%+ found it "challenging but fair"

---

## Extensibility

This case design can be extended with:

- **Hard Mode**: Remove the manifest.json hint files, require actual image analysis
- **Expert Mode**: Generate real PCAP with noise, require actual Wireshark filtering
- **Team Mode**: Different team members get different artifacts, must collaborate
- **Time Attack**: Speed-running competitions with pre-learned techniques
- **Write-Up Requirement**: Full forensic report with evidence chain documentation

---

*This document is for internal use only. Player-facing documentation should maintain the investigative mystery without revealing the underlying pedagogical structure.*
