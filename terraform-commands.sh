#!/usr/bin/env bash

# Makefile alternative for Windows PowerShell users
# Usage: ./terraform-commands.sh init|plan|apply|destroy

set -e

COMMAND=${1:-help}
ENVIRONMENT=${2:-dev}

case "$COMMAND" in
  init)
    echo "🔧 Initializing Terraform..."
    terraform -chdir=terraform init
    ;;
  
  plan)
    echo "📋 Planning infrastructure changes..."
    terraform -chdir=terraform plan -out=tfplan
    ;;
  
  apply)
    echo "🚀 Applying infrastructure changes..."
    if [ -f terraform/tfplan ]; then
      terraform -chdir=terraform apply tfplan
    else
      echo "⚠️  tfplan not found. Run './terraform-commands.sh plan' first."
      exit 1
    fi
    ;;
  
  destroy)
    echo "🗑️  Destroying infrastructure..."
    read -p "Are you sure? This will delete all AWS resources. (yes/no): " confirm
    if [ "$confirm" == "yes" ]; then
      terraform -chdir=terraform destroy
    else
      echo "Cancelled."
    fi
    ;;
  
  output)
    echo "📊 Terraform outputs:"
    terraform -chdir=terraform output
    ;;
  
  logs)
    echo "📝 Fetching application logs..."
    aws logs tail /ecs/tec-energy --follow --since 5m
    ;;
  
  validate)
    echo "✓ Validating Terraform configuration..."
    terraform -chdir=terraform fmt -check
    terraform -chdir=terraform validate
    ;;
  
  help)
    echo "Terraform Commands:"
    echo "  ./terraform-commands.sh init      - Initialize Terraform"
    echo "  ./terraform-commands.sh plan      - Plan changes"
    echo "  ./terraform-commands.sh apply     - Apply changes"
    echo "  ./terraform-commands.sh destroy   - Destroy infrastructure"
    echo "  ./terraform-commands.sh output    - Show outputs"
    echo "  ./terraform-commands.sh logs      - View application logs"
    echo "  ./terraform-commands.sh validate  - Validate configuration"
    ;;
  
  *)
    echo "Unknown command: $COMMAND"
    echo "Run './terraform-commands.sh help' for available commands."
    exit 1
    ;;
esac
