# fastapi-lambda/README.md

# FastAPI AWS Lambda Deployment

This project deploys a FastAPI application to AWS Lambda using Terraform. The FastAPI application provides endpoints to retrieve student information.

## Project Structure

```
terraform-fastapi-lambda
├── src
│   ├── main.py          # FastAPI application code
│   └── requirements.txt  # Python dependencies
├── main.tf              # Terraform configuration for AWS resources
├── variables.tf         # Input variables for Terraform
├── outputs.tf           # Outputs from Terraform deployment
└── README.md            # Project documentation
```

## Prerequisites

- AWS Account
- Terraform installed
- Python 3.x installed

## Setup Instructions

1. Clone the repository:

   ```
   git clone <repository-url>
   cd terraform-fastapi-lambda
   ```

2. Navigate to the `src` directory and install the required Python packages:

   ```
   pip install -r requirements.txt
   ```

3. Configure your AWS credentials. You can do this by setting up the AWS CLI or by exporting environment variables:

   ```
   export AWS_ACCESS_KEY_ID=<your-access-key>
   export AWS_SECRET_ACCESS_KEY=<your-secret-key>
   export AWS_DEFAULT_REGION=<your-region>
   ```

## Deployment Steps

1. Initialize Terraform:

   ```
   terraform init
   ```

2. Plan the deployment:

   ```
   terraform plan
   ```

3. Apply the configuration to deploy the FastAPI application:

   ```
   terraform apply
   ```

4. After deployment, Terraform will output the API Gateway endpoint URL. You can use this URL to access your FastAPI application.

## Usage

You can access the FastAPI application using the provided API Gateway endpoint. For example:

```
GET <api-gateway-endpoint>/alunos
GET <api-gateway-endpoint>/alunos/{aluno_id}
```

## Cleanup

To remove the deployed resources, run:

```
terraform destroy
```

## License

This project is licensed under the MIT License.