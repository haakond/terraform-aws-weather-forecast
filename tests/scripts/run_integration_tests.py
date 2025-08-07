#!/usr/bin/env python3
"""
Integration test runner with cleanup.
Runs integration tests and ensures proper cleanup of resources.
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IntegrationTestRunner:
    """Manages integration test execution with cleanup."""

    def __init__(self, test_environment='test', cleanup=True, verbose=False):
        self.test_environment = test_environment
        self.cleanup = cleanup
        self.verbose = verbose
        self.test_resources = []
        self.start_time = datetime.now()

        # Set up paths
        self.project_root = Path(__file__).parent.parent.parent
        self.test_dir = self.project_root / 'tests'

        # Test configuration
        self.test_config = {
            'project_name': f'weather-test-{int(time.time())}',
            'environment': self.test_environment,
            'aws_region': 'eu-west-1',
            'company_website': 'test.example.com',
            'budget_limit': 10,  # Low budget for testing
            'log_retention_days': 1  # Minimal retention for testing
        }

    def run_all_tests(self):
        """Run all integration tests with proper setup and cleanup."""
        logger.info("Starting integration test suite")

        try:
            # Setup test environment
            self.setup_test_environment()

            # Run Python integration tests
            self.run_python_integration_tests()

            # Run infrastructure tests
            self.run_infrastructure_tests()

            # Run end-to-end tests (if infrastructure is deployed)
            if self.test_environment == 'deployed':
                self.run_e2e_tests()

            logger.info("All integration tests completed successfully")
            return True

        except Exception as e:
            logger.error(f"Integration tests failed: {e}")
            return False

        finally:
            if self.cleanup:
                self.cleanup_test_resources()

    def setup_test_environment(self):
        """Setup test environment and dependencies."""
        logger.info("Setting up test environment")

        # Create virtual environment for testing
        venv_path = self.project_root / '.test-venv'
        if not venv_path.exists():
            subprocess.run([
                sys.executable, '-m', 'venv', str(venv_path)
            ], check=True)

        # Install test dependencies
        pip_path = venv_path / 'bin' / 'pip'
        subprocess.run([
            str(pip_path), 'install', '-r',
            str(self.project_root / 'requirements-dev.txt')
        ], check=True)

        # Set environment variables for testing
        os.environ.update({
            'PYTHONPATH': str(self.project_root / 'src'),
            'AWS_DEFAULT_REGION': self.test_config['aws_region'],
            'DYNAMODB_TABLE_NAME': f"{self.test_config['project_name']}-cache",
            'COMPANY_WEBSITE': self.test_config['company_website'],
            'LOG_LEVEL': 'DEBUG' if self.verbose else 'INFO'
        })

        logger.info("Test environment setup completed")

    def run_python_integration_tests(self):
        """Run Python integration tests."""
        logger.info("Running Python integration tests")

        # Run pytest with integration tests
        cmd = [
            sys.executable, '-m', 'pytest',
            str(self.test_dir / 'integration'),
            '-v' if self.verbose else '-q',
            '--tb=short',
            '--junit-xml=test-results-integration.xml'
        ]

        result = subprocess.run(cmd, cwd=self.project_root)

        if result.returncode != 0:
            raise RuntimeError("Python integration tests failed")

        logger.info("Python integration tests passed")

    def run_infrastructure_tests(self):
        """Run infrastructure deployment tests."""
        logger.info("Running infrastructure tests")

        # Run pytest with infrastructure tests
        cmd = [
            sys.executable, '-m', 'pytest',
            str(self.test_dir / 'infrastructure'),
            '-v' if self.verbose else '-q',
            '--tb=short',
            '--junit-xml=test-results-infrastructure.xml'
        ]

        result = subprocess.run(cmd, cwd=self.project_root)

        if result.returncode != 0:
            raise RuntimeError("Infrastructure tests failed")

        logger.info("Infrastructure tests passed")

    def run_e2e_tests(self):
        """Run end-to-end tests (requires deployed infrastructure)."""
        logger.info("Running end-to-end tests")

        # This would typically deploy infrastructure first, then run E2E tests
        # For now, we'll simulate this with a placeholder

        logger.info("End-to-end tests completed (simulated)")

    def cleanup_test_resources(self):
        """Clean up test resources and temporary files."""
        logger.info("Cleaning up test resources")

        try:
            # Remove test virtual environment
            venv_path = self.project_root / '.test-venv'
            if venv_path.exists():
                subprocess.run(['rm', '-rf', str(venv_path)], check=True)

            # Remove test result files
            for result_file in self.project_root.glob('test-results-*.xml'):
                result_file.unlink()

            # Remove any temporary Terraform files
            for tf_file in self.project_root.glob('*.tfplan'):
                tf_file.unlink()

            for tf_file in self.project_root.glob('*.tfstate*'):
                tf_file.unlink()

            # Clean up any test DynamoDB tables (if using local DynamoDB)
            self.cleanup_dynamodb_tables()

            logger.info("Test resource cleanup completed")

        except Exception as e:
            logger.warning(f"Cleanup encountered errors: {e}")

    def cleanup_dynamodb_tables(self):
        """Clean up test DynamoDB tables."""
        try:
            import boto3
            from botocore.exceptions import ClientError

            dynamodb = boto3.client('dynamodb', region_name=self.test_config['aws_region'])

            # List tables with test prefix
            response = dynamodb.list_tables()
            test_tables = [
                table for table in response['TableNames']
                if table.startswith(self.test_config['project_name'])
            ]

            # Delete test tables
            for table_name in test_tables:
                try:
                    dynamodb.delete_table(TableName=table_name)
                    logger.info(f"Deleted test table: {table_name}")
                except ClientError as e:
                    if e.response['Error']['Code'] != 'ResourceNotFoundException':
                        logger.warning(f"Failed to delete table {table_name}: {e}")

        except ImportError:
            logger.info("boto3 not available, skipping DynamoDB cleanup")
        except Exception as e:
            logger.warning(f"DynamoDB cleanup failed: {e}")

    def generate_test_report(self):
        """Generate test execution report."""
        end_time = datetime.now()
        duration = end_time - self.start_time

        report = {
            'test_run': {
                'start_time': self.start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration.total_seconds(),
                'environment': self.test_environment,
                'cleanup_performed': self.cleanup
            },
            'configuration': self.test_config,
            'resources_created': self.test_resources
        }

        report_file = self.project_root / 'test-report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Test report generated: {report_file}")
        return report


def main():
    """Main entry point for integration test runner."""
    parser = argparse.ArgumentParser(description='Run integration tests with cleanup')
    parser.add_argument(
        '--environment',
        choices=['test', 'deployed'],
        default='test',
        help='Test environment type'
    )
    parser.add_argument(
        '--no-cleanup',
        action='store_true',
        help='Skip cleanup of test resources'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate test execution report'
    )

    args = parser.parse_args()

    # Create test runner
    runner = IntegrationTestRunner(
        test_environment=args.environment,
        cleanup=not args.no_cleanup,
        verbose=args.verbose
    )

    # Run tests
    success = runner.run_all_tests()

    # Generate report if requested
    if args.report:
        runner.generate_test_report()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()