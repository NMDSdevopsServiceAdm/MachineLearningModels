#!/bin/bash

set -e

SECRET_NAME="sagemaker/${env}/deploy"
REGION="eu-west-2"
KEYFILE_PATH="~/.ssh/${env}_private_key"

cd /home/ec2-user

echo "Getting Deploy Private Key..."
aws secretsmanager get-secret-value \
    --secret-id "$SECRET_NAME" \
    --region "$REGION" \
    --query SecretString \
    --output text > $KEYFILE_PATH

chmod 600 $KEYFILE_PATH

echo "Adding SSH Private Key..."
eval "$(ssh-agent -s)"

ssh-add $KEYFILE_PATH
