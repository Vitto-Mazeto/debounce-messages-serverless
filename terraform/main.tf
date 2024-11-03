provider "aws" {
  region = "us-east-1"
}

# ----------------------------------------
# Criação de Recursos
# ----------------------------------------

# Cria a tabela DynamoDB para received_messages
module "dynamodb_received_messages" {
  source           = "./modules/dynamodb"
  table_name       = "debouncer_received_messages"
  hash_key_name    = "app_id"
  hash_key_type    = "S"
  range_key_name   = "phone_number"
  range_key_type   = "S"
}

# Cria a fila SQS para envio de mensagens
module "sqs_queue" {
  source                  = "./modules/sqs"
  queue_name              = "debouncer_send_message_queue"
  delay_seconds           = 0
  max_message_size        = 262144  # 256 KB
  message_retention_seconds = 86400  # 1 dia
  receive_wait_time_seconds = 0
}

# ----------------------------------------
# IAM Roles e Permissões
# ----------------------------------------

# Cria a role IAM para as Lambdas
resource "aws_iam_role" "lambda_role" {
  name = "debouncer_lambda_execution_role"
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

resource "aws_iam_role_policy_attachment" "lambda_full_access" {
  policy_arn = "arn:aws:iam::aws:policy/AWSLambda_FullAccess"
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

# Policy para SQS
resource "aws_iam_policy" "lambda_sqs_access" {
  name        = "LambdaSQSAcessPolicy"
  description = "Policy that allows Lambda to access SQS"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
        ]
        Effect   = "Allow"
        Resource = module.sqs_queue.queue_arn
      }
    ]
  })
}

# Anexa a política SQS ao papel da Lambda
resource "aws_iam_role_policy_attachment" "lambda_sqs_access" {
  policy_arn = aws_iam_policy.lambda_sqs_access.arn
  role       = aws_iam_role.lambda_role.name

  depends_on = [aws_iam_role.lambda_role]
}

resource "aws_lambda_permission" "allow_sqs" {
  statement_id  = "AllowSQSTrigger"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda_send_message_api.lambda_arn
  principal     = "sqs.amazonaws.com"
  source_arn    = module.sqs_queue.queue_arn
}

# ----------------------------------------
# Criação de Lambdas
# ----------------------------------------

# Cria a Lambda de post message
module "lambda_post_message" {
  source        = "./modules/lambda"
  function_name = "debouncer_post_message"
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
  function_name = "debouncer_process_message"
  role_arn      = aws_iam_role.lambda_role.arn
  zip_file      = "./deployments/process_message.zip"
  layers        = []
  environment_variables = {
    DYNAMODB_TABLE = module.dynamodb_received_messages.table_name
    PROCESSING_LAMBDAS_MAP = "{\"patricia\": \"patricia-chat-lambda\", \"app2\": \"blabla\"}"
  }
}

# Creates the lambda that send the messages to the APIs (WhatsApp, Telegram, etc)
module "lambda_send_message_api" {
  source        = "./modules/lambda"
  function_name = "debouncer_send_message_api"
  role_arn      = aws_iam_role.lambda_role.arn
  zip_file      = "./deployments/send_message_api.zip"
  # Use Klayers for requests https://github.com/keithrozario/Klayers
  layers        = ["arn:aws:lambda:us-east-1:770693421928:layer:Klayers-p311-requests:12"]
  environment_variables = {
    CLIENT_TOKEN = var.client_token,
    API_URLS_MAP = var.api_urls_map
  }
}

resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn = module.sqs_queue.queue_arn
  function_name    = module.lambda_send_message_api.lambda_arn
  batch_size       = 10
  enabled          = true
}

# ----------------------------------------
# Step Functions
# ----------------------------------------

# Cria a step function
module "step_function_whatsapp_debounce" {
  source                     = "./modules/step_functions"
  step_functions_role_arn    = aws_iam_role.step_functions_role.arn
  process_message_lambda_arn = module.lambda_process_message.lambda_arn
}

# ----------------------------------------
# API Gateway
# ----------------------------------------

# Cria o API Gateway
resource "aws_apigatewayv2_api" "http_api" {
  name          = "debouncer-http-api-whatsapp"
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
  path              = "/debouncer-post-message"
  lambda_invoke_arn = module.lambda_post_message.lambda_invoke_arn
}
