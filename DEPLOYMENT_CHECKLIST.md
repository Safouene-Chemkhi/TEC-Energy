# Quick Start Checklist for Terraform Deployment

## ✅ Pre-Deployment Checklist

- [ ] Terraform installed (`terraform --version`)
- [ ] AWS CLI installed and configured (`aws configure`)
- [ ] Docker installed and running
- [ ] GitHub account set up (if using CI/CD)
- [ ] AWS account with appropriate permissions

## ✅ Step 1: Prepare Docker Image

- [ ] Build Docker image: `docker build -t tec-energy:latest .`
- [ ] Create ECR repository: `aws ecr create-repository --repository-name tec-energy`
- [ ] Push image to ECR (follow steps in README.md)
- [ ] Note your ECR image URI: `<account-id>.dkr.ecr.us-east-1.amazonaws.com/tec-energy:latest`

## ✅ Step 2: Configure Terraform

- [ ] Copy `terraform.tfvars.example` to `terraform.tfvars`
- [ ] Update `container_image` with your ECR URI
- [ ] Set `db_password` to a strong password (min 8 chars)
- [ ] Review other variables (region, instance types, etc.)
- [ ] Verify `terraform.tfvars` is in `.gitignore`

## ✅ Step 3: Deploy Infrastructure

```bash
# Navigate to terraform directory
cd terraform

# Initialize Terraform
terraform init

# Review planned changes
terraform plan -out=tfplan

# Apply changes
terraform apply tfplan
```

## ✅ Step 4: Verify Deployment

- [ ] Check ECS service is running:
  ```bash
  aws ecs describe-services \
    --cluster tec-energy-cluster \
    --services tec-energy-service \
    --query 'services[0].status'
  ```

- [ ] Get application URL:
  ```bash
  terraform output application_url
  ```

- [ ] Test the application:
  ```bash
  curl <APPLICATION_URL>/health
  ```

- [ ] Check logs:
  ```bash
  aws logs tail /ecs/tec-energy --follow
  ```

## ✅ Step 5: Setup CI/CD (Optional but Recommended)

If using GitHub:

- [ ] Create GitHub repository secrets:
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
  - `AWS_ACCOUNT_ID`
  - `DB_PASSWORD`

- [ ] Push `.github/workflows/deploy.yml` to main branch
- [ ] GitHub Actions will automatically build and deploy

## 📊 Post-Deployment

### Useful Commands

```bash
# View all outputs
terraform output

# View specific output
terraform output application_url

# View ECS service status
aws ecs describe-services \
  --cluster tec-energy-cluster \
  --services tec-energy-service

# View recent logs
aws logs tail /ecs/tec-energy --follow

# Scale application
# Edit terraform.tfvars: desired_count = 4
terraform apply

# Destroy all resources (if needed)
terraform destroy
```

### Monitoring Resources

- **Application**: Visit the ALB URL from `terraform output application_url`
- **Logs**: CloudWatch > Log Groups > `/ecs/tec-energy`
- **ECS**: AWS Console > ECS > Clusters > tec-energy-cluster
- **RDS**: AWS Console > RDS > Databases > tec-energy-db
- **Load Balancer**: AWS Console > EC2 > Load Balancers > tec-energy-alb

## 🔒 Security Reminders

- [ ] Never commit `terraform.tfvars` to version control
- [ ] Rotate database password periodically
- [ ] Use strong passwords (uppercase, lowercase, numbers, symbols)
- [ ] Review security groups in AWS Console
- [ ] Enable MFA on AWS account
- [ ] Use IAM roles for programmatic access
- [ ] Enable encryption for RDS and S3

## 🆘 Troubleshooting

### Issue: Tasks not starting

```bash
# Check logs
aws logs tail /ecs/tec-energy --follow

# Common causes:
# - Invalid Docker image URI
# - Insufficient task memory/CPU
# - Database connectivity issues
```

### Issue: ALB health check failing

```bash
# Verify health endpoint exists in your app
curl <ALB_URL>/health

# Check security group rules
aws ec2 describe-security-groups --filters Name=tag:Name,Values=tec-energy-*
```

### Issue: Database connection error

```bash
# Verify RDS is running
aws rds describe-db-instances --db-instance-identifier tec-energy-db

# Check security group allows port 5432
aws ec2 describe-security-groups --filters Name=group-name,Values=tec-energy-rds-sg
```

## 📚 Next Steps

1. **Set up monitoring**: Configure CloudWatch alarms for CPU/memory
2. **Enable SSL/TLS**: Add ACM certificate to ALB
3. **Setup backups**: Configure automated RDS backups
4. **Configure alerts**: Set up SNS for important events
5. **Implement CI/CD**: Use GitHub Actions for automated deployments
6. **Setup logging**: Configure application-level logging to CloudWatch

---

**For detailed information**, see `terraform/README.md`
