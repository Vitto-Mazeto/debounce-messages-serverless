# Message Debouncer To Serverless Processing

## Overview

This project implements a serverless system on AWS for processing messages from WhatsApp (or other messaging tools such as Direct, Telegram, etc.) using a debounce mechanism. It leverages various AWS services, including Lambda, DynamoDB, API Gateway, and Step Functions, all orchestrated and provisioned using Terraform.

## Motivation

While developing various integration solutions with messaging applications, I noticed that receiving "choppy" messages - where the overall context of the request is fragmented across multiple messages - was a common issue. To address this, I created this project to concatenate messages received from the same number within a short time frame. This way, the system batches received messages and processes them together, saving time and resources while providing a more coherent and human-like communication experience.

### Problem

Different individuals have varying typing speeds, making a fixed debounce time of 10 seconds insufficient for slower typers. To resolve this, we could implement an adaptive debounce system that extends the waiting time as the user continues typing.

## Architecture

The system consists of the following components:

1. **DynamoDB**: Stores the received messages.
2. **Lambda Functions**:
   - `post_message`: Receives messages and initiates the debounce process.
   - `process_message`: Processes the messages after the debounce period.
3. **Step Functions**: Implements the debounce logic, waiting 10 seconds before processing the message.
4. **IAM Roles**: Manages the necessary permissions for the AWS services.

## Prerequisites

- [Terraform](https://www.terraform.io/downloads.html) (version 0.12+)
- [AWS CLI](https://aws.amazon.com/cli/) configured with your credentials
- [Python](https://www.python.org/downloads/) (version 3.11+)

## Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/your-username/message-debouncer-serverless.git
   cd message-debouncer-serverless
   ```

2. Prepare ZIP files for the Lambda functions:
   ```bash
   zip -j post_message.zip lambda/post_message.py
   zip -j process_message.zip lambda/process_message.py
   ```
   Alternatively, use the script in the `util` directory.

## Deploying

1. Initialize Terraform:
   ```bash
   terraform init
   ```

2. Review the planned changes:
   ```bash
   terraform plan
   ```

3. Apply the changes:
   ```bash
   terraform apply
   ```

4. Confirm by typing `yes` when prompted.

## Usage

After deployment, you will have an endpoint in **API Gateway** to receive messages. Use this endpoint to integrate with your messaging system on WhatsApp, Instagram, Telegram, etc.

The processing flow will be:
1. The message is received by the `post_message` function.
   - This is what your messaging system should call.
2. The message is stored in DynamoDB.
3. A Step Function execution is initiated.
4. After 10 seconds, the `process_message` function is called to process the message.
    - If another message arrives for the same number before the 10 seconds are up, the debounce time is reset, and the previous message is concatenated.

### Processing Logic

The `process_message` function can dynamically determine where to send the processed message based on environment variables configured in your `.env` file. 

- **Send to API or Another Lambda**: 
  - If the environment variable `SEND_TO_API` is set to `true`, the processed message will be sent to an external API specified by the `API_URL` environment variable.
  - If `SEND_TO_API` is not set to `true`, the message will be sent to another Lambda function specified by the `PROCESSING_LAMBDA_FUNCTION` environment variable.

This flexibility allows you to switch between processing options easily without altering the core logic of the Lambda functions.

## Project Structure

```
project/
├── main.tf                 # Main Terraform configuration
├── variables.tf            # Variable definitions
├── outputs.tf              # Terraform outputs
├── providers.tf            # AWS provider configuration
├── terraform.tfvars        # Variable values
├── modules/                # Terraform modules
│   ├── dynamodb/           # DynamoDB module
│   ├── api_gateway/        # API Gateway module
│   ├── lambda/             # Lambda functions module
│   └── step_functions/     # Step Functions module
└── lambda/                 # Source code for Lambda functions
    ├── post_message.py
    └── process_message.py
```

## Customization

- To modify the debounce time, change the `Seconds` value in the file `modules/step_functions/main.tf`.
- If you want to redirect to another processing function after receiving the concatenated message in `process_message`, update the code in `process_message.py`.

## Cleanup

To remove all created resources:

```bash
terraform destroy
```

Confirm by typing `yes` when prompted.

## Contributing

Contributions are welcome! Please open an issue to discuss major changes before submitting a pull request.

## License

This project is licensed under the [MIT License](LICENSE).
