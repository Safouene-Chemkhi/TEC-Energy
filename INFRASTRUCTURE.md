# Infrastructure Deployment Guide for TEC Energy

## Overview

Your infrastructure is now configured with **Infrastructure-as-Code (IaC)** using Terraform. This ensures:

✅ **Repeatable deployments** - Run the same commands multiple times, same results  
✅ **Idempotent** - Resources are updated safely, not recreated  
✅ **Version controlled** - Track all infrastructure changes in git  
✅ **Scalable** - Easily add/remove resources  
✅ **Auditable** - See what changed and when  

## What's Included

```
terraform/
├── provider.tf              # AWS provider configuration
├── main.tf                  # Infrastructure resources (VPC, ECS, RDS, ALB, etc.)
├── variables.tf             # Input variables
├── outputs.tf               # Output values (URLs, endpoints, etc.)
├── backend.tf               # Remote state configuration (optional)
├── terraform.tfvars.example # Example variables (copy and customize)
├── .gitignore              # Git ignore rules
└── README.md               # Detailed Terraform documentation

.github/workflows/
└── deploy.yml              # GitHub Actions CI/CD pipeline (optional)

DEPLOYMENT_CHECKLIST.md     # Step-by-step deployment checklist
terraform-commands.sh       # Helper script for common Terraform commands
```

## Architecture

```
                    ┌─────────────────────┐
                    │   Internet Users    │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   Application      │
                    │   Load Balancer    │
                    │   (ALB)            │
                    └──────────┬──────────┘
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
    ┌───────▼────────┐  ┌──────▼──────┐  ┌──────▼──────┐
    │  ECS Task 1    │  │ ECS Task 2  │  │ ECS Task 3  │
    │  (FastAPI App) │  │ (FastAPI...)│  │ (FastAPI...)│
    └───────┬────────┘  └──────┬──────┘  └──────┬──────┘
            │                  │                  │
            └──────────────────┼──────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   RDS PostgreSQL   │
                    │   Database         │
                    └────────────────────┘
```

## Quick Start (Windows PowerShell)

### 1️⃣ Prerequisites

```powershell
# Check Terraform is installed
terraform -v

# Check AWS CLI
aws --version

# Configure AWS credentials
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and region (us-east-1)
```

### 2️⃣ Push Docker Image to ECR

```powershell
# Create ECR repository
aws ecr create-repository --repository-name tec-energy --region us-east-1

# Build Docker image
docker build -t tec-energy:latest .

# Get ECR login token and login
aws ecr get-login-password --region us-east-1 | `
  docker login --username AWS --password-stdin `
  <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

# Tag and push image
docker tag tec-energy:latest <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/tec-energy:latest
docker push <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/tec-energy:latest
```

### 3️⃣ Setup Terraform

```powershell
# Navigate to terraform directory
cd terraform

# Copy example variables file
Copy-Item terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars with your values
# - Set container_image to your ECR image URI
# - Set db_password to a secure password
notepad terraform.tfvars
```

### 4️⃣ Deploy Infrastructure

```powershell
# Initialize Terraform
terraform init

# Review planned changes
terraform plan -out=tfplan

# Apply the infrastructure
terraform apply tfplan
# This takes 10-15 minutes

# Get outputs
terraform output
```

### 5️⃣ Verify Deployment

```powershell
# Get the application URL
$AppUrl = terraform output -raw application_url

# Test the application
Invoke-WebRequest -Uri "$AppUrl/health"

# View logs
aws logs tail /ecs/tec-energy --follow

# Check ECS service status
aws ecs describe-services `
  --cluster tec-energy-cluster `
  --services tec-energy-service
```

## Common Operations

### Update Application (New Docker Image)

```powershell
# Build and push new image
docker build -t tec-energy:v2 .
docker tag tec-energy:v2 <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/tec-energy:v2
docker push <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/tec-energy:v2

# Update Terraform variable
notepad terraform/terraform.tfvars
# Change container_image to new URI

# Apply changes
cd terraform
terraform apply
# ECS automatically redeploys with new image
```

### Scale Application

```powershell
# Edit terraform.tfvars
notepad terraform/terraform.tfvars
# Change: desired_count = 4

# Apply
terraform apply

# Auto-scaling handles CPU/memory spikes automatically
# Min: 2 tasks
# Max: 4 tasks
# Target CPU: 70%
# Target Memory: 80%
```

### View Logs

```powershell
# Recent logs
aws logs tail /ecs/tec-energy --follow

# Last hour
aws logs tail /ecs/tec-energy --since 1h

# Specific time range
aws logs filter-log-events `
  --log-group-name /ecs/tec-energy `
  --start-time 1698000000000 `
  --end-time 1698003600000
```

### Destroy Infrastructure (if needed)

```powershell
cd terraform
terraform destroy

# Confirm by typing 'yes'
```

## Setup GitHub Actions (Optional but Recommended)

Automated CI/CD with GitHub:

### 1. Add GitHub Secrets

```
GitHub > Settings > Secrets and Variables > Actions
Add:
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- AWS_ACCOUNT_ID
- DB_PASSWORD
```

### 2. Push to GitHub

```powershell
git add .
git commit -m "Add Terraform infrastructure"
git push origin main
```

### 3. GitHub Actions Runs Automatically

- Tests code on every push
- Builds Docker image on `main` branch
- Pushes to ECR
- Runs Terraform plan
- Applies changes
- Posts results to PR

## Monitoring & Logs

### CloudWatch Logs (Application)

```powershell
# View in real-time
aws logs tail /ecs/tec-energy --follow

# Or in AWS Console:
# AWS > CloudWatch > Log Groups > /ecs/tec-energy
```

### ECS Dashboard

```powershell
# Service details
aws ecs describe-services `
  --cluster tec-energy-cluster `
  --services tec-energy-service `
  --query 'services[0].[status,desiredCount,runningCount]'

# Task details
aws ecs list-tasks --cluster tec-energy-cluster
aws ecs describe-tasks `
  --cluster tec-energy-cluster `
  --tasks <TASK_ARN>
```

### RDS Database

```powershell
# Connect locally (requires security group rule)
psql -h <RDS_ENDPOINT> -U dbadmin -d tec_energy_db

# Or in AWS Console:
# AWS > RDS > Databases > tec-energy-db
```

## Idempotent Deployments Explained

### What is Idempotency?

Running the same Terraform command multiple times produces the **same result** without errors or resource recreation.

### Example: Running `terraform apply` 3 Times

```powershell
# First run - Creates all resources
terraform apply

# Second run - No changes (all resources already exist)
terraform apply
# Output: "No changes. Infrastructure is up-to-date."

# Third run - Still no changes
terraform apply
# Output: "No changes. Infrastructure is up-to-date."
```

### Why This Matters

✅ **Safe to re-run** - Accidentally ran twice? No problem.  
✅ **Predictable** - Always get the same infrastructure  
✅ **Team-friendly** - Multiple people can run deployments safely  
✅ **DevOps best practice** - All infrastructure changes through code  

## Updating Infrastructure

All updates are done through Terraform code + `terraform apply`:

```powershell
# Edit terraform.tfvars
# Example: Change desired_count from 2 to 4
notepad terraform/terraform.tfvars

# Plan the changes
terraform plan

# Apply the changes
terraform apply

# Result: Terraform updates only the changed resources
```

**No manual AWS Console changes needed!** All infrastructure changes through Terraform.

## Security Best Practices

✅ **Never commit `terraform.tfvars`** - It contains sensitive data  
✅ **Use strong passwords** - Min 8 chars, mix of uppercase/lowercase/numbers/symbols  
✅ **Rotate credentials** - Regenerate DB password periodically  
✅ **Use IAM roles** - Already configured in Terraform  
✅ **Enable encryption** - RDS, S3, and state file encrypted  
✅ **Restrict security groups** - Only allow necessary access  
✅ **Use version control** - Track all changes in git  

## Troubleshooting

### Issue: `terraform init` fails

```powershell
# Remove cached modules
Remove-Item -Path .terraform -Recurse -Force

# Try again
terraform init
```

### Issue: Tasks not starting

```powershell
# Check logs
aws logs tail /ecs/tec-energy --follow --since 1m

# Verify ECR image exists
aws ecr list-images --repository-name tec-energy

# Check task definition
aws ecs describe-task-definition `
  --task-definition tec-energy `
  --query 'taskDefinition.containerDefinitions[0].image'
```

### Issue: ALB health checks failing

```powershell
# Test health endpoint directly
Invoke-WebRequest -Uri "http://<TASK_IP>:80/health"

# Check if /health endpoint exists in your FastAPI app
# In main.py, add:
# @app.get("/health")
# def health():
#     return {"status": "ok"}
```

### Issue: Database connection error

```powershell
# Verify RDS is running
aws rds describe-db-instances `
  --db-instance-identifier tec-energy-db `
  --query 'DBInstances[0].DBInstanceStatus'

# Check security group rules
aws ec2 describe-security-groups `
  --filters Name=group-name,Values=tec-energy-rds-sg
```

## Cost Optimization

For development, keep costs low:

```hcl
# In terraform.tfvars
container_cpu    = 256        # Lower = cheaper
container_memory = 512        # Lower = cheaper
desired_count    = 1          # Single instance
db_instance_class = "db.t3.micro"  # Free tier eligible
```

These settings are fine for development. Increase for production.

## Next Steps

1. ✅ Follow the "Quick Start" section above
2. ✅ Test your application with the ALB URL
3. ✅ Monitor logs with CloudWatch
4. ✅ Setup GitHub Actions for CI/CD (optional)
5. ✅ Configure monitoring alerts
6. ✅ Add HTTPS/SSL certificate
7. ✅ Setup automated backups for RDS

## Resources

- 📖 [Terraform AWS Provider Docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- 📖 [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- 📖 [AWS RDS Documentation](https://docs.aws.amazon.com/rds/)
- 📖 [Terraform Best Practices](https://www.terraform.io/docs/cloud/best-practices)
- 📄 `terraform/README.md` - Detailed Terraform documentation
- 📄 `DEPLOYMENT_CHECKLIST.md` - Step-by-step checklist

---

**Questions?** Check `terraform/README.md` for comprehensive documentation.
