# Test file for backend module DynamoDB configuration

run "validate_dynamodb_table_configuration" {
  command = plan

  variables {
    project_name    = "test-weather-app"
    environment     = "dev"
    aws_region      = "eu-west-1"
    company_website = "test.example.com"
    budget_limit    = 50
  }

  # Test that DynamoDB table is created with correct configuration
  assert {
    condition     = module.backend.dynamodb_table_name == "test-weather-app-weather-cache"
    error_message = "DynamoDB table name should follow the naming convention"
  }

  # Test that DynamoDB table ARN is available
  assert {
    condition     = module.backend.dynamodb_table_arn != null
    error_message = "DynamoDB table ARN should be available"
  }

  # Test that Lambda role ARN is available
  assert {
    condition     = module.backend.lambda_role_arn != null
    error_message = "Lambda role ARN should be available"
  }
}

run "validate_dynamodb_table_features" {
  command = plan

  variables {
    project_name    = "test-weather-app"
    environment     = "dev"
    aws_region      = "eu-west-1"
    company_website = "test.example.com"
    budget_limit    = 50
  }

  # Test that DynamoDB table name follows naming convention
  assert {
    condition     = module.backend.dynamodb_table_name == "test-weather-app-weather-cache"
    error_message = "DynamoDB table name should follow the naming convention: project_name-weather-cache"
  }

  # Test that DynamoDB table ARN is properly formatted
  assert {
    condition     = can(regex("^arn:aws:dynamodb:", module.backend.dynamodb_table_arn))
    error_message = "DynamoDB table ARN should be properly formatted"
  }

  # Test that Lambda role ARN is properly formatted
  assert {
    condition     = can(regex("^arn:aws:iam:", module.backend.lambda_role_arn))
    error_message = "Lambda role ARN should be properly formatted"
  }
}

run "validate_backend_module_outputs" {
  command = plan

  variables {
    project_name    = "test-weather-app"
    environment     = "dev"
    aws_region      = "eu-west-1"
    company_website = "test.example.com"
    budget_limit    = 50
  }

  # Test that backend module outputs are available
  assert {
    condition     = module.backend.dynamodb_table_name != null
    error_message = "Backend module should output DynamoDB table name"
  }

  assert {
    condition     = module.backend.dynamodb_table_arn != null
    error_message = "Backend module should output DynamoDB table ARN"
  }

  assert {
    condition     = module.backend.lambda_role_arn != null
    error_message = "Backend module should output Lambda role ARN"
  }
}

run "validate_iam_permissions" {
  command = plan

  variables {
    project_name    = "test-weather-app"
    environment     = "dev"
    aws_region      = "eu-west-1"
    company_website = "test.example.com"
    budget_limit    = 50
  }

  # Test that Lambda role ARN is available and properly formatted
  assert {
    condition     = can(regex("^arn:aws:iam::[0-9]+:role/test-weather-app-lambda-dynamodb-role$", module.backend.lambda_role_arn))
    error_message = "Lambda role ARN should follow the expected naming pattern"
  }

  # Test that DynamoDB table ARN is available for IAM policy reference
  assert {
    condition     = can(regex("^arn:aws:dynamodb:[a-z0-9-]+:[0-9]+:table/test-weather-app-weather-cache$", module.backend.dynamodb_table_arn))
    error_message = "DynamoDB table ARN should follow the expected naming pattern"
  }

  # Test that outputs are consistent between table name and ARN
  assert {
    condition     = endswith(module.backend.dynamodb_table_arn, module.backend.dynamodb_table_name)
    error_message = "DynamoDB table ARN should end with the table name"
  }
}