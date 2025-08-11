#!/usr/bin/env python3
"""
Test script to verify Lambda handler imports work correctly.
This simulates the AWS Lambda environment import behavior.
"""

import sys
import os
import tempfile
import zipfile
import shutil

def test_lambda_imports():
    """Test that Lambda handler imports work in a simulated Lambda environment."""

    # Get the source directory
    src_dir = os.path.join(os.path.dirname(__file__), 'src')

    # Create a temporary directory to simulate Lambda environment
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Testing in temporary directory: {temp_dir}")

        # Copy source files to temp directory (simulating Lambda deployment)
        for item in os.listdir(src_dir):
            src_path = os.path.join(src_dir, item)
            dst_path = os.path.join(temp_dir, item)
            if os.path.isdir(src_path):
                shutil.copytree(src_path, dst_path)
            else:
                shutil.copy2(src_path, dst_path)

        # Add temp directory to Python path (simulating Lambda environment)
        sys.path.insert(0, temp_dir)

        try:
            # Test importing the Lambda handler (this is what AWS Lambda does)
            print("Testing lambda_handler import...")
            import lambda_handler
            print("✓ Successfully imported lambda_handler")

            # Test that the handler function exists
            if hasattr(lambda_handler, 'lambda_handler'):
                print("✓ lambda_handler function found")
            else:
                print("✗ lambda_handler function not found")
                return False

            # Test importing weather_service components
            print("Testing weather_service imports...")
            from weather_service import WeatherProcessor, create_weather_processor
            print("✓ Successfully imported weather_service components")

            # Test creating a weather processor (basic functionality test)
            print("Testing weather processor creation...")
            processor = create_weather_processor()
            print("✓ Successfully created weather processor")

            print("\n🎉 All Lambda import tests passed!")
            return True

        except ImportError as e:
            print(f"✗ Import error: {e}")
            return False
        except Exception as e:
            print(f"✗ Unexpected error: {e}")
            return False
        finally:
            # Clean up sys.path
            if temp_dir in sys.path:
                sys.path.remove(temp_dir)

if __name__ == "__main__":
    success = test_lambda_imports()
    sys.exit(0 if success else 1)
