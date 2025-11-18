# Weather Forecast App - Provider Configuration

# Configure the AWS Provider
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Service     = "weather-forecast-app"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

provider "awscc" {
  region = var.aws_region
}
