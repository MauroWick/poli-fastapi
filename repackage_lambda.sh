#!/bin/bash

# Remove old files
rm -f lambda_function.zip
rm -f lambda_layer.zip
rm -rf lambda_layer/python/*

# Write all dependencies to requirements.txt
pip freeze > ./src/requirements.txt

# Install dependencies into the local directory
pip install -r ./src/requirements.txt -t ./lambda_layer/python

# Package the dependencies into a ZIP file
cd lambda_layer
zip -r ../lambda_layer.zip .
cd ..

# Package the application into a ZIP file, excluding .venv
cd src
zip -r ../lambda_function.zip . -x "*.venv/*"
cd ..

# Upload the ZIP files to S3
aws s3 cp lambda_layer.zip s3://poli-fastapi-lambda-layer-python200422022025/lambda_layer.zip
aws s3 cp lambda_function.zip s3://poli-fastapi-lambda-layer-python200422022025/lambda_function.zip

echo "Lambda function and layer repackaged and uploaded successfully."