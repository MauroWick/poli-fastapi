variable "aws_region" {
  description = "The AWS region to deploy the FastAPI application"
  type        = string
  default     = "us-east-1"
}

variable "function_name" {
  description = "The name of the AWS Lambda function"
  type        = string
  default     = "fastapi_lambda_function"
}

variable "account_id" {
  description = "The Account ID"
  type        = string
  default     = "058264215162"
}

variable "dynamodb_table" {
  description = "The name of DynamoDB Table for Lambda function"
  type        = string
  default     = "poli_fastapi_table_students"
}

variable "runtime" {
  description = "The runtime environment for the Lambda function"
  type        = string
  default     = "python3.12"
}

variable "handler" {
  description = "The function handler for the Lambda function"
  type        = string
  default     = "main.lambda_handler"
}

variable "memory_size" {
  description = "The amount of memory available to the function"
  type        = number
  default     = 128
}

variable "timeout" {
  description = "The amount of time that Lambda allows a function to run before stopping it"
  type        = number
  default     = 10
}

variable "api_gateway_stage" {
  description = "The stage name for the API Gateway"
  type        = string
  default     = "dev"
}

variable "env_vars" {
  description = "Environment variables for the Lambda function"
  type = map(string)
  default = {
    "REQUIRED_COLUMNS" = "value1"
    "ALL_COLUMNS" = "value2"
  }
}
