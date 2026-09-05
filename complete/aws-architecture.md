# Prodway AI AWS Architecture

**Region:** us-east-1

## Services

Two FastAPI services running on ECS Fargate behind a shared ALB.

**SowFlow** handles Slack bot commands, SOW generation, OAuth, Stripe billing, DocuSign e-signatures, and API key validation.

**FormPilot** handles AI powered form field mapping, profile import, and field suggestions for the Chrome extension.

## Networking

VPC (10.0.0.0/16) with two public subnets across us-east-1a and us-east-1b. Internet Gateway attached. Three security groups enforce traffic flow: ALB accepts HTTP/HTTPS from the internet, ECS tasks accept traffic only from the ALB, and EFS accepts NFS only from ECS tasks.

## Compute

ECS cluster running Fargate Spot with on demand Fargate as fallback. Each service runs at 0.25 vCPU and 512 MB memory on port 3000.

## Load Balancing

ALB with an HTTP listener and path based routing. Default traffic routes to SowFlow. Requests matching /formpilot/* route to FormPilot. Health checks run every 30 seconds on each target group.

## Storage

EFS file system with an access point configured for UID/GID 1000 to match the non root container user. Mount targets in both subnets. SowFlow mounts EFS at /app/data for JSON document storage (SOWs, team data, billing records, audit logs).

## Secrets

14 application secrets stored in AWS Secrets Manager under prodway/sowflow/production. Injected as environment variables at container launch through ECS task definition configuration. No secrets in code, env files, or CI/CD.

## Container Registry

Two ECR repositories (prodway/sowflow and prodway/formpilot). Images built for linux/amd64 and tagged with the git commit SHA and latest.

## IAM

Three roles with scoped permissions:
- Task execution role: pulls images from ECR, reads secrets, writes CloudWatch logs
- Task role: mounts EFS at runtime
- CI/CD role: pushes to ECR and updates ECS services, assumed via GitHub OIDC with no stored credentials

## Observability

CloudWatch log groups for both services. ALB metrics tracked (request count, response time, 5xx errors, healthy host count). ECS metrics tracked for CPU and memory utilization.

## CI/CD

On push to main, GitHub Actions runs 124 tests, then assumes an IAM role via OIDC, builds and pushes both images to ECR, updates both ECS services, and waits for stable deployments. Landing page deploys to Cloudflare Pages in parallel. No AWS access keys stored in GitHub.

## DNS

prodway.ai routes to Cloudflare Pages (landing page). api.prodway.ai is a CNAME pointing to the ALB, proxied through Cloudflare.

## Request Flow

All API traffic hits api.prodway.ai, goes through Cloudflare, then the ALB. SowFlow handles /health, /slack/*, /signup, /webhooks/*, and /api/*. FormPilot handles /formpilot/*. SowFlow reads and writes to EFS and calls Slack, Stripe, DocuSign, and AI APIs. FormPilot calls Google Gemini and validates subscriptions against SowFlow.
