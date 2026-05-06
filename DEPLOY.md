# HealthMeter — Deployment guide

Three GitHub Actions workflows, all `workflow_dispatch` (manual trigger):

| # | Workflow | Purpose |
|---|----------|---------|
| 1 | **Infrastructure Setup** (`infra.yml`) | `terraform apply` → DuckDNS update → Ansible installs Docker + Nginx + Certbot/HTTPS |
| 2 | **Deploy Application** (`deploy.yml`) | Build & push Docker image → rsync code to EC2 → regenerate `.env` from secrets → `docker-compose up -d` → migrate + collectstatic → install reminder cron |
| 3 | **Infrastructure Destroy** (`infra-destroy.yml`) | `pg_dump` + `tar media` → upload to S3 → `terraform destroy` |

---

## One-time setup (do this **once**, before the first `infra.yml` run)

### 1. AWS prerequisites

```bash
# From your local machine, AWS creds in env / ~/.aws/credentials
./scripts/bootstrap-aws.sh
```

This creates:
- S3 bucket `healthmeter-terraform-state` (versioned, encrypted, private) — holds Terraform state
- DynamoDB table `terraform-locks` — Terraform state lock

### 2. EC2 key pair

The Terraform config references a key pair called `aws-key-pair-30/2025` (defined in `infra/variables.tf`). Either:

- Use an existing key pair (and put its **private key** in the `EC2_SSH_KEY` GitHub secret), or
- Create a new one (`aws ec2 create-key-pair --key-name healthmeter-key`) and update `infra/variables.tf::key_name` to match.

### 3. DuckDNS

Sign up at https://www.duckdns.org and create a subdomain called `healthmeter`. Copy the token — it goes into `DUCKDNS_TOKEN` secret. The first `infra.yml` run will point `healthmeter.duckdns.org` at the EC2 public IP.

### 4. GitHub repository — set up environment + secrets

In the repo settings:

1. **Settings → Environments → New environment** → name it **`dev`**.
2. Add the following secrets to the `dev` environment:

#### Infra secrets
| Secret | Description |
|---|---|
| `AWS_ACCESS_KEY_ID` | AWS user with EC2 + S3 + VPC + DynamoDB perms |
| `AWS_SECRET_ACCESS_KEY` | matching secret |
| `EC2_SSH_KEY` | full text of the **private** key matching the EC2 key pair (PEM, with newlines preserved) |
| `EC2_USER` | `ubuntu` |
| `DUCKDNS_TOKEN` | token from https://www.duckdns.org |

#### Docker Hub
| Secret | Description |
|---|---|
| `DOCKERHUB_USERNAME` | your Docker Hub user |
| `DOCKERHUB_TOKEN` | a Docker Hub access token (not your password) |

#### App secrets
| Secret | Description |
|---|---|
| `DJANGO_SECRET_KEY` | random long string (`python -c 'import secrets;print(secrets.token_urlsafe(64))'`) |
| `POSTGRES_USER` | e.g. `healthmeter` |
| `POSTGRES_PASSWORD` | strong password |
| `POSTGRES_DB` | e.g. `healthmeter` |
| `EMAIL_HOST_USER` | Gmail address |
| `EMAIL_HOST_PASSWORD` | Gmail **app password** (not account password) |
| `DAILY_API_KEY` | from daily.co |
| `DEEPGRAM_API_KEY` | from deepgram |
| `GROQ_API_KEY` | from groq |
| `GROQ_MODEL` | e.g. `openai/gpt-oss-120b` |
| `REMINDER_CRON_TOKEN` | random long string — protects `/api/trigger-reminders/` |

> Razorpay secrets are intentionally not set: `RAZORPAY_ENABLED=False` is hard-wired in `deploy.yml`.

---

## First-time run order

1. **Infrastructure Setup** workflow → wait until it reports `https://healthmeter.duckdns.org` is ready (~5 min).
2. **Deploy Application** workflow → builds image, ships code, runs migrations.
3. Visit `https://healthmeter.duckdns.org`. Site should serve over HTTPS, chat WebSocket should connect, video call should work.

## Re-deploys

Just run **Deploy Application** again. It rebuilds the Docker image, regenerates `.env` from current secret values, and rolls the container.

## Tearing it all down

Run **Infrastructure Destroy**. Before destroying:
- `pg_dump` of the database is uploaded to `s3://healthmeter-db-backups/db/<timestamp>.sql` and `db/latest.sql`
- `media/` directory tarball uploaded to `s3://healthmeter-db-backups/media/<timestamp>.tar.gz`

The S3 backup bucket itself is also destroyed by Terraform — see the workflow for the version-emptying logic.

---

## Local development (optional)

```bash
cp .env.example .env   # fill in values for local dev
docker-compose up --build
# visit http://localhost:8000
```

The Django server runs in `DEBUG=True` mode locally because of `.env`. Postgres data persists in the `postgres_data` named volume.

---

## Architecture diagram

```
                ┌──────────────────────────────────────────┐
                │ GitHub Actions runners (workflows)       │
                └───────────────┬──────────────────────────┘
       (1) infra.yml           (2) deploy.yml         (3) infra-destroy.yml
       Terraform + Ansible     Docker push + ssh       pg_dump + S3 + destroy
                               
        AWS                                                  Docker Hub
        ┌─────────────────────────────────────────┐          ┌──────────┐
        │ VPC / Subnet / IGW / SG (22, 80, 443)  │          │ image    │
        │ ┌───────────────────────────────────┐  │          └──────────┘
        │ │ EC2 t2.micro (Ubuntu 22.04)       │  │
        │ │  ├── nginx (host) :80/:443        │  │
        │ │  │   ├── /static + /media         │  │
        │ │  │   ├── /ws/  → daphne (upgrade) │  │
        │ │  │   └── /     → daphne          │  │
        │ │  └── docker-compose               │  │
        │ │      ├── healthmeter_web (daphne) │  │
        │ │      └── healthmeter_db (postgres)│  │
        │ └───────────────────────────────────┘  │
        │ S3: healthmeter-db-backups (versioned) │
        │ S3: healthmeter-terraform-state        │
        │ DynamoDB: terraform-locks              │
        └─────────────────────────────────────────┘
                       ▲
                       │
              healthmeter.duckdns.org (DuckDNS A record)
```
