# Message Debouncer To Serverless Processing

## Visão Geral

Este projeto implementa um sistema serverless na AWS para processar mensagens do WhatsApp (ou outras ferramentas de mensagem ex: Direct, Telegram, ...) com um mecanismo de debounce. Ele utiliza diversos serviços da AWS, incluindo Lambda, DynamoDB, API Gateway e Step Functions, todos orquestrados e provisionados usando Terraform.

## Arquitetura

O sistema é composto pelos seguintes componentes:

1. **DynamoDB**: Armazena as mensagens recebidas.
2. **Lambda Functions**:
   - `post_message`: Recebe mensagens e inicia o processo de debounce.
   - `process_message`: Processa as mensagens após o período de debounce.
3. **Step Functions**: Implementa a lógica de debounce, esperando 10 segundos antes de processar a mensagem.
4. **IAM Roles**: Gerencia as permissões necessárias para os serviços da AWS.

## Pré-requisitos

- [Terraform](https://www.terraform.io/downloads.html) (versão 0.12+)
- [AWS CLI](https://aws.amazon.com/cli/) configurado com suas credenciais
- [Python](https://www.python.org/downloads/) (versão 3.11+)

## Configuração

1. Clone este repositório:
   ```
   git clone https://github.com/seu-usuario/message-debouncer-serverless.git
   cd message-debouncer-serverless
   ```

2. Prepare os arquivos ZIP para as funções Lambda:
   ```
   zip -j post_message.zip lambda/post_message.py
   zip -j process_message.zip lambda/process_message.py
   ```
   Ou use o script da pasta 'util'.

## Deploying

1. Inicialize o Terraform:
   ```
   terraform init
   ```

2. Revise as mudanças planejadas:
   ```
   terraform plan
   ```

3. Aplique as mudanças:
   ```
   terraform apply
   ```

4. Confirme digitando `yes` quando solicitado.

## Uso

Após o deploy, você terá um endpoint no **API Gateway** para receber mensagens. Use este endpoint para integrar com o seu sistema de mensagens do WhatsApp, Instagram, Telegram, ...

O fluxo de processamento será:
1. A mensagem é recebida pela função `post_message`.
   - É o que deverá ser chamado pelo seu sistema de mensagens.
2. A mensagem é armazenada no DynamoDB.
3. Uma execução do Step Function é iniciada.
4. Após 10 segundos, a função `process_message` é chamada para processar a mensagem.
    - Caso chegue outra mensagem para o mesmo número antes dos 10 segundos, o tempo de debounce é reiniciado. E a mensagem anterior é concatenada.

## Estrutura do Projeto

```
project/
├── main.tf                 # Configuração principal do Terraform
├── variables.tf            # Definição de variáveis
├── outputs.tf              # Outputs do Terraform
├── providers.tf            # Configuração do provider AWS
├── terraform.tfvars        # Valores das variáveis
├── modules/                # Módulos Terraform
│   ├── dynamodb/           # Módulo para o DynamoDB
│   ├── api_gateway/        # Módulo para o API Gateway
│   ├── lambda/             # Módulo para funções Lambda
│   └── step_functions/     # Módulo para Step Functions
└── lambda/                 # Código fonte das funções Lambda
    ├── post_message.py
    └── process_message.py
```

## Customização

- Para modificar o tempo de debounce, altere o valor `Seconds` no arquivo `modules/step_functions/main.tf`.
- Caso queria redirecionar para outro processamento após receber a mensagem já concatenada no process_message, altere o código da função `process_message.py`.

## Limpeza

Para remover todos os recursos criados:

```
terraform destroy
```

Confirme digitando `yes` quando solicitado.

## Contribuindo

Contribuições são bem-vindas! Por favor, abra uma issue para discutir mudanças maiores antes de submeter um pull request.

## Licença

Este projeto está licenciado sob a [MIT License](LICENSE).