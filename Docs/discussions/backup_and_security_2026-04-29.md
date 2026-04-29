# Backup & Security — First Principles Analysis

**Date:** 2026-04-29  
**Context:** Travel Agency Agent — solo dev, PII data (passports, visas)  
**Approach:** Independent analysis — minimum viable backup, no enterprise overkill  

---

## 1. The Core Truth: You're One Laptop Crash Away from Disaster**

### Your Reality (Solo Dev)

| Risk | Impact | Probability |
|------|--------|-------------|
| **Laptop crashes** | Lose ALL enquiries, bookings, PII | HIGH (5+ years old) |
| **PostgreSQL corrupts** | Lose database, can't recover | MEDIUM (SSD fails) |
| **Encryption keys lost** | ALL PII unreadable (worse than lost!) | HIGH (if you lose `.env`) |
| **WhatsApp chat deleted** | Lose comms history | MEDIUM (account banned) |
| **Ransomware** | Lose everything, pay to recover | LOW (Mac, not Windows) |

**My insight:**  
As solo dev, **YOU are the backup strategy**. Automate it or lose everything.  
One crash = 2 years of customer data gone = business over.

---

## 2. My Backup Strategy (3 Layers)**

### Layer 1: Database Backups (Automated, Daily)

```bash
#!/bin/bash
# /scripts/backup-db.sh (run by cron daily 2am)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/postgres"
DB_NAME="travel_agency"
S3_BUCKET="s3://my-agency-backups/db/"

# 1. pg_dump (compressed)
pg_dump $DB_NAME | gzip > "$BACKUP_DIR/db_$TIMESTAMP.sql.gz"

# 2. Upload to S3 (offsite)
aws s3 cp "$BACKUP_DIR/db_$TIMESTAMP.sql.gz" "$S3_BUCKET"

# 3. Keep last 7 local, last 30 remote
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +7 -delete
# S3 lifecycle policy: delete after 90 days
```

**My insight:**  
Backup to **S3** (offsite) — if your house burns, data survives.  
Compress with `gzip` — 100MB DB → 10MB backup.

---

### Layer 2: File Backups (Receipts, Invoices, Passport Scans)

```bash
#!/bin/bash
# /scripts/backup-files.sh (run by cron daily 3am)
S3_BUCKET="s3://my-agency-backups/files/"
LOCAL_DIR="/data/uploads"  # receipt PDFs, passport scans

# Sync to S3 (incremental)
aws s3 sync "$LOCAL_DIR" "$S3_BUCKET" --storage-class STANDARD_IA

# Verify (sample check)
aws s3 ls "$S3_BUCKET" | tail -1  # Should see today's upload
```

**My insight:**  
Use `s3 sync` (incremetal) — only uploads new files.  
`STANDARD_IA` storage class = 50% cheaper for backups.

---

### Layer 3: Encryption Keys Backup (CRITICAL)**

```bash
#!/bin/bash
# /scripts/backup-keys.sh (run manually after key rotation)
S3_BUCKET="s3://my-agency-backups/keys/"
KEYS_FILE="$HOME/.env.travel_agency"

# 1. Encrypt keys file with GPG (password from your brain)
gpg --symmetric --cipher-algo AES256 -o /tmp/keys.gpg "$KEYS_FILE"

# 2. Upload to S3 (encrypted at rest)
aws s3 cp /tmp/keys.gpg "$S3_BUCKET" --sse AES256

# 3. Verify you can decrypt (TEST!)
gpg -d "$S3_BUCKET/keys.gpg" > /tmp/test_decrypt
diff "$KEYS_FILE" /tmp/test_decrypt  # Should be identical
```

**My insight:**  
Lose encryption keys = **ALL PII unreadable**. Worse than losing data!  
GPG encrypt with password from your brain (not stored anywhere).

---

## 3. Disaster Recovery (How Fast Can You Restore?)**

### Recovery Time Objective (RTO) — Solo Dev Target: 1 Hour**

```bash
#!/bin/bash
# /scripts/restore-db.sh (run when disaster strikes)
TIMESTAMP=$1  # "20260429_020000"

# 1. Download from S3
aws s3 cp "s3://my-agency-backups/db/db_$TIMESTAMP.sql.gz" /tmp/

# 2. Drop + recreate DB
dropdb travel_agency
createdb travel_agency

# 3. Restore
gunzip -c /tmp/db_$TIMESTAMP.sql.gz | psql travel_agency

# 4. Verify (row counts)
psql travel_agency -c "SELECT COUNT(*) FROM enquiries;"
psql travel_agency -c "SELECT COUNT(*) FROM customers;"
```

**My insight:**  
Test restore **monthly** — backup you can't restore = useless.  
`gunzip -c` → restores without extracting (saves disk space).

---

### Recovery Point Objective (RPO) — Solo Dev Target: 24 Hours Max Loss**

| Backup Frequency | Max Loss | Use Case |
|------------------|----------|----------|
| **Daily 2am** | 24 hours | Normal operation |
| **After milestone** | 0 hours | After big booking day, manual backup |
| **Before deployment** | 0 hours | `pg_dump` before `git push` |

**My insight:**  
Set cron: `0 2 * * * /scripts/backup-db.sh` (daily 2am).  
BEFORE deployment: manually run backup (just in case).

---

## 4. Database Security (PostgreSQL Hardening)**

### What You Need (Minimum)**

```sql
-- 1. No default passwords
ALTER USER postgres WITH PASSWORD 'complex-random-32-chars';

-- 2. Only listen on localhost (no remote)
-- In postgresql.conf:
listen_addresses = 'localhost'  -- NOT '*'

-- 3. Firewall (if VPS)
-- UFW (Ubuntu):
ufw deny 5432  -- Block PostgreSQL port from internet

-- 4. SSL for connections (if remote)
-- In postgresql.conf:
ssl = on
ssl_cert_file = '/etc/ssl/certs/server.crt'
ssl_key_file = '/etc/ssl/private/server.key'
```

**My insight:**  
`listen_addresses = 'localhost'` — database NOT accessible from internet.  
If you need remote access → **SSH tunnel**, not open port.

---

## 5. Environment Secrets (Never in Code)**

### What Secrets You Have**

| Secret | Where Stored | Exposure Risk |
|--------|-------------|---------------|
| **DB password** | `.env` file | ❌ NEVER in code |
| **WhatsApp API key** | `.env` file | ❌ NEVER in git |
| **Encryption key** | `.env` (or environment variable) | ❌ NEVER in code |
| **AWS S3 keys** | `~/.aws/credentials` | ❌ NEVER in git |
| **Session secret** | `.env` file | ❌ NEVER in code |

```bash
# .gitignore (NEVER commit secrets)
.env
*.pem
*.key
aws/credentials
```

**My insight:**  
`.env` is in `.gitignore` — if not, your secrets are PUBLIC on GitHub.  
AWS keys in git = **someone will mine them in 5 minutes**.

---

## 6. WhatsApp Chat Backup (Google Drive)**

### Why This Matters (Comms History)**

WhatsApp Business → Settings → Chats → Chat Backup → **Backup to Google Drive**.

| Backup Frequency | Recommended |
|------------------|---------------|
| **Daily** | ✅ YES — auto-backup every night |
| **Include videos** | ❌ NO — wastes space, receipts are photos |
| **Google account** | Use dedicated agency Gmail (not personal) |

**My insight:**  
Use **agency Gmail** for WhatsApp backup (not personal).  
If you lose phone, WhatsApp restore = 5 minutes (all comms back).

---

## 7. Encryption at Rest (PostgreSQL pgcrypto)**

### What Needs Encryption (Recap)**

| Data | Encrypt? | How (Simple) |
|------|---------|--------------|
| **Passport numbers** | ✅ YES | `pgp_sym_encrypt()` |
| **Passport scan files** | ✅ YES | AES-256 file-level |
| **Visa documents** | ✅ YES | AES-256 file-level |
| **Medical conditions** | ✅ YES | `pgp_sym_encrypt()` |
| **Phone numbers** | 🟡 OPTIONAL | Hash if you want |
| **Email addresses** | ❌ NO | Not sensitive enough |

```sql
-- Store encryption key in environment (not DB!)
SET app.secret_key = current_setting('app.secret_key');

-- Encrypt before INSERT
INSERT INTO travellers (passport_encrypted) 
VALUES (pgp_sym_encrypt('A1234567', current_setting('app.secret_key')));

-- Decrypt when needed (agent views)
SELECT pgp_sym_decrypt(passport_encrypted, current_setting('app.secret_key'))
FROM travellers;
```

**My insight:**  
`app.secret_key` → environment variable, NOT in database.  
If DB is stolen but keys are safe → data is unreadable.

---

## 8. Current State vs Backup & Security Model**

| Concept | Current State | My Lean Model |
|---------|---------------|-------------------|
| DB backups | None | Daily `pg_dump` → S3 (offsite) |
| File backups | None | `s3 sync` (incremental) for uploads |
| Encryption keys backup | None | GPG-encrypted → S3 (password from brain) |
| Disaster recovery | None | RTO = 1 hour, RPO = 24 hours |
| DB hardening | Default (open) | `listen_addresses = localhost` |
| Secrets management | None | `.env` + `.gitignore` |
| WhatsApp backup | None | Google Drive daily (agency Gmail) |

---

## 9. Decisions Needed (Solo Dev Reality)**

| Decision | Options | My Recommendation |
|-----------|---------|-------------------|
| Backup frequency? | Daily / Weekly / Manual | **Daily** — automate via cron |
| Offsite backup? | S3 / Dropbox / None | **S3** — cheap, reliable |
| Encryption keys backup? | S3 / GPG / None | **GPg** — password from brain |
| Test restore? | Monthly / Never / Before deploy | **Monthly** + before deploy |
| WhatsApp backup? | Google Drive / None | **Google Drive** daily |
| DB accessible remotely? | Yes / No | **NO** — localhost only, use SSH tunnel |

---

## 10. Next Discussion: Integrations**

Now that we know **HOW to protect data**, we need to discuss: **WHAT else needs to connect?**

Key questions for next discussion:
1. **WhatsApp Business API** — already discussed in Mobile, but DETAILS? (webhooks, QR code)
2. **Google Calendar** — sync enquiry deadlines, travel dates?
3. **CRM imports** — import past customers from Excel/CSV?
4. **Zoho/QuickBooks** — sync invoices for accounting?
5. **Payment gateway** — we said SKIP collection, but webhook for reconciliation?
6. **Solo dev reality** — what integrations are MUST vs nice-to-have?

---

**Next file:** `Docs/discussions/integrations_2026-04-29.md`
