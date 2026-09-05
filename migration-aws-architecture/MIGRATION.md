# Prodway AI — Railway to AWS Migration

> **Date:** April 8, 2026  
> **Author:** Dale Yarborough  
> **Status:** Complete

---

## Executive Summary

Migrated Prodway's production API from Railway to AWS ECS Fargate Spot, reducing estimated monthly cost from ~$48 to ~$28–33 while gaining persistent storage, proper secrets management, and zero-credential CI/CD.

---

## Before & After

```
BEFORE (Railway)                         AFTER (AWS)
─────────────────                        ──────────────────────────
┌──────────────┐                         ┌──────────────────────────┐
│   Railway     │                         │     AWS us-east-1         │
│               │                         │                           │
│  ┌──────────┐ │                         │  ┌─────┐   ┌───────────┐ │
│  │ SowFlow  │ │   ──────────────►       │  │ ALB │──►│ SowFlow   │ │
│  │ (single  │ │   (zero downtime)       │  │     │   │ (Fargate  │ │
│  │ service) │ │                         │  │     │   │  Spot)    │ │
│  └──────────┘ │                         │  │     │   └─────┬─────┘ │
│               │                         │  │     │         │ EFS   │
│  FormPilot:   │                         │  │     │   ┌─────▼─────┐ │
│  not deployed │                         │  │     │──►│ FormPilot │ │
│               │                         │  │     │   │ (Fargate  │ │
│  Secrets:     │                         │  │     │   │  Spot)    │ │
│  env vars     │                         │  └─────┘   └───────────┘ │
│  in Railway   │                         │                           │
│  dashboard    │                         │  Secrets Manager (14 keys)│
│               │                         │  ECR (2 repos)            │
└──────────────┘                         │  CloudWatch Logs           │
                                          └──────────────────────────┘
Cost: ~$48/mo                            Cost: ~$28–33/mo
```

---

## Architecture Diagram

```
                         ┌──────────────────────────────┐
                         │        Internet               │
                         └──────────────┬───────────────┘
                                        │
                         ┌──────────────▼───────────────┐
                         │  Cloudflare DNS               │
                         │  prodway.ai → Pages           │
                         │  api.prodway.ai → ALB CNAME   │
                         └──────────────┬───────────────┘
                                        │
                    ┌───────────────────────────────────────┐
                    │  VPC 10.0.0.0/16                      │
                    │  ┌────────────────────────────────┐   │
                    │  │  ALB (prodway-alb)              │   │
                    │  │  HTTP :80                       │   │
                    │  │  SG: 80, 443 from 0.0.0.0/0    │   │
                    │  └────────┬──────────┬────────────┘   │
                    │           │          │                 │
                    │   default │          │ /formpilot/*    │
                    │           │          │                 │
                    │  ┌────────▼────┐ ┌───▼────────────┐   │
                    │  │  Subnet 1a  │ │  Subnet 1b     │   │
                    │  │  10.0.1.0   │ │  10.0.2.0      │   │
                    │  └─────────────┘ └────────────────┘   │
                    │                                        │
                    │  ┌─────────────────────────────────┐   │
                    │  │  ECS Cluster: prodway            │   │
                    │  │  Capacity: FARGATE_SPOT (80%)    │   │
                    │  │            FARGATE (20%)         │   │
                    │  │                                  │   │
                    │  │  ┌────────────┐ ┌────────────┐  │   │
                    │  │  │  SowFlow   │ │ FormPilot  │  │   │
                    │  │  │  0.25 vCPU │ │ 0.25 vCPU  │  │   │
                    │  │  │  512 MB    │ │ 512 MB     │  │   │
                    │  │  │  Port 3000 │ │ Port 3000  │  │   │
                    │  │  │  EFS mount │ │            │  │   │
                    │  │  └──────┬─────┘ └────────────┘  │   │
                    │  └─────────┼────────────────────────┘   │
                    │            │                             │
                    │  ┌─────────▼─────────┐                  │
                    │  │  EFS (prodway-data)│                  │
                    │  │  Access Point      │                  │
                    │  │  UID/GID 1000      │                  │
                    │  │  /prodway-data     │                  │
                    │  └───────────────────┘                  │
                    └─────────────────────────────────────────┘

                    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
                    │  ECR         │  │  Secrets Mgr │  │  CloudWatch  │
                    │  sowflow     │  │  14 keys     │  │  /ecs/prodway│
                    │  formpilot   │  │  encrypted   │  │  /sowflow    │
                    └──────────────┘  └──────────────┘  │  /formpilot  │
                                                         └──────────────┘
```

---

## CI/CD Flow (GitHub OIDC → AWS)

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Push to main                                                            │
│                                                                          │
│  ┌──────────┐    ┌───────────────┐    ┌─────────────┐    ┌───────────┐  │
│  │  pytest   │───►│ OIDC Assume   │───►│ ECR Login   │───►│ Docker    │  │
│  │  tests/   │    │ Role          │    │             │    │ Build     │  │
│  └──────────┘    │ (no stored    │    └─────────────┘    │ (amd64)   │  │
│                   │  credentials) │                       └─────┬─────┘  │
│                   └───────────────┘                             │        │
│                                                                 │        │
│  ┌──────────────────────────────────────────────────────────────▼─────┐  │
│  │  Push to ECR                                                       │  │
│  │  prodway/sowflow:latest + :sha                                     │  │
│  │  prodway/formpilot:latest + :sha                                   │  │
│  └────────────────────────────────┬──────────────────────────────────┘  │
│                                    │                                     │
│  ┌─────────────────────────────────▼─────────────────────────────────┐  │
│  │  ECS update-service --force-new-deployment                         │  │
│  │  Wait for services-stable                                          │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────────┐  (parallel)                                        │
│  │ Cloudflare Pages │  Landing page deploy                               │
│  └──────────────────┘                                                    │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Migration Process (Step by Step)

### Phase 1: Foundation
| Step | What | Result |
|------|------|--------|
| 1 | Created VPC (10.0.0.0/16) with DNS support | `vpc-0b229b1890153b13e` |
| 2 | Created 2 public subnets (us-east-1a, 1b) with auto-assign public IPs | Required for ALB multi-AZ |
| 3 | Created Internet Gateway + route 0.0.0.0/0 → IGW | Public internet access |
| 4 | Created 3 security groups (ALB, ECS, EFS) with least-privilege rules | Traffic flows: Internet → ALB → ECS → EFS |

### Phase 2: Storage & Registry
| Step | What | Result |
|------|------|--------|
| 5 | Created 2 ECR repositories (sowflow, formpilot) | Container image registry |
| 6 | Built Docker images (linux/amd64) and pushed to ECR | Both images < 500MB |
| 7 | Created EFS file system + mount targets in both subnets | Persistent JSON storage |
| 8 | Created EFS Access Point (UID 1000) | Matches Docker `app` user — fixed permission denied error |

### Phase 3: Compute
| Step | What | Result |
|------|------|--------|
| 9 | Created ALB with HTTP listener + path-based routing | Default → SowFlow, `/formpilot/*` → FormPilot |
| 10 | Created ECS cluster with Fargate Spot (80%) + Fargate (20%) | Cost-optimized compute |
| 11 | Created IAM roles: task-execution (ECR + Secrets Manager) + task (EFS) | Least-privilege access |
| 12 | Registered SowFlow task definition (14 secrets from Secrets Manager, EFS mount) | `sowflow:2` |
| 13 | Registered FormPilot task definition (2 secrets) | `formpilot:1` |
| 14 | Created ECS services, verified health via ALB | Both services RUNNING + steady state |

### Phase 4: CI/CD
| Step | What | Result |
|------|------|--------|
| 15 | Created GitHub OIDC identity provider in AWS | Trusts `token.actions.githubusercontent.com` |
| 16 | Created IAM role `github-actions-prodway` scoped to repo | Zero stored credentials in GitHub |
| 17 | Updated `.github/workflows/ci.yml`: Railway → AWS ECR/ECS | Build, push, deploy via OIDC |

### Phase 5: DNS Cutover
| Step | What | Result |
|------|------|--------|
| 18 | Update Cloudflare CNAME: `api.prodway.ai` → ALB DNS | Pending — requires Cloudflare dashboard |
| 19 | Verify all integrations (Slack, Stripe, DocuSign) | Post-cutover validation |
| 20 | Decommission Railway | After 48hr soak period |

---

## Decision Log

| Decision | Why | Alternative Considered |
|----------|-----|----------------------|
| **Fargate Spot over regular Fargate** | 70% cost reduction, acceptable for startup traffic | Regular Fargate (~$15–25/mo more) |
| **Single public subnet (no NAT Gateway)** | Saves $32/mo; services don't need private networking yet | Private subnets + NAT (~$32/mo) |
| **EFS over RDS** | Keep file-based JSON storage; no database needed yet | RDS db.t4g.micro (~$15–25/mo) |
| **Shared ALB with path-based routing** | One ALB serves both services | Two ALBs (~$16/mo wasted) |
| **GitHub OIDC over stored AWS keys** | Zero credentials to rotate or leak | IAM user access keys in GitHub Secrets |
| **Skip API Gateway** | ALB handles routing directly | API Gateway (~$3.50/mo minimum) |
| **EFS Access Point with UID 1000** | Match Docker non-root user; solved permission errors | Run container as root (security risk) |

---

## Verification Tests

### Health Check Verification (post-deployment)

```bash
# SowFlow — via ALB
$ curl http://prodway-alb-1094679811.us-east-1.elb.amazonaws.com/health
{"status":"ok","timestamp":"2026-04-08T04:23:37.927738"}

# FormPilot — via ALB path-based routing
$ curl http://prodway-alb-1094679811.us-east-1.elb.amazonaws.com/formpilot/health
{"status":"ok","service":"formpilot-api"}

# SowFlow version endpoint
$ curl http://prodway-alb-1094679811.us-east-1.elb.amazonaws.com/version
{"v":"4"}
```

### ECS Service Status

```bash
$ aws ecs describe-services --cluster prodway --services sowflow formpilot
sowflow:   running=1, desired=1, status="has reached a steady state"
formpilot: running=1, desired=1, status="has reached a steady state"
```

### Automated Test Suite (124 tests)

```
tests/sowflow/test_storage.py       — 13 tests  (SOW CRUD, team data, edits, outcomes)
tests/sowflow/test_billing.py       — 18 tests  (subscriptions, paywall, API keys, usage)
tests/sowflow/test_security.py      —  6 tests  (encryption, audit logging)
tests/sowflow/test_generation.py    —  8 tests  (AI generation, Slack formatting, HTML)
tests/sowflow/test_endpoints.py     —  7 tests  (health, contact, key validation, signup)
tests/formpilot/test_validation.py  — 29 tests  (URL/email/phone validators, semantic guards)
tests/formpilot/test_endpoints.py   — 24 tests  (auth, mappings, field suggest, stats)
tests/formpilot/test_prompt.py      — 19 tests  (prompt building, HTML strip, AI provider)
─────────────────────────────────────────────────
Total                                 124 tests   ALL PASSING
```

### Issue Encountered & Resolved

| Issue | Cause | Fix |
|-------|-------|-----|
| SowFlow container exiting with `PermissionError: /app/data/installations` | EFS root mount owned by root; Docker user is UID 1000 | Created EFS Access Point with `OwnerUid=1000, OwnerGid=1000`, updated task definition to use access point with IAM auth |

---

## Cost Comparison

```
                Railway          AWS (current)
                ────────         ─────────────
Compute         ~$48/mo          ~$5–8   (Fargate Spot)
Load Balancer   included         ~$16–18 (ALB)
Storage         ephemeral        ~$0.30  (EFS)
Registry        GHCR (free)      ~$1     (ECR)
Secrets         env vars         ~$5.60  (Secrets Manager)
Monitoring      basic            free tier (CloudWatch)
                ────────         ─────────────
TOTAL           ~$48/mo          ~$28–33/mo
SAVINGS                          ~$15–20/mo (31–42%)
```

**Additional gains:** Persistent storage (EFS), proper secrets management, multi-AZ networking, zero-credential CI/CD, and both services deployed (FormPilot was not deployed on Railway).

---

## Resource Inventory

| Resource | ID |
|----------|----|
| VPC | `vpc-0b229b1890153b13e` |
| Subnet 1a | `subnet-0c23a5bf3f26425d5` |
| Subnet 1b | `subnet-0db8f532f0b4a4935` |
| Internet Gateway | `igw-09628dc0dcd81ac9a` |
| ALB SG | `sg-0862c9e1e32e5298b` |
| ECS SG | `sg-07796bca04b6016ba` |
| EFS SG | `sg-0dd186bdaec477edc` |
| EFS | `fs-0e9f2893c1c394f48` |
| EFS Access Point | `fsap-0aefd5e0bffc768c1` |
| ECS Cluster | `prodway` |
| ALB | `prodway-alb-1094679811.us-east-1.elb.amazonaws.com` |
| ECR SowFlow | `272795262341.dkr.ecr.us-east-1.amazonaws.com/prodway/sowflow` |
| ECR FormPilot | `272795262341.dkr.ecr.us-east-1.amazonaws.com/prodway/formpilot` |
| Secrets | `prodway/sowflow/production` (14 keys) |
| OIDC Provider | `arn:aws:iam::272795262341:oidc-provider/token.actions.githubusercontent.com` |
| CI/CD Role | `arn:aws:iam::272795262341:role/github-actions-prodway` |
