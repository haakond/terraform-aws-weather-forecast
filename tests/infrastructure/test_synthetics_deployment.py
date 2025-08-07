"""
Test CloudWatch Synthetics deployment via Terraform.
"""

import json
import os
import subprocess
import tempfile
import pytest
import boto3
from botocore.exceptions import ClientError


class TestSyntheticsDeployment:
    """Test CloudWatch Synthetics infrastructure deployment."""

    def test_synthetics_canary_script_exists(self):
        """Test that the Synthetics canary script exists."""
        script_path = os.path.join(
            os.path.dirname(__file__),
            '..', '..',
            'modules', 'monitoring', 'synthetics_canary.js'
        )
        assert os.path.exists(script_path), "Synthetics canary script not found"

        # Verify script content
        with open(script_path, 'r') as f:
            content = f.read()

        # Check for required functions
        assert 'pageLoadBlueprint' in content, "pageLoadBlueprint function not found"
        assert 'exports.handler' in content, "Handler export not found"
        assert 'synthetics.executeStep' in content, "Synthetics executeStep not found"

    def test_terraform_synthetics_resources(self):
        """Test that Terraform includes Synthetics resources."""
        monitoring_tf_path = os.path.join(
            os.path.dirname(__file__),
            '..', '..',
            'modules', 'monitoring', 'main.tf'
        )

        assert os.path.exists(monitoring_tf_path), "Monitoring module main.tf not found"

        with open(monitoring_tf_path, 'r') as f:
            content = f.read()

        # Check for required Synthetics resources
        assert 'aws_synthetics_canary' in content, "Synthetics canary resource not found"
        assert 'aws_s3_bucket' in content, "S3 bucket for artifacts not found"
        assert 'aws_iam_role' in content, "IAM role for canary not found"
        assert 'synthetics_canary_role' in content, "Synthetics canary role not found"

    def test_synthetics_variables_defined(self):
        """Test that required variables are defined for Synthetics."""
        variables_path = os.path.join(
            os.path.dirname(__file__),
            '..', '..',
            'modules', 'monitoring', 'variables.tf'
        )

        assert os.path.exists(variables_path), "Monitoring variables.tf not found"

        with open(variables_path, 'r') as f:
            content = f.read()

        # Check for Synthetics-specific variables
        assert 'cloudfront_distribution_domain' in content, "CloudFront domain variable not found"
        assert 'api_gateway_url' in content, "API Gateway URL variable not found"

    def test_synthetics_outputs_defined(self):
        """Test that Synthetics outputs are defined."""
        outputs_path = os.path.join(
            os.path.dirname(__file__),
            '..', '..',
            'modules', 'monitoring', 'outputs.tf'
        )

        assert os.path.exists(outputs_path), "Monitoring outputs.tf not found"

        with open(outputs_path, 'r') as f:
            content = f.read()

        # Check for Synthetics outputs
        assert 'synthetics_canary_name' in content, "Synthetics canary name output not found"
        assert 'synthetics_canary_arn' in content, "Synthetics canary ARN output not found"
        assert 'synthetics_artifacts_bucket' in content, "Synthetics artifacts bucket output not found"

    def test_main_tf_passes_synthetics_variables(self):
        """Test that main.tf passes required variables to monitoring module."""
        main_tf_path = os.path.join(
            os.path.dirname(__file__),
            '..', '..',
            'main.tf'
        )

        assert os.path.exists(main_tf_path), "main.tf not found"

        with open(main_tf_path, 'r') as f:
            content = f.read()

        # Check that monitoring module call includes Synthetics variables
        assert 'cloudfront_distribution_domain' in content, "CloudFront domain not passed to monitoring"
        assert 'api_gateway_url' in content, "API Gateway URL not passed to monitoring"

    def test_synthetics_canary_script_syntax(self):
        """Test that the Synthetics canary script has valid JavaScript syntax."""
        script_path = os.path.join(
            os.path.dirname(__file__),
            '..', '..',
            'modules', 'monitoring', 'synthetics_canary.js'
        )

        with open(script_path, 'r') as f:
            content = f.read()

        # Basic syntax checks
        assert content.count('{') == content.count('}'), "Mismatched braces in JavaScript"
        assert content.count('(') == content.count(')'), "Mismatched parentheses in JavaScript"
        assert 'exports.handler' in content, "Missing exports.handler"

        # Check for required Synthetics API calls
        assert 'synthetics.executeStep' in content, "Missing synthetics.executeStep calls"
        assert 'page.goto' in content, "Missing page navigation"
        assert 'page.waitForSelector' in content, "Missing element waiting"

    def test_synthetics_iam_permissions(self):
        """Test that IAM permissions for Synthetics are properly configured."""
        monitoring_tf_path = os.path.join(
            os.path.dirname(__file__),
            '..', '..',
            'modules', 'monitoring', 'main.tf'
        )

        with open(monitoring_tf_path, 'r') as f:
            content = f.read()

        # Check for required IAM permissions
        assert 's3:PutObject' in content, "S3 PutObject permission not found"
        assert 's3:GetObject' in content, "S3 GetObject permission not found"
        assert 'logs:CreateLogGroup' in content, "CloudWatch Logs permission not found"
        assert 'cloudwatch:PutMetricData' in content, "CloudWatch metrics permission not found"
        assert 'CloudWatchSyntheticsExecutionRolePolicy' in content, "Synthetics execution policy not attached"

    @pytest.mark.skipif(
        not os.environ.get('AWS_ACCESS_KEY_ID'),
        reason="AWS credentials not available"
    )
    def test_synthetics_service_availability(self):
        """Test that CloudWatch Synthetics service is available in the region."""
        try:
            synthetics_client = boto3.client('synthetics', region_name='eu-west-1')

            # Try to list canaries (should work even if none exist)
            response = synthetics_client.describe_canaries(MaxResults=1)
            assert 'Canaries' in response, "Synthetics service not available"

        except ClientError as e:
            if e.response['Error']['Code'] in ['AccessDenied', 'UnauthorizedOperation']:
                pytest.skip(f"Insufficient permissions to test Synthetics service: {e}")
            else:
                raise

    def test_terraform_synthetics_plan_validation(self):
        """Test that Terraform plan includes Synthetics resources."""
        # This test would require a full Terraform workspace setup
        # For now, we'll do a basic validation of the configuration

        monitoring_tf_path = os.path.join(
            os.path.dirname(__file__),
            '..', '..',
            'modules', 'monitoring', 'main.tf'
        )

        with open(monitoring_tf_path, 'r') as f:
            content = f.read()

        # Verify conditional resource creation
        assert 'count = var.cloudfront_distribution_domain != ""' in content, \
            "Synthetics canary should be conditionally created"

        # Verify resource dependencies
        assert 'depends_on' in content, "Resource dependencies not properly defined"

        # Verify template file usage
        assert 'templatefile' in content, "Template file not used for canary script"


class TestSyntheticsConfiguration:
    """Test Synthetics configuration and settings."""

    def test_canary_schedule_configuration(self):
        """Test that canary schedule is properly configured."""
        monitoring_tf_path = os.path.join(
            os.path.dirname(__file__),
            '..', '..',
            'modules', 'monitoring', 'main.tf'
        )

        with open(monitoring_tf_path, 'r') as f:
            content = f.read()

        # Check schedule configuration
        assert 'rate(5 minutes)' in content, "Canary schedule not set to 5 minutes"
        assert 'timeout_in_seconds' in content, "Timeout not configured"
        assert 'memory_in_mb' in content, "Memory not configured"
        assert 'active_tracing = true' in content, "X-Ray tracing not enabled"

    def test_canary_retention_settings(self):
        """Test that canary retention settings are configured."""
        monitoring_tf_path = os.path.join(
            os.path.dirname(__file__),
            '..', '..',
            'modules', 'monitoring', 'main.tf'
        )

        with open(monitoring_tf_path, 'r') as f:
            content = f.read()

        # Check retention settings
        assert 'failure_retention_period = 30' in content, "Failure retention not set"
        assert 'success_retention_period = 30' in content, "Success retention not set"

    def test_synthetics_alarm_configuration(self):
        """Test that CloudWatch alarms for Synthetics are configured."""
        monitoring_tf_path = os.path.join(
            os.path.dirname(__file__),
            '..', '..',
            'modules', 'monitoring', 'main.tf'
        )

        with open(monitoring_tf_path, 'r') as f:
            content = f.read()

        # Check alarm configuration
        assert 'synthetics_canary_failure' in content, "Synthetics failure alarm not found"
        assert 'SuccessPercent' in content, "Success percentage metric not monitored"
        assert 'LessThanThreshold' in content, "Alarm threshold not properly configured"
        assert 'threshold           = "90"' in content, "Success threshold not set to 90%"

    def test_synthetics_dashboard_integration(self):
        """Test that Synthetics metrics are included in dashboard."""
        monitoring_tf_path = os.path.join(
            os.path.dirname(__file__),
            '..', '..',
            'modules', 'monitoring', 'main.tf'
        )

        with open(monitoring_tf_path, 'r') as f:
            content = f.read()

        # Check dashboard integration
        assert 'CloudWatchSynthetics' in content, "Synthetics metrics not in dashboard"
        assert 'End-to-End Test Results' in content, "E2E test widget not in dashboard"
        assert 'End-to-End Test Failures' in content, "E2E failure logs not in dashboard"