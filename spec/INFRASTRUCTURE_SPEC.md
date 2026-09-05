# Infrastructure Specification

> **Status:** Production (AWS)  
> **Last Updated:** April 2026

---

## Overview

Prodway runs on AWS (us-east-1) with a cost-optimized ECS Fargate architecture. Two services — SowFlow and FormPilot API — share a single ALB with path-based routing. File storage uses EFS, secrets live in AWS Secrets Manager, and CI/CD deploys via GitHub OIDC (zero stored credentials).

## Architecture

```
                    ┌─────────────────────────┐
                    │     Cloudflare DNS       │
                    │   prodway.ai (Pages)     │
                    │   api.prodway.ai (CNAME) │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   Application Load      │
                    │   Balancer (ALB)         │
                    │   HTTP :80               │
                    └──────┬──────────┬───────┘
                           │          │
              Default rule │          │ /formpilot/*
                           │          │
              ┌────────────▼──┐  ┌────▼────────────┐
              │   SowFlow     │  │  FormPilot API   │
              │   (Fargate    │  │  (Fargate Spot)  │
              │    Spot)      │  │  0.25 vCPU/512MB │
              │   0.25 vCPU   │  └──────────────────┘
              │   512 MB      │
              │   EFS mount   │
              └───────────────┘
```

## AWS Resources

### Networking
| Resource | ID | Details |
|----------|----|---------|
| VPC | `vpc-0b229b1890153b13e` | 10.0.0.0/16, DNS enabled |
| Subnet 1 (us-east-1a) | `subnet-0c23a5bf3f26425d5` | 10.0.1.0/24, public |
| Subnet 2 (us-east-1b) | `subnet-0db8f532f0b4a4935` | 10.0.2.0/24, public |
| Internet Gateway | `igw-09628dc0dcd81ac9a` | Attached to VPC |
| Route Table | `rtb-0055575a328d85e13` | 0.0.0.0/0 → IGW |

### Security Groups
| Name | ID | Inbound Rules |
|------|----|---------------|
| `prodway-alb-sg` | `sg-0862c9e1e32e5298b` | 80, 443 from 0.0.0.0/0 |
| `prodway-ecs-sg` | `sg-07796bca04b6016ba` | 3000 from ALB SG |
| `prodway-efs-sg` | `sg-0dd186bdaec477edc` | 2049 from ECS SG |

### Compute (ECS)
| Resource | Details |
|----------|---------|
| Cluster | `prodway` |
| Capacity Providers | FARGATE_SPOT (weight 4), FARGATE (weight 1) |
| SowFlow Service | Task def `sowflow:2`, 1 task, Fargate Spot |
| FormPilot Service | Task def `formpilot:1`, 1 task, Fargate Spot |

### Storage
| Resource | ID | Details |
|----------|----|---------|
| EFS | `fs-0e9f2893c1c394f48` | General purpose, bursting throughput |
| EFS Access Point | `fsap-0aefd5e0bffc768c1` | UID/GID 1000, path `/prodway-data` |

### Container Registry
| Repository | URI |
|------------|-----|
| SowFlow | `272795262341.dkr.ecr.us-east-1.amazonaws.com/prodway/sowflow` |
| FormPilot | `272795262341.dkr.ecr.us-east-1.amazonaws.com/prodway/formpilot` |

### Load Balancer
| Resource | Details |
|----------|---------|
| ALB | `prodway-alb-1094679811.us-east-1.elb.amazonaws.com` |
| Listener | HTTP :80, default → SowFlow TG |
| Rule Priority 10 | `/formpilot/*` → FormPilot TG |
| SowFlow TG | IP target, port 3000, health `/health` |
| FormPilot TG | IP target, port 3000, health `/formpilot/health` |

### Secrets
| Secret | Keys |
|--------|------|
| `prodway/sowflow/production` | ANTHROPIC_API_KEY, GOOGLE_API_KEY, SLACK_CLIENT_ID, SLACK_CLIENT_SECRET, SLACK_SIGNING_SECRET, STRIPE_SECRET_KEY, STRIPE_CLIENT_ID, STRIPE_WEBHOOK_SECRET, STRIPE_PRICE_BASE_ID, STRIPE_PRICE_USAGE_ID, DOCUSIGN_INTEGRATION_KEY, DOCUSIGN_SECRET_KEY, ENCRYPTION_KEY, SENDGRID_API_KEY |

### IAM
| Role | Purpose |
|------|---------|
| `prodway-ecs-task-execution` | ECR pull, CloudWatch Logs, Secrets Manager read |
| `prodway-ecs-task` | EFS mount access |
| `github-actions-prodway` | CI/CD: ECR push, ECS deploy, IAM pass role |

## CI/CD Pipeline

```
Push to main
    → Test (pytest)
    → Build & Deploy to AWS
        → OIDC assume role (github-actions-prodway)
        → ECR login
        → Build + push SowFlow image (linux/amd64)
        → Build + push FormPilot image (linux/amd64)
        → ECS update-service --force-new-deployment (both)
        → Wait for services-stable
    → Deploy Landing Page (Cloudflare Pages)
```

**Security:** GitHub OIDC federation — no AWS keys stored in GitHub. IAM role scoped to `dalefrieswthat/prodway.ai` repo only.

## Estimated Monthly Cost

| Resource | Cost |
|----------|------|
| ECS Fargate Spot (2 services) | ~$5–8 |
| ALB | ~$16–18 |
| EFS | ~$0.30 |
| ECR | ~$1 |
| Secrets Manager (14 keys) | ~$5.60 |
| CloudWatch (free tier) | $0 |
| **Total** | **~$28–33/mo** |

## Monitoring

- **CloudWatch Log Groups:** `/ecs/prodway/sowflow`, `/ecs/prodway/formpilot`
- **ALB Metrics:** RequestCount, TargetResponseTime, HTTPCode_Target_5XX
- **ECS Metrics:** CPUUtilization, MemoryUtilization per service
- **Health Checks:** ALB → `/health` (SowFlow), `/formpilot/health` (FormPilot)
