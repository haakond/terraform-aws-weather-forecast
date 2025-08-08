# Frontend Module Variables

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
}
# Additional variables for S3 bucket configuration
variable "bucket_versioning_enabled" {
  description = "Enable versioning for the S3 bucket"
  type        = bool
  default     = true
}

variable "lifecycle_rules_enabled" {
  description = "Enable lifecycle rules for the S3 bucket"
  type        = bool
  default     = true
}

variable "cloudfront_price_class" {
  description = "CloudFront price class"
  type        = string
  default     = "PriceClass_100"
  validation {
    condition = contains([
      "PriceClass_All",
      "PriceClass_200",
      "PriceClass_100"
    ], var.cloudfront_price_class)
    error_message = "CloudFront price class must be one of: PriceClass_All, PriceClass_200, PriceClass_100."
  }
}

variable "api_gateway_url" {
  description = "API Gateway URL for the backend service"
  type        = string
}

variable "frontend_source_path" {
  description = "Path to the frontend source code directory (relative to Terraform root). The module will automatically search for the directory if not found at the specified path."
  type        = string
  default     = "frontend"
}

