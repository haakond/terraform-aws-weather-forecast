# CI/CD Integration Examples

## TL;DR

This directory contains examples for integrating the Weather Forecast App Terraform module into various CI/CD pipelines.

**Quick Setup:**
```bash
# Copy the example that matches your CI/CD platform
cp -r examples/ci-cd-integration/github-actions .github/workflows/
cp -r examples/ci-cd-integration/gitlab-ci .gitlab-ci.yml
```

## Overview

The Weather Forecast App can be integrated into CI/CD pipelines for automated deployment and testing. This directory provides examples for popular CI/CD platforms:

- **GitHub Actions** - Complete workflow with testing and deployment
- **GitLab CI** - Pipeline with multiple stages and environments
- **Jenkins** - Jenkinsfile with pipeline stages
- **Azure DevOps** - Azure Pipelines YAML configuration
- **AWS CodePipeline** - Native AWS CI/CD solution

## Prerequisites

### Required Secrets/Variables

All CI/CD platforms need these environment variables configured:

| Variable | Description | Example |
|----------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | AWS access key | `AKIA...` |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | `wJalr...` |
| `AWS_DEFAULT_REGION` | AWS region | `eu-west-1` |
| `TF_VAR_project_name` | Project name | `weather-app-prod` |
| `TF_VAR_environment` | Environment | `prod` |
| `TF_VAR_company_website` | Company website | `mycompany.com` |
| `TF_VAR_budget_limit` | Budget limit | `100` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TERRAFORM_VERSION` | Terraform version | `1.5.0` |
| `PYTHON_VERSION` | Python version | `3.13` |
| `NODE_VERSION` | Node.js version | `18` |

## GitHub Actions

### Complete Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy Weather Forecast App

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  TERRAFORM_VERSION: 1.5.0
  PYTHON_VERSION: 3.13
  AWS_DEFAULT_REGION: eu-west-1

jobs:
  test:
    name: Test
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TERRAFORM_VERSION }}

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_DEFAULT_REGION }}

      - name: Install Python dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements-dev.txt

      - name: Run Python tests
        run: |
          python -m pytest tests/unit/ -v
          python -m pytest tests/integration/ -v

      - name: Terraform Format Check
        run: terraform fmt -check

      - name: Terraform Init
        run: terraform init

      - name: Terraform Validate
        run: terraform validate

      - name: Terraform Plan
        run: terraform plan -var-file="environments/dev.tfvars"

  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/develop'
    environment: staging

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TERRAFORM_VERSION }}

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_DEFAULT_REGION }}

      - name: Terraform Init
        run: terraform init

      - name: Terraform Apply
        run: terraform apply -auto-approve -var-file="environments/staging.tfvars"

      - name: Run Integration Tests
        run: |
          python -m pytest tests/integration/ -v --api-url=$(terraform output -raw api_gateway_url)

  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'
    environment: production

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TERRAFORM_VERSION }}

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_DEFAULT_REGION }}

      - name: Terraform Init
        run: terraform init

      - name: Terraform Plan
        run: terraform plan -var-file="environments/prod.tfvars"

      - name: Terraform Apply
        run: terraform apply -auto-approve -var-file="environments/prod.tfvars"

      - name: Run Smoke Tests
        run: |
          # Test application endpoints
          curl -f $(terraform output -raw cloudfront_distribution_domain)
          curl -f $(terraform output -raw api_gateway_url)/health

      - name: Notify Deployment
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          channel: '#deployments'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
        if: always()
```

### Environment-Specific Workflows

Create separate workflows for different environments:

**`.github/workflows/deploy-dev.yml`**:
```yaml
name: Deploy Development

on:
  push:
    branches: [feature/*]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3
      - name: Deploy
        run: |
          terraform init
          terraform apply -auto-approve -var="environment=dev-${{ github.run_number }}"
```

## GitLab CI

Create `.gitlab-ci.yml`:

```yaml
stages:
  - validate
  - test
  - plan
  - deploy
  - cleanup

variables:
  TERRAFORM_VERSION: "1.5.0"
  PYTHON_VERSION: "3.13"
  TF_ROOT: ${CI_PROJECT_DIR}
  TF_ADDRESS: ${CI_API_V4_URL}/projects/${CI_PROJECT_ID}/terraform/state/weather-app

cache:
  paths:
    - .terraform
    - venv/

before_script:
  - apt-get update -qq && apt-get install -y -qq git curl unzip
  - curl -LO https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip
  - unzip terraform_${TERRAFORM_VERSION}_linux_amd64.zip
  - mv terraform /usr/local/bin/
  - terraform --version

validate:
  stage: validate
  script:
    - terraform init -backend=false
    - terraform validate
    - terraform fmt -check
  only:
    - merge_requests
    - main
    - develop

test:
  stage: test
  image: python:${PYTHON_VERSION}
  script:
    - pip install -r requirements-dev.txt
    - python -m pytest tests/unit/ -v
    - python -m pytest tests/integration/ -v
  only:
    - merge_requests
    - main
    - develop

plan:
  stage: plan
  script:
    - terraform init
    - terraform plan -var-file="environments/${CI_COMMIT_REF_NAME}.tfvars" -out=plan.tfplan
  artifacts:
    paths:
      - plan.tfplan
    expire_in: 1 week
  only:
    - main
    - develop

deploy:staging:
  stage: deploy
  script:
    - terraform init
    - terraform apply -auto-approve -var-file="environments/staging.tfvars"
  environment:
    name: staging
    url: https://$CI_PROJECT_NAME-staging.example.com
  only:
    - develop

deploy:production:
  stage: deploy
  script:
    - terraform init
    - terraform apply -auto-approve -var-file="environments/prod.tfvars"
  environment:
    name: production
    url: https://$CI_PROJECT_NAME.example.com
  when: manual
  only:
    - main

cleanup:
  stage: cleanup
  script:
    - terraform destroy -auto-approve -var-file="environments/review-${CI_MERGE_REQUEST_IID}.tfvars"
  environment:
    name: review/${CI_MERGE_REQUEST_IID}
    action: stop
  when: manual
  only:
    - merge_requests
```

## Jenkins

Create `Jenkinsfile`:

```groovy
pipeline {
    agent any

    parameters {
        choice(
            name: 'ENVIRONMENT',
            choices: ['dev', 'staging', 'prod'],
            description: 'Environment to deploy to'
        )
        booleanParam(
            name: 'DESTROY',
            defaultValue: false,
            description: 'Destroy infrastructure instead of creating it'
        )
    }

    environment {
        AWS_DEFAULT_REGION = 'eu-west-1'
        TERRAFORM_VERSION = '1.5.0'
        PYTHON_VERSION = '3.13'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup') {
            parallel {
                stage('Setup Terraform') {
                    steps {
                        sh '''
                            curl -LO https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip
                            unzip terraform_${TERRAFORM_VERSION}_linux_amd64.zip
                            sudo mv terraform /usr/local/bin/
                            terraform --version
                        '''
                    }
                }

                stage('Setup Python') {
                    steps {
                        sh '''
                            python${PYTHON_VERSION} -m venv venv
                            . venv/bin/activate
                            pip install -r requirements-dev.txt
                        '''
                    }
                }
            }
        }

        stage('Test') {
            parallel {
                stage('Python Tests') {
                    steps {
                        sh '''
                            . venv/bin/activate
                            python -m pytest tests/unit/ -v --junitxml=test-results.xml
                        '''
                    }
                    post {
                        always {
                            junit 'test-results.xml'
                        }
                    }
                }

                stage('Terraform Validate') {
                    steps {
                        sh '''
                            terraform init -backend=false
                            terraform validate
                            terraform fmt -check
                        '''
                    }
                }
            }
        }

        stage('Plan') {
            when {
                not { params.DESTROY }
            }
            steps {
                withCredentials([
                    [$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws-credentials']
                ]) {
                    sh '''
                        terraform init
                        terraform plan -var-file="environments/${ENVIRONMENT}.tfvars" -out=tfplan
                    '''
                }
            }
        }

        stage('Apply') {
            when {
                anyOf {
                    branch 'main'
                    branch 'develop'
                }
                not { params.DESTROY }
            }
            steps {
                input message: 'Deploy to ${ENVIRONMENT}?', ok: 'Deploy'
                withCredentials([
                    [$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws-credentials']
                ]) {
                    sh '''
                        terraform apply -auto-approve tfplan
                    '''
                }
            }
        }

        stage('Integration Tests') {
            when {
                not { params.DESTROY }
            }
            steps {
                sh '''
                    . venv/bin/activate
                    API_URL=$(terraform output -raw api_gateway_url)
                    python -m pytest tests/integration/ -v --api-url=$API_URL
                '''
            }
        }

        stage('Destroy') {
            when {
                params.DESTROY
            }
            steps {
                input message: 'Destroy ${ENVIRONMENT} infrastructure?', ok: 'Destroy'
                withCredentials([
                    [$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws-credentials']
                ]) {
                    sh '''
                        terraform init
                        terraform destroy -auto-approve -var-file="environments/${ENVIRONMENT}.tfvars"
                    '''
                }
            }
        }
    }

    post {
        always {
            cleanWs()
        }
        success {
            slackSend(
                channel: '#deployments',
                color: 'good',
                message: "✅ Weather App deployed to ${params.ENVIRONMENT} successfully"
            )
        }
        failure {
            slackSend(
                channel: '#deployments',
                color: 'danger',
                message: "❌ Weather App deployment to ${params.ENVIRONMENT} failed"
            )
        }
    }
}
```

## Azure DevOps

Create `azure-pipelines.yml`:

```yaml
trigger:
  branches:
    include:
      - main
      - develop

pr:
  branches:
    include:
      - main

variables:
  terraformVersion: '1.5.0'
  pythonVersion: '3.13'
  awsRegion: 'eu-west-1'

stages:
- stage: Test
  displayName: 'Test Stage'
  jobs:
  - job: TestJob
    displayName: 'Run Tests'
    pool:
      vmImage: 'ubuntu-latest'
    steps:
    - task: UsePythonVersion@0
      inputs:
        versionSpec: '$(pythonVersion)'
      displayName: 'Setup Python'

    - task: TerraformInstaller@0
      inputs:
        terraformVersion: '$(terraformVersion)'
      displayName: 'Install Terraform'

    - script: |
        pip install -r requirements-dev.txt
        python -m pytest tests/unit/ -v
      displayName: 'Run Python Tests'

    - script: |
        terraform init -backend=false
        terraform validate
        terraform fmt -check
      displayName: 'Validate Terraform'

- stage: Deploy
  displayName: 'Deploy Stage'
  dependsOn: Test
  condition: and(succeeded(), in(variables['Build.SourceBranch'], 'refs/heads/main', 'refs/heads/develop'))
  jobs:
  - deployment: DeployJob
    displayName: 'Deploy to AWS'
    pool:
      vmImage: 'ubuntu-latest'
    environment: 'production'
    strategy:
      runOnce:
        deploy:
          steps:
          - task: TerraformInstaller@0
            inputs:
              terraformVersion: '$(terraformVersion)'
            displayName: 'Install Terraform'

          - task: AWSShellScript@1
            inputs:
              awsCredentials: 'aws-service-connection'
              regionName: '$(awsRegion)'
              scriptType: 'inline'
              inlineScript: |
                terraform init
                terraform plan -var-file="environments/prod.tfvars"
                terraform apply -auto-approve -var-file="environments/prod.tfvars"
            displayName: 'Deploy Infrastructure'

          - script: |
              curl -f $(terraform output -raw cloudfront_distribution_domain)
              curl -f $(terraform output -raw api_gateway_url)/health
            displayName: 'Smoke Tests'
```

## AWS CodePipeline

Create `buildspec.yml` for CodeBuild:

```yaml
version: 0.2

phases:
  install:
    runtime-versions:
      python: 3.13
    commands:
      - echo Installing Terraform
      - curl -LO https://releases.hashicorp.com/terraform/1.5.0/terraform_1.5.0_linux_amd64.zip
      - unzip terraform_1.5.0_linux_amd64.zip
      - mv terraform /usr/local/bin/
      - terraform --version

  pre_build:
    commands:
      - echo Installing Python dependencies
      - pip install -r requirements-dev.txt
      - echo Running tests
      - python -m pytest tests/unit/ -v

  build:
    commands:
      - echo Terraform init and validate
      - terraform init
      - terraform validate
      - terraform fmt -check
      - echo Planning Terraform deployment
      - terraform plan -var-file="environments/${ENVIRONMENT}.tfvars"

  post_build:
    commands:
      - echo Applying Terraform configuration
      - terraform apply -auto-approve -var-file="environments/${ENVIRONMENT}.tfvars"
      - echo Running integration tests
      - API_URL=$(terraform output -raw api_gateway_url)
      - python -m pytest tests/integration/ -v --api-url=$API_URL

artifacts:
  files:
    - '**/*'
```

Create CloudFormation template for CodePipeline:

```yaml
# codepipeline.yml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'CodePipeline for Weather Forecast App'

Parameters:
  GitHubRepo:
    Type: String
    Default: 'your-org/weather-forecast-app'
  GitHubBranch:
    Type: String
    Default: 'main'
  GitHubToken:
    Type: String
    NoEcho: true

Resources:
  CodePipelineServiceRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: codepipeline.amazonaws.com
            Action: sts:AssumeRole
      Policies:
        - PolicyName: CodePipelinePolicy
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - s3:GetObject
                  - s3:PutObject
                  - codebuild:BatchGetBuilds
                  - codebuild:StartBuild
                Resource: '*'

  WeatherAppPipeline:
    Type: AWS::CodePipeline::Pipeline
    Properties:
      RoleArn: !GetAtt CodePipelineServiceRole.Arn
      Stages:
        - Name: Source
          Actions:
            - Name: SourceAction
              ActionTypeId:
                Category: Source
                Owner: ThirdParty
                Provider: GitHub
                Version: '1'
              Configuration:
                Owner: !Select [0, !Split ['/', !Ref GitHubRepo]]
                Repo: !Select [1, !Split ['/', !Ref GitHubRepo]]
                Branch: !Ref GitHubBranch
                OAuthToken: !Ref GitHubToken
              OutputArtifacts:
                - Name: SourceOutput

        - Name: Build
          Actions:
            - Name: BuildAction
              ActionTypeId:
                Category: Build
                Owner: AWS
                Provider: CodeBuild
                Version: '1'
              Configuration:
                ProjectName: !Ref WeatherAppBuild
              InputArtifacts:
                - Name: SourceOutput
```

## Best Practices

### Security
- **Never commit secrets** to version control
- **Use environment-specific variables** for different deployments
- **Implement least privilege** IAM policies for CI/CD roles
- **Enable audit logging** for all deployments

### Testing
- **Run tests in parallel** to reduce pipeline time
- **Use different test environments** for different branches
- **Implement smoke tests** after deployment
- **Cache dependencies** to speed up builds

### Deployment
- **Use infrastructure as code** for all environments
- **Implement blue-green deployments** for zero downtime
- **Have rollback procedures** ready
- **Monitor deployments** with CloudWatch

### Monitoring
- **Set up alerts** for deployment failures
- **Track deployment metrics** (frequency, success rate, duration)
- **Monitor application health** after deployment
- **Use structured logging** for better debugging

## Troubleshooting CI/CD Issues

### Common Problems

1. **AWS Credentials Issues**
   - Verify credentials are correctly configured
   - Check IAM permissions for CI/CD role
   - Ensure credentials haven't expired

2. **Terraform State Conflicts**
   - Use remote state backend (S3 + DynamoDB)
   - Implement state locking
   - Handle concurrent deployments

3. **Test Failures**
   - Check test environment setup
   - Verify test data and dependencies
   - Review test logs for specific failures

4. **Deployment Timeouts**
   - Increase timeout values in CI/CD configuration
   - Check AWS service limits
   - Monitor resource creation progress

### Debugging Tips

```bash
# Enable Terraform debug logging
export TF_LOG=DEBUG

# Check AWS CLI configuration
aws sts get-caller-identity

# Validate Terraform configuration locally
terraform init
terraform validate
terraform plan
```

---

**Next Steps**: After setting up CI/CD, review the [operational runbooks](../../docs/operational-runbooks.md) for ongoing maintenance procedures.