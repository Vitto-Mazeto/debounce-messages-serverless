variable "queue_name" {
  description = "The name of the SQS queue."
  type        = string
}

variable "delay_seconds" {
  description = "The time in seconds that the delivery of all messages in the queue will be delayed."
  type        = number
  default     = 0
}

variable "max_message_size" {
  description = "The maximum message size (in bytes) that can be sent to the queue."
  type        = number
  default     = 262144  # 256 KB, default limit for SQS
}

variable "message_retention_seconds" {
  description = "The length of time (in seconds) that the SQS queue retains a message."
  type        = number
  default     = 345600  # 4 days
}

variable "receive_wait_time_seconds" {
  description = "The duration (in seconds) for which the call waits for a message to arrive in the queue before returning."
  type        = number
  default     = 0
}

variable "tags" {
  description = "A map of tags to assign to the queue."
  type        = map(string)
  default     = {}
}
