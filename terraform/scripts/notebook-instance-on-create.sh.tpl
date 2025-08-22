#!/bin/bash

set -e

SECRET_NAME="sagemaker/${env}/deploy"
REGION="eu-west-2"
FILENAME="${env}_private_key"
SSH_DIR="/home/ec2-user/.ssh"

cd /home/ec2-user

echo "Getting Deploy Private Key..."
aws secretsmanager get-secret-value \
    --secret-id "$SECRET_NAME" \
    --region "$REGION" \
    --query SecretString \
    --output text > $FILENAME

mv $FILENAME "$SSH_DIR"

chmod 600 "$SSH_DIR/$FILENAME"

echo "Adding SSH Private Key..."
eval "$(ssh-agent -s)"

ssh-add "$SSH_DIR/$FILENAME"

echo "Configuring SSH for GitHub..."
echo "Host github.com" >> "$SSH_DIR/config"
echo "  HostName github.com" >> "$SSH_DIR/config"
echo "  IdentityFile $SSH_DIR/$FILENAME" >> "$SSH_DIR/config"
echo "  User git" >> "$SSH_DIR/config"

chmod 600 "$SSH_DIR/config"

ssh-keyscan -H github.com >> "$SSH_DIR/known_hosts"
chmod 644 "$SSH_DIR/known_hosts"

