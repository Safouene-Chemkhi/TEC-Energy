# Terraform Infrastructure Setup

This directory contains simplified Infrastructure-as-Code (IaC) for deploying the TEC Energy application to AWS using Terraform. The configuration focuses on **deployment and monitoring**.

## Architecture

- **Compute**: ECS Fargate (with optional Container Insights)
- **Networking**: VPC with public/private subnets, NAT Gateway, ALB
- **Load Balancing**: Application Load Balancer with health checks
- **Monitoring**: CloudWatch logs, alarms, and dashboard
- **Logging**: 30-day retention CloudWatch log groups

## Prerequisites

1. **Terraform** >= 1.0
2. **AWS Account** with appropriate permissions
3. **AWS CLI** configured with credentials
4. **Docker Image** pushed to ECR (Elastic Container Registry)

## Quick Start

### 1. Configure AWS Credentials

```bash
aws configure
```

Or set environment variables:

```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

### 2. Push Docker Image to ECR

Create ECR repository:

```bash
aws ecr create-repository --repository-name tec-energy --region us-east-1
```

Build and push image:

```bash
# Build
docker build -t tec-energy:latest .

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

# Tag and push
docker tag tec-energy:latest \
  <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/tec-energy:latest
  
docker push <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/tec-energy:latest
```

### 3. Create Terraform Variables File

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:

```hcl
aws_region       = "us-east-1"
project_name     = "tec-energy"
environment      = "dev"
container_image  = "<ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/tec-energy:latest"
container_port   = 8000
container_cpu    = 512
container_memory = 1024
desired_count    = 2
enable_monitoring = true
```

**⚠️ Important**: Never commit `terraform.tfvars` to version control!

### 4. Deploy Infrastructure

```bash
# Initialize
terraform init

# Plan
terraform plan

# Apply
terraform apply
```

Deployment takes about 10-15 minutes.

### 5. Access Your Application

```bash
terraform output application_url
```

View CloudWatch dashboard:

```bash
terraform output cloudwatch_dashboard_url
```

## Configuration

### Key Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `container_image` | ECR image URI | Required |
| `container_port` | Container port | 8000 |
| `container_cpu` | CPU units | 512 |
| `container_memory` | Memory (MB) | 1024 |
| `desired_count` | Number of tasks | 2 |
| `enable_monitoring` | Enable CloudWatch monitoring | true |

### Supported CPU/Memory Combinations

- CPU 256: Memory 512, 1024, 2048
- CPU 512: Memory 1024, 2048, 3072, 4096
- CPU 1024: Memory 2048-8192 (increments of 1024)
- CPU 2048: Memory 4096-16384 (increments of 1024)
- CPU 4096: Memory 8192-30720 (increments of 1024)

## Monitoring

### CloudWatch Dashboard

Includes metrics for:
- ALB response times and request counts
- ECS CPU and memory utilization
- Application logs

### CloudWatch Alarms

Automatically created when `enable_monitoring = true`:

| Alarm | Threshold | Duration |
|-------|-----------|----------|
| ALB Response Time | > 1 second | 2 minutes |
| Unhealthy Hosts | >= 1 | 2 minutes |
| ECS CPU | > 80% | 10 minutes |
| ECS Memory | > 85% | 10 minutes |

## Deployment Workflow

### Update Application Image

1. Build and push new image to ECR:
   ```bash
   docker build -t tec-energy:v2 .
   docker tag tec-energy:v2 <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/tec-energy:v2
   docker push <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/tec-energy:v2
   ```

2. Update `terraform.tfvars`:
   ```hcl
   container_image = "<ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/tec-energy:v2"
   ```

3. Apply changes:
   ```bash
   terraform apply
   ```

ECS automatically redeploys with the new image (rolling update).

### Scale Tasks

Adjust `desired_count` in `terraform.tfvars`:

```hcl
desired_count = 4  # Run 4 tasks instead of 2
```

Then apply:

```bash
terraform apply
```

### Change Environment

Update `environment` in `terraform.tfvars`:

```hcl
environment = "prod"
```

This updates all resource tags and log groups.

## Managing Terraform State

### Local State (Development)

Default: stored in `terraform.tfstate` (local machine)

### Remote State (Recommended for Production)

Uncomment and configure in `backend.tf`:

```hcl
terraform {
  backend "s3" {
    bucket         = "your-terraform-state-bucket"
    key            = "tec-energy/dev/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

Then reinitialize:

```bash
terraform init
```

## Troubleshooting

### Application won't start

Check ECS task logs:

```bash
aws logs tail /ecs/tec-energy --follow
```

### ALB shows unhealthy targets

1. Verify health check endpoint: `/health`
2. Check task logs: `aws logs tail /ecs/tec-energy`
3. Verify container port matches `container_port` variable

### Out of memory or CPU limits

1. Increase `container_memory` or `container_cpu` in `terraform.tfvars`
2. Run `terraform apply`
3. ECS will redeploy tasks with new limits

## Cleanup

To destroy all AWS resources:

```bash
terraform destroy
```

**⚠️ Warning**: This permanently deletes all infrastructure, load balancer, and logs.

## File Structure

```
terraform/
├── main.tf           # Core resources (VPC, ECS, ALB, monitoring)
├── variables.tf      # Variable definitions
├── outputs.tf        # Output values
├── provider.tf       # AWS provider configuration
├── backend.tf        # Remote state configuration (optional)
├── terraform.tfvars.example  # Example variables file
└── README.md         # This file
```

## Best Practices

1. **Always plan before apply**: `terraform plan`
2. **Use version control**: Commit code, exclude `terraform.tfvars`
3. **Enable monitoring**: Set `enable_monitoring = true` in production
4. **Use remote state**: Enable backend.tf for team collaboration
5. **Regular backups**: CloudWatch logs retained for 30 days
6. **Tag resources**: Use meaningful project names and environment tags

## Support

For issues or questions about the Terraform configuration, check the AWS documentation:
- [AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [ECS Terraform Module](https://registry.terraform.io/modules/terraform-aws-modules/ecs/aws/latest)
- [CloudWatch Documentation](https://docs.aws.amazon.com/cloudwatch/)
```

Then apply:

```bash
terraform apply
```

### Auto-Scaling

Auto-scaling is already configured:
- **Min tasks**: 2 (or your `desired_count`)
- **Max tasks**: 4
- **CPU target**: 70%
- **Memory target**: 80%

Tasks automatically scale based on load.

## Monitoring

### CloudWatch Logs

View application logs:

```bash
aws logs tail /ecs/tec-energy --follow
```

Or in AWS Console:
1. Go to CloudWatch → Log Groups
2. Open `/ecs/tec-energy`
3. View recent log streams

### ECS Dashboard

Monitor service health:

```bash
aws ecs describe-services \
  --cluster tec-energy-cluster \
  --services tec-energy-service
```

## Database Access

### From Local Machine

```bash
psql -h <rds_address> -U dbadmin -d tec_energy_db
```

(Requires security group rules to allow your IP)

### From ECS Tasks

Tasks can access the database automatically via the `DATABASE_URL` environment variable.

## Updating Infrastructure

### Scaling Up Database

Update `db_instance_class` in `terraform.tfvars`:

```hcl
db_instance_class = "db.t3.small"
```

Then:

```bash
terraform apply
```

### Changing VPC CIDR

Edit `vpc_cidr` in `terraform.tfvars` (only for new deployments).

## Destroying Infrastructure

To tear down all resources:

```bash
terraform destroy
```

Review the destruction plan and confirm. All AWS resources will be deleted.

## Troubleshooting

### Task Won't Start

Check logs:

```bash
aws logs tail /ecs/tec-energy --follow
```

Common issues:
- Invalid Docker image URI
- Database connection string incorrect
- Insufficient task memory/CPU

### RDS Connection Errors

Verify security groups:

```bash
aws ec2 describe-security-groups \
  --filters Name=group-name,Values=tec-energy-rds-sg
```

Ensure ECS security group can access RDS security group on port 5432.

### ALB Health Checks Failing

Check container health check:
- Is the `/health` endpoint working?
- Is port 80 correct?

View task logs for errors.

## State Management

Terraform state is stored locally in `terraform.tfstate`. For production:

1. Use S3 backend:

   ```hcl
   # Add to provider.tf
   terraform {
     backend "s3" {
       bucket         = "your-terraform-state-bucket"
       key            = "tec-energy/terraform.tfstate"
       region         = "us-east-1"
       encrypt        = true
       dynamodb_table = "terraform-locks"
     }
   }
   ```

2. Create S3 bucket and DynamoDB table
3. Run `terraform init` to migrate state

## Cost Optimization

For development environments:
- Use `db.t3.micro` (included in free tier)
- Set `desired_count = 1`
- Use FARGATE_SPOT for non-critical tasks
- Set `skip_final_snapshot = true` when destroying

## Security Best Practices

1. **Never commit `terraform.tfvars`** to version control
2. **Use strong database passwords** (min 8 chars, mix of uppercase, lowercase, numbers, symbols)
3. **Restrict security groups** to necessary IPs only
4. **Enable encryption** for RDS and S3 state
5. **Use IAM roles** for ECS tasks (already configured)
6. **Enable MFA** for AWS account
7. **Use Terraform locks** with DynamoDB for team collaboration

## Additional Resources

- [Terraform AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS ECS with Fargate Guide](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-cpu-memory-error.html)
- [Terraform Best Practices](https://www.terraform.io/docs/cloud/best-practices)
