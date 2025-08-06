# Weather Forecast App - Terraform AWS Module

## TL;DR

A serverless weather forecast application deployed on AWS using Terraform. Displays tomorrow's weather for Oslo, Paris, London, and Barcelona with a responsive web interface.

**Quick Start:**
```bash
git clone <repository>
cd terraform-aws-weather-forecast
terraform init
terraform plan -var-file="environments/dev.tfvars"
terraform apply -var-file="environments/dev.tfvars"
```

## Executive Summary

The Weather Forecast App is a modern, serverless web application that provides tomorrow's weather forecast for four major European cities. Built with AWS serverless technologies and deployed using Terraform infrastructure-as-code, this solution offers:

**Value Proposition:**
- **Fast & Responsive**: Sub-second response times with global CDN distribution
- **Cost-Effective**: Serverless architecture with pay-per-use pricing model
- **Scalable**: Automatically handles traffic spikes without manual intervention
- **Reliable**: Multi-AZ deployment with 99.9% availability SLA
- **Secure**: AWS Well-Architected security best practices built-in

**Target Users:**
- End users seeking quick weather information for European travel planning
- Developers learning serverless architecture patterns
- Organizations needing a reference implementation for AWS serverless applications

## Architecture Overview

The application follows a serverless-first architecture pattern:

- **Frontend**: React SPA hosted on S3 with CloudFront CDN
- **Backend**: AWS Lambda functions with API Gateway
- **Database**: DynamoDB for weather data caching
- **External API**: Norwegian Meteorological Institute weather service
- **Monitoring**: CloudWatch dashboards and AWS Budget alerts

*Architecture diagrams will be generated and included here during implementation.*

## Features

### User Features
- ✅ Weather forecast for 4 European cities (Oslo, Paris, London, Barcelona)
- ✅ Mobile-responsive design optimized for all screen sizes
- ✅ Fast loading with sub-second response times
- ✅ Clean, modern user interface

### Technical Features
- ✅ Serverless architecture for minimal operational overhead
- ✅ Infrastructure-as-code with Terraform
- ✅ Automated testing (unit, integration, infrastructure)
- ✅ Cost monitoring and budget alerts
- ✅ Security best practices (CIS AWS Security Hub compliance)
- ✅ High availability with multi-AZ deployment

## Project Structure

```
.
├── main.tf                 # Main Terraform configuration
├── variables.tf            # Variable definitions
├── outputs.tf             # Output definitions
├── versions.tf            # Provider version constraints
├── modules/               # Terraform modules
│   ├── backend/          # Lambda, API Gateway, DynamoDB
│   ├── frontend/         # S3, CloudFront
│   └── monitoring/       # CloudWatch, AWS Budget
├── src/                  # Python application code
│   ├── weather_service/  # Weather service package
│   └── lambda_handler.py # Lambda function handler
├── frontend/             # React frontend application
│   ├── src/             # React components
│   └── public/          # Static assets
├── tests/               # Test suites
│   ├── unit/           # Unit tests
│   ├── integration/    # Integration tests
│   └── terraform/      # Terraform tests
├── docs/               # Documentation
├── examples/           # Usage examples
└── environments/       # Environment-specific configurations
```

## Prerequisites

- **Terraform** >= 1.0
- **AWS CLI** configured with appropriate credentials
- **Python** 3.13+ with pyenv
- **Node.js** (for frontend development)
- **Git** for version control

## Quick Start

### 1. Clone and Setup
```bash
git clone <repository-url>
cd terraform-aws-weather-forecast

# Set up Python virtual environment
pyenv virtualenv 3.13.3 weather-forecast-app
pyenv local weather-forecast-app
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### 2. Deploy Infrastructure
```bash
# Initialize Terraform
terraform init

# Plan deployment
terraform plan -var-file="environments/dev.tfvars"

# Deploy to AWS
terraform apply -var-file="environments/dev.tfvars"
```

### 3. Access Application
After deployment, Terraform will output the CloudFront distribution URL where you can access the application.

## Environment Configuration

### Development
```bash
terraform workspace select dev
terraform apply -var-file="environments/dev.tfvars"
```

### Production
```bash
terraform workspace select prod
terraform apply -var-file="environments/prod.tfvars"
```

## Testing

### Run All Tests
```bash
make test
```

### Individual Test Suites
```bash
# Python tests
make test-python

# Terraform tests
make test-tf

# Infrastructure validation
terraform validate
terraform plan
```

## Cost Analysis

*Detailed cost analysis will be generated using AWS Labs Pricing MCP server and included here during implementation.*

**Estimated Monthly Costs (Development Environment):**
- AWS Lambda: ~$2-5
- API Gateway: ~$1-3
- DynamoDB: ~$1-2
- CloudFront: ~$1-2
- S3: ~$0.50-1
- **Total: ~$5-13/month**

## Monitoring and Observability

- **CloudWatch Dashboard**: Custom dashboard with key metrics
- **AWS Budget**: Cost monitoring with Service tag filter
- **X-Ray Tracing**: Distributed tracing for Lambda functions
- **Log Retention**: 180-day retention for all CloudWatch logs

## Security

- **IAM**: Least privilege access principles
- **Encryption**: At-rest and in-transit encryption
- **CORS**: Properly configured for frontend-backend communication
- **Rate Limiting**: API Gateway throttling protection
- **CIS Compliance**: AWS Security Hub control standards

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `make test`
5. Submit a pull request

## Documentation

- [Architecture Documentation](docs/architecture.md)
- [Deployment Guide](docs/deployment.md)
- [API Documentation](docs/api.md)
- [Troubleshooting Guide](docs/troubleshooting.md)
- [Cost Analysis](docs/cost-analysis.md)

## Support

For issues and questions:
1. Check the [troubleshooting guide](docs/troubleshooting.md)
2. Review existing GitHub issues
3. Create a new issue with detailed information

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Status**: ✅ Project structure and configuration complete
**Next Steps**: Implement core Python weather service (Task 2.1)
