provider "aws" {
  region = var.aws_region
}

resource "aws_lambda_function" "fastapi_lambda" {
  function_name = var.function_name
  runtime       = var.runtime
  handler       = var.handler
  memory_size   = var.memory_size
  timeout       = var.timeout

  s3_bucket        = "poli-fastapi-lambda-layer-python200422022025"
  s3_key           = "lambda_function.zip"
  source_code_hash = filebase64sha256("lambda_function.zip")

  role = aws_iam_role.lambda_exec.arn

  environment {
    variables = var.env_vars
  }
}

resource "aws_iam_policy" "lambda_dynamodb_policy" {
  name = "fastapi_lambda_dynamodb_policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem"
        ]
        Effect = "Allow"
        Resource = "arn:aws:dynamodb:${var.aws_region}:${var.account_id}:table/${var.dynamodb_table}"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_dynamodb_policy_attachment" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.lambda_dynamodb_policy.arn
}

resource "aws_iam_role" "lambda_exec" {
  name = "lambda_exec_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_policy" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_api_gateway_rest_api" "fastapi_api" {
  name        = "fastapi_api"
  description = "API Gateway for FastAPI application"
}

resource "aws_api_gateway_resource" "proxy" {
  rest_api_id = aws_api_gateway_rest_api.fastapi_api.id
  parent_id   = aws_api_gateway_rest_api.fastapi_api.root_resource_id
  path_part   = "{proxy+}"
}

resource "aws_api_gateway_method" "proxy_method" {
  rest_api_id   = aws_api_gateway_rest_api.fastapi_api.id
  resource_id   = aws_api_gateway_resource.proxy.id
  http_method   = "ANY"
  authorization = "NONE"

  request_parameters = {
    "method.request.header.Content-Type" = true
  }
}

resource "aws_api_gateway_integration" "lambda_integration" {
  rest_api_id = aws_api_gateway_rest_api.fastapi_api.id
  resource_id = aws_api_gateway_resource.proxy.id
  http_method = aws_api_gateway_method.proxy_method.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.fastapi_lambda.invoke_arn

  request_parameters = {
    "integration.request.header.Content-Type" = "method.request.header.Content-Type"
  }

  passthrough_behavior = "WHEN_NO_MATCH"
}

resource "aws_api_gateway_deployment" "fastapi_deployment" {
  depends_on = [
    aws_api_gateway_integration.lambda_integration
  ]

  rest_api_id = aws_api_gateway_rest_api.fastapi_api.id
  stage_name  = var.api_gateway_stage
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.fastapi_lambda.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.fastapi_api.execution_arn}/*/*"
}
