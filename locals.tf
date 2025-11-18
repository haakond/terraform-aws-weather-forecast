# Weather Forecast App - Local Values

locals {
  name_prefix = "${var.project_name}-${var.environment}"

  common_tags = {
    Name        = local.name_prefix
    Service     = "weather-forecast-app"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}
