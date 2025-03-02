#!/bin/bash

# Remove old files
rm -f lambda_function.zip

# Write all dependencies to requirements.txt
pip freeze > ./src/requirements.txt

# Install dependencies into the local directory
pip install -r ./src/requirements.txt -t ./src

# Package the application and dependencies into a ZIP file, excluding .venv
cd src
zip -r ../lambda_function.zip . -x "*.venv/*"
cd ..

# Upload the ZIP file to S3
aws s3 cp lambda_function.zip s3://poli-fastapi-lambda-layer-python200422022025/lambda_function.zip

echo "Lambda function repackaged and uploaded successfully."