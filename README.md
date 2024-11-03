# Message Debouncer and Sender with Serverless Processing

## Overview

This project implements a serverless system on AWS for processing messages from various messaging tools (like WhatsApp, Telegram, and others) using a debounce mechanism. It leverages multiple AWS services, including Lambda, DynamoDB, API Gateway, and Step Functions, all orchestrated and provisioned using Terraform.

### Enhanced Gateway Functionality

The system serves as an enhanced gateway specifically designed for managing and processing messages from multiple applications. Unlike a standard proxy, which merely forwards requests and responses between clients and servers, this gateway is optimized for several key functionalities:

1. **Contextual Message Handling**: By using an `app_id`, the system identifies the source of incoming messages, ensuring they are routed to the correct Lambda functions. This contextual awareness allows for tailored processing logic depending on the application, leading to better handling of specific requirements.

2. **Debouncing Mechanism**: The system implements a debounce logic to aggregate messages received in quick succession from the same source. This not only optimizes resource usage by reducing the number of function invocations but also enhances the overall communication flow, making it more coherent and human-like.

3. **Dynamic Routing**: Instead of a fixed routing approach, this gateway can easily adapt to different applications by simply updating environment variables. When new applications are added, developers need only to include the new mappings in the environment configuration, making the system highly scalable and maintainable.

4. **Integration with AWS Services**: By leveraging AWS Lambda, DynamoDB, and Step Functions, the system seamlessly integrates multiple AWS capabilities, including storage, processing, and workflow management. This allows for a robust infrastructure that can handle complex message processing scenarios with minimal operational overhead.

5. **Simplified Webhook Management**: The system centralizes webhook management, allowing multiple applications to send messages to a single endpoint. It then takes care of the necessary routing and processing based on the provided `app_id`, simplifying integration for developers.

6. **Queue-Based Message Sending**: A new feature allows applications to send messages to the API through an SQS queue, enhancing the scalability of message processing. This mechanism enables messages to be sent back to the clients, which are typically the same ones that sent the messages being answered.

Overall, this enhanced gateway not only routes messages but also enriches the message processing experience, enabling effective communication management across various messaging platforms while minimizing latency and resource consumption.

## Motivation

While developing various integration solutions with messaging applications and LLMs, I noticed that receiving "choppy" messages — where the overall context of the request is fragmented across multiple messages — was a common issue. To address this, I created this project to concatenate messages received from the same number within a short time frame. This system batches received messages and processes them together, saving time and resources while providing a more coherent and human-like communication experience.

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
5. **SQS Queue**: Used to send messages to the API, enabling asynchronous processing.

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

### Processing Flow

1. The message is received by the `post_message` function.
   - This is what your messaging system should call.
2. The message is stored in DynamoDB.
3. A Step Function execution is initiated.
4. After 10 seconds, the `process_message` function is called to process the message.
   - If another message arrives for the same number before the 10 seconds are up, the debounce time is reset, and the previous message is concatenated.

### Queue-Based Message Sending

To send messages to the API via SQS, format the message in JSON as follows:

```json
{
  "app_id": "patricia",
  "phone_number": "5511996534923",
  "message_to_send": "Olá, da AWS"
}
```

#### Sending a Message

1. Use the SQS console or an SQS client to send a message formatted like above to the queue.
2. The `send_message_api` Lambda will then read the message from the queue and process it sending the message to the API.

### Query Parameter Requirement

To properly route messages to the right processing function, ensure that the `appId` query parameter is included in your webhook requests. This parameter allows the system to determine which application the message is coming from and to redirect it accordingly.

### Adding New Applications for Processing Webhook

To support additional applications, simply add their configuration to the environment variable map in your `process_message`. For example:

```json
PROCESSING_LAMBDAS_MAP = "{\"bot1\": \"bot1-chat-lambda\", \"app2\": \"blabla\"}"
```

This flexibility allows you to easily extend the system to handle new integrations without modifying the core processing logic.

### API_URLS_MAP Example (To send messages)

In the environment variables of your Lambda function, you can also define an `API_URLS_MAP` to map application IDs to their respective API endpoints. Here’s an example configuration:

```json
API_URLS_MAP = "{\"patricia\": \"https://api.z-api.io/instances/instance-id/token/token/send-text\", \"other_app\": \"https://api.example.com/other\"}"
```

This allows you to dynamically route processed messages to the correct API endpoint based on the `app_id` present in the incoming message.

### Processing Logic

The `process_message` function dynamically determines where to send the processed message based on environment variables configured in your lambda env variables. This map of possible Lambda functions based on `app_id` allows seamless redirection of messages to the appropriate processing logic.

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
    ├── post_message
    ├── send_message_api
    └── process_message
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
