provider "aws" {
  region = "us-east-1"
}

# ----------------------------------------
# Criação de Recursos
# ----------------------------------------

# Cria a tabela DynamoDB para received_messages
module "dynamodb_received_messages" {
  source        = "./modules/dynamodb"
  table_name    = "received_messages"
  hash_key_name = "phone_number"
  hash_key_type = "S"
}

# ----------------------------------------
# IAM Roles e Permissões
# ----------------------------------------

# Cria a role IAM para as Lambdas
resource "aws_iam_role" "lambda_role" {
  name = "lambda_execution_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      Effect = "Allow"
      Sid    = ""
    }]
  })
}

# Anexa políticas gerenciadas amplas à role
resource "aws_iam_role_policy_attachment" "lambda_full_access_s3" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
  role       = aws_iam_role.lambda_role.name

  depends_on = [aws_iam_role.lambda_role]
}

resource "aws_iam_role_policy_attachment" "lambda_full_access_dynamodb" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
  role       = aws_iam_role.lambda_role.name

  depends_on = [aws_iam_role.lambda_role]
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.lambda_role.name

  depends_on = [aws_iam_role.lambda_role]
}

resource "aws_iam_role_policy_attachment" "lambda_step_functions" {
  policy_arn = "arn:aws:iam::aws:policy/AWSStepFunctionsFullAccess"
  role       = aws_iam_role.lambda_role.name

  depends_on = [aws_iam_role.lambda_role]
}

# Role para Step Functions
resource "aws_iam_role" "step_functions_role" {
  name = "step_functions_execution_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Principal = {
        Service = "states.amazonaws.com"
      }
      Effect = "Allow"
      Sid    = ""
    }]
  })
}

# Anexa a política à role, permitindo step functions invocar Lambdas
resource "aws_iam_role_policy" "step_functions_policy" {
  role = aws_iam_role.step_functions_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = "*"
      }
    ]
  })
}

# ----------------------------------------
# Criação de Lambdas
# ----------------------------------------

# Cria a Lambda de post message
module "lambda_post_message" {
  source        = "./modules/lambda"
  function_name = "post_message"
  role_arn      = aws_iam_role.lambda_role.arn
  zip_file      = "./deployments/post_message.zip"
  layers        = []
  environment_variables = {
    STEP_FUNCTION_ARN = module.step_function_whatsapp_debounce.state_machine_arn
    DYNAMODB_TABLE    = module.dynamodb_received_messages.table_name
  }
  create_api_gw        = true
  api_gw_execution_arn = aws_apigatewayv2_api.http_api.execution_arn
}

# Cria a Lambda de process message
module "lambda_process_message" {
  source        = "./modules/lambda"
  function_name = "process_message"
  role_arn      = aws_iam_role.lambda_role.arn
  zip_file      = "./deployments/process_message.zip"
  layers        = []
  environment_variables = {
    DYNAMODB_TABLE = module.dynamodb_received_messages.table_name
  }
}

# ----------------------------------------
# Step Functions
# ----------------------------------------

# Cria a step function
module "step_function_whatsapp_debounce" {
  source                     = "./modules/step_functions"
  step_functions_role_arn    = aws_iam_role.step_functions_role.arn
  process_message_lambda_arn = module.lambda_process_message.lambda_invoke_arn
}

# ----------------------------------------
# API Gateway
# ----------------------------------------

# Cria o API Gateway
resource "aws_apigatewayv2_api" "http_api" {
  name          = "http-api-whatsapp"
  protocol_type = "HTTP"
}

# Stage da API
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http_api.id
  name        = "$default"
  auto_deploy = true
}

# Configura os endpoints do API Gateway
module "api_gateway_post_message" {
  source            = "./modules/api_gateway"
  api_id            = aws_apigatewayv2_api.http_api.id
  method            = "POST"
  path              = "/post-message"
  lambda_invoke_arn = module.lambda_post_message.lambda_invoke_arn
}
