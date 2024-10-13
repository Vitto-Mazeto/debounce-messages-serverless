resource "aws_sfn_state_machine" "whatsapp_debounce" {
  name     = "WhatsAppDebounce"
  role_arn = var.step_functions_role_arn

  definition = jsonencode({
    Comment = "WhatsApp Message Debounce Workflow"
    StartAt = "Wait 10 Seconds"
    States = {
      "Wait 10 Seconds" = {
        Type    = "Wait"
        Seconds = 10
        Next    = "Process Message"
      }
      "Process Message" = {
        Type     = "Task"
        Resource = var.process_message_lambda_arn
        InputPath = "$"
        End      = true
      }
    }
  })
}
