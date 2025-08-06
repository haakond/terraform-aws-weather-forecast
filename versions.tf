# Weather Forecast App - Terraform Version Constraints

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    awscc = {
      source  = "hashicorp/awscc"
      version = "~> 0.70"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }
}