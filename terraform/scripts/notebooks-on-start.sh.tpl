#!/bin/bash

# This script is based on approved AWS Sagemaker lifecycle configuration scripts found at
# https://github.com/aws-samples/amazon-sagemaker-notebook-instance-lifecycle-config-samples

set -e

# OVERVIEW
# This script:
#  - installs Polars in the python3 anaconda environment, which is the one used by our standard notebooks
#  - installs a Python script that stops the instance after it has been idle for an hour (or whatever time period)
#  - sets the PYTHONPATH environment variable in the python3 and base environments so that local code is accessible
#  - sets the ENV environment variable (e.g. "dev" or "prod") so that code interacts with the correct infrastructure.
#  - sets the git configuration for the ssh protocol
# Note this may timeout if the package installations in all environments take longer than 5 mins.

echo "STEP 1 - Installing Polars..."
sudo -u ec2-user -i <<'EOF'

source /home/ec2-user/anaconda3/bin/activate python3
conda install polars --name "python3" --yes
conda deactivate

EOF

set -ex

# Stops a SageMaker notebook once it's idle for more than 1 hour (default time)

# PARAMETERS
IDLE_TIME=3600

echo "STEP 2 - Installing the autostop script..."
aws s3 cp "s3://${bucket}/scripts/python/${env}/autostop.py" .

echo "Detecting Python install with boto3 install"

# Find which install has boto3 and use that to run the cron command. So will use default when available
# Redirect stderr as it is unneeded
CONDA_PYTHON_DIR=$(source /home/ec2-user/anaconda3/bin/activate /home/ec2-user/anaconda3/envs/JupyterSystemEnv && which python)
if $CONDA_PYTHON_DIR -c "import boto3" 2>/dev/null; then
    PYTHON_DIR=$CONDA_PYTHON_DIR
elif /usr/bin/python -c "import boto3" 2>/dev/null; then
    PYTHON_DIR='/usr/bin/python'
else
    # If no boto3 just quit because the script won't work
    echo "No boto3 found in Python or Python3. Exiting..."
    exit 1
fi

echo "Found boto3 at $PYTHON_DIR"


echo "Starting the SageMaker autostop script in cron"

(crontab -l 2>/dev/null; echo "*/5 * * * * $PYTHON_DIR $PWD/autostop.py --time $IDLE_TIME --ignore-connections >> /var/log/jupyter.log") | crontab -

# Setting environment variables

echo "STEP 3 - Getting and setting environment variables..."
VAR1=PYTHONPATH
VAR2=ENV

INSTANCE_ARN=$(jq '.ResourceArn' /opt/ml/metadata/resource-metadata.json --raw-output)
touch /etc/profile.d/jupyter-env.sh

# Get the environment variable values from the instance tags (defined in Terraform)
TAG1=$(aws sagemaker list-tags --resource-arn $INSTANCE_ARN | jq -r --arg VAR1 "$VAR1" .'Tags[] | select(.Key == $VAR1).Value' --raw-output)
TAG2=$(aws sagemaker list-tags --resource-arn $INSTANCE_ARN | jq -r --arg VAR2 "$VAR2" .'Tags[] | select(.Key == $VAR2).Value' --raw-output)

# Set variables in the Linux shell
echo "export $VAR1=$TAG1" >> /etc/profile.d/jupyter-env.sh
echo "export $VAR2=$TAG2" >> /etc/profile.d/jupyter-env.sh

ENV1="/home/ec2-user/anaconda3/envs/python3/etc/conda/activate.d/env_vars.sh"
ENV2="/home/ec2-user/anaconda3/etc/conda/activate.d/env_vars.sh"

# Setting in both the base and python3 conda environments
cat > $ENV1 << EOF
#!/bin/bash
export $VAR1=$TAG1
export $VAR2=$TAG2
EOF
chmod +x $ENV1

cat > $ENV2 << EOF
#!/bin/bash
export $VAR1=$TAG1
export $VAR2=$TAG2
EOF
chmod +x $ENV2

echo "Step 4 - Setting the GitHub credentials..."
# Set the deploy key
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
echo "  StrictHostKeyChecking no" >> "$SSH_DIR/config"
echo "  UserKnownHostsFile /dev/null" >> "$SSH_DIR/config"
echo "  User git" >> "$SSH_DIR/config"

chmod 600 "$SSH_DIR/config"

echo "Setting the git remote url..."

# Set the git remote url, checking first that the directory exists.

ELAPSED_TIME=0
TIMEOUT=120
CHECK_INTERVAL=5
REPO_ROOT="/home/ec2-user/SageMaker/MachineLearningModels"

while [ "$ELAPSED_TIME" -lt "$TIMEOUT" ]; do

    if [ -d "$REPO_ROOT" ]; then
        echo "Directory $REPO_ROOT exists."
        cd $REPO_ROOT
        git remote set-url origin git@github.com:NMDSdevopsServiceAdm/MachineLearningModels.git
        echo "Git remote updated."
        break
    fi

    echo "Directory not found yet. Checking again in $CHECK_INTERVAL seconds..."
    sleep "$CHECK_INTERVAL"

    # Increment the elapsed time counter.
    ELAPSED_TIME=$((ELAPSED_TIME + CHECK_INTERVAL))

done
