#!/bin/bash

set -e

SECRET_NAME="sagemaker/dev/deploy"
REGION="eu-west-2"
FILENAME="dev_private_key"
SSH_DIR="/home/ec2-user/.ssh"

cd /home/ec2-user

echo "Getting Deploy Private Key..."
aws secretsmanager get-secret-value \
    --secret-id "$SECRET_NAME" \
    --region "$REGION" \
    --query SecretString \
    --output text > $FILENAME

mv $FILENAME "${SSH_DIR}"

chmod 600 "${SSH_DIR}/${FILENAME}"

echo "Adding SSH Private Key..."
eval "$(ssh-agent -s)"

ssh-add "${SSH_DIR}/${FILENAME}"
