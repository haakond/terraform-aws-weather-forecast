"""
Infrastructure deployment tests.
Tests that verify the Terraform infrastructure deploys correctly.
"""

import json
import os
import subprocess
import tempfile
import time
import pytest
import boto3
from botocore.exceptions import ClientError


class TestInfrastructureDeployment:
    """Test infrastructure deployment scenarios."""

    @pytest.fixture(scope="class")
    def terraform_workspace(self):
        """Create a temporary Terraform workspace for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Copy Terraform files to temp directory
            subprocess.run([
                'cp', '-r',
                os.path.join(os.path.dirname(__file__), '..', '..'),
                temp_dir
            ], check=True)

            workspace_dir = os.path.join(temp_dir, os.path.basename(os.getcwd()))

            # Initialize Terraform
            result = subprocess.run([
                'terraform', 'init'
            ], cwd=workspace_dir, capture_output=True, text=True)

            if result.returncode != 0:
                pytest.fail(f"Terraform init failed: {result.stderr}")

            yield workspace_dir

    def test_terraform_validate(self, terraform_workspace):
        """Test that Terraform configuration is valid."""
        result = subprocess.run([
            'terraform', 'validate'
        ], cwd=terraform_workspace, capture_output=True, text=True)

        assert result.returncode == 0, f"Terraform validation failed: {result.stderr}"
        assert "Success!" in result.stdout, "Terraform validation did not report success"

    def test_terraform_plan(self, terraform_workspace):
        """Test that Terraform plan executes without errors."""
        # Create test variables file
        test_vars = {
            'project_name': 'weather-test',
            'environment': 'test',
            'aws_region': 'eu-west-1',
            'company_website': 'test.com',
            'budget_limit': 25
        }

        vars_file = os.path.join(terraform_workspace, 'test.tfvars')
        with open(vars_file, 'w') as f:
            for key, value in test_vars.items():
                if isinstance(value, str):
                    f.write(f'{key} = "{value}"\n')
                else:
                    f.write(f'{key} = {value}\n')

        result = subprocess.run([
            'terraform', 'plan', f'-var-file={vars_file}', '-out=test.tfplan'
        ], cwd=terraform_workspace, capture_output=True, text=True)

        assert result.returncode == 0, f"Terraform plan failed: {result.stderr}"
        assert "Plan:" in result.stdout, "Terraform plan did not generate a plan"

    def test_terraform_plan_output_parsing(self, terraform_workspace):
        """Test that Terraform plan output can be parsed for resource counts."""
        test_vars = {
            'project_name': 'weather-test',
            'environment': 'test',
            'aws_region': 'eu-west-1',
            'company_website': 'test.com',
            'budget_limit': 25
        }

        vars_file = os.path.join(terraform_workspace, 'test.tfvars')
        with open(vars_file, 'w') as f:
            for key, value in test_vars.items():
                if isinstance(value, str):
                    f.write(f'{key} = "{value}"\n')
                else:
                    f.write(f'{key} = {value}\n')

        result = subprocess.run([
            'terraform', 'plan', f'-var-file={vars_file}', '-out=test.tfplan'
        ], cwd=terraform_workspace, capture_output=True, text=True)

        assert result.returncode == 0, f"Terraform plan failed: {result.stderr}"

        # Parse plan output for resource counts
        plan_output = result.stdout

        # Should plan to create resources (not destroy or modify)
        assert "to add" in plan_output, "Plan should include resources to add"
        assert "to destroy" not in plan_output or "0 to destroy" in plan_output, \
            "Plan should not destroy existing resources"

        # Verify key resources are planned
        expected_resources = [
            'aws_lambda_function',
            'aws_api_gateway_rest_api',
            'aws_dynamodb_table',
            'aws_s3_bucket',
            'aws_cloudfront_distribution',
            'aws_cloudwatch_dashboard',
            'aws_budgets_budget'
        ]

        for resource in expected_resources:
            assert resource in plan_output, f"Expected resource {resource} not found in plan"

    def test_terraform_fmt_check(self, terraform_workspace):
        """Test that Terraform files are properly formatted."""
        result = subprocess.run([
            'terraform', 'fmt', '-check', '-recursive'
        ], cwd=terraform_workspace, capture_output=True, text=True)

        assert result.returncode == 0, f"Terraform files not properly formatted: {result.stderr}"

    def test_module_structure(self, terraform_workspace):
        """Test that module structure is correct."""
        # Check that all required modules exist
        modules_dir = os.path.join(terraform_workspace, 'modules')
        assert os.path.exists(modules_dir), "Modules directory not found"

        required_modules = ['backend', 'frontend', 'monitoring']
        for module in required_modules:
            module_dir = os.path.join(modules_dir, module)
            assert os.path.exists(module_dir), f"Module {module} directory not found"

            # Check for required files in each module
            required_files = ['main.tf', 'variables.tf', 'outputs.tf']
            for file in required_files:
                file_path = os.path.join(module_dir, file)
                assert os.path.exists(file_path), f"Required file {file} not found in {module} module"

    def test_variable_validation(self, terraform_workspace):
        """Test variable validation rules."""
        # Test invalid project name
        invalid_vars = {
            'project_name': 'Invalid_Name_With_Underscores',
            'environment': 'test',
            'aws_region': 'eu-west-1'
        }

        vars_file = os.path.join(terraform_workspace, 'invalid.tfvars')
        with open(vars_file, 'w') as f:
            for key, value in invalid_vars.items():
                f.write(f'{key} = "{value}"\n')

        result = subprocess.run([
            'terraform', 'plan', f'-var-file={vars_file}'
        ], cwd=terraform_workspace, capture_output=True, text=True)

        # Should fail due to validation
        assert result.returncode != 0, "Terraform should fail with invalid project name"
        assert "validation" in result.stderr.lower(), "Error should mention validation"

    def test_provider_versions(self, terraform_workspace):
        """Test that provider versions are properly constrained."""
        versions_file = os.path.join(terraform_workspace, 'versions.tf')
        assert os.path.exists(versions_file), "versions.tf file not found"

        with open(versions_file, 'r') as f:
            content = f.read()

        # Check for required providers with version constraints
        required_providers = ['aws', 'awscc', 'random']
        for provider in required_providers:
            assert provider in content, f"Provider {provider} not found in versions.tf"
            assert '~>' in content, "Version constraints should use ~> operator"

    def test_outputs_defined(self, terraform_workspace):
        """Test that all expected outputs are defined."""
        outputs_file = os.path.join(terraform_workspace, 'outputs.tf')
        assert os.path.exists(outputs_file), "outputs.tf file not found"

        with open(outputs_file, 'r') as f:
            content = f.read()

        expected_outputs = [
            'cloudfront_distribution_domain',
            'api_gateway_url',
            'lambda_function_name',
            'dynamodb_table_name',
            's3_bucket_name',
            'cloudwatch_dashboard_url',
            'budget_name'
        ]

        for output in expected_outputs:
            assert f'output "{output}"' in content, f"Output {output} not defined"


class TestAWSResourceValidation:
    """Test AWS resource validation and permissions."""

    def test_aws_credentials_available(self):
        """Test that AWS credentials are available for testing."""
        try:
            sts = boto3.client('sts')
            identity = sts.get_caller_identity()
            assert 'Account' in identity, "AWS credentials not properly configured"
        except ClientError as e:
            pytest.skip(f"AWS credentials not available: {e}")

    def test_required_aws_permissions(self):
        """Test that required AWS permissions are available."""
        # This is a basic test - in practice, you'd test specific permissions
        try:
            # Test Lambda permissions
            lambda_client = boto3.client('lambda', region_name='eu-west-1')
            lambda_client.list_functions(MaxItems=1)

            # Test API Gateway permissions
            apigateway_client = boto3.client('apigateway', region_name='eu-west-1')
            apigateway_client.get_rest_apis(limit=1)

            # Test DynamoDB permissions
            dynamodb_client = boto3.client('dynamodb', region_name='eu-west-1')
            dynamodb_client.list_tables(Limit=1)

            # Test S3 permissions
            s3_client = boto3.client('s3', region_name='eu-west-1')
            s3_client.list_buckets()

            # Test CloudFront permissions
            cloudfront_client = boto3.client('cloudfront')
            cloudfront_client.list_distributions(MaxItems='1')

        except ClientError as e:
            if e.response['Error']['Code'] in ['AccessDenied', 'UnauthorizedOperation']:
                pytest.fail(f"Insufficient AWS permissions: {e}")
            else:
                # Other errors might be acceptable (e.g., resource not found)
                pass

    def test_aws_region_availability(self):
        """Test that the target AWS region is available."""
        try:
            ec2 = boto3.client('ec2', region_name='eu-west-1')
            regions = ec2.describe_regions()

            available_regions = [r['RegionName'] for r in regions['Regions']]
            assert 'eu-west-1' in available_regions, "Target region eu-west-1 not available"

        except ClientError as e:
            pytest.skip(f"Cannot verify AWS region availability: {e}")


class TestDeploymentScripts:
    """Test deployment automation scripts."""

    def test_makefile_targets(self):
        """Test that Makefile has required targets."""
        makefile_path = os.path.join(os.path.dirname(__file__), '..', '..', 'Makefile')

        if not os.path.exists(makefile_path):
            pytest.skip("Makefile not found")

        with open(makefile_path, 'r') as f:
            content = f.read()

        required_targets = ['test', 'test-python', 'test-tf', 'deploy', 'destroy']
        for target in required_targets:
            assert f'{target}:' in content, f"Makefile missing target: {target}"

    def test_requirements_files(self):
        """Test that Python requirements files are present and valid."""
        base_dir = os.path.join(os.path.dirname(__file__), '..', '..')

        # Check requirements.txt
        req_file = os.path.join(base_dir, 'requirements.txt')
        assert os.path.exists(req_file), "requirements.txt not found"

        with open(req_file, 'r') as f:
            content = f.read()
            assert 'boto3' in content, "boto3 not in requirements.txt"
            assert 'requests' in content, "requests not in requirements.txt"

        # Check requirements-dev.txt
        dev_req_file = os.path.join(base_dir, 'requirements-dev.txt')
        assert os.path.exists(dev_req_file), "requirements-dev.txt not found"

        with open(dev_req_file, 'r') as f:
            content = f.read()
            assert 'pytest' in content, "pytest not in requirements-dev.txt"
            assert 'moto' in content, "moto not in requirements-dev.txt"

    def test_precommit_config(self):
        """Test that pre-commit configuration is present and valid."""
        precommit_file = os.path.join(os.path.dirname(__file__), '..', '..', '.pre-commit-config.yaml')

        if not os.path.exists(precommit_file):
            pytest.skip(".pre-commit-config.yaml not found")

        with open(precommit_file, 'r') as f:
            content = f.read()

        required_hooks = ['terraform_fmt', 'terraform_docs', 'terraform_checkov']
        for hook in required_hooks:
            assert hook in content, f"Pre-commit hook {hook} not configured"