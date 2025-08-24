#!/bin/bash

# This script is based on approved AWS Sagemaker lifecycle configuration scripts found at
# https://github.com/aws-samples/amazon-sagemaker-notebook-instance-lifecycle-config-samples

set -e

# OVERVIEW
# This script installs a single pip package in all SageMaker conda environments, apart from the JupyterSystemEnv which
# is a system environment reserved for Jupyter.
# Note this may timeout if the package installations in all environments take longer than 5 mins, consider using
# "nohup" to run this as a background process in that case.

sudo -u ec2-user -i <<'EOF'

conda install polars --name base --yes

# Note that "base" is special environment name, include it there as well.
for env in base /home/ec2-user/anaconda3/envs/*; do
    source /home/ec2-user/anaconda3/bin/activate $(basename "$env")
    env_name=$(basename "$env")

    if [ $env = 'JupyterSystemEnv' ]; then
        continue
    fi

    # pip install --upgrade polars
    conda install polars --name "$env_name" --yes

    source /home/ec2-user/anaconda3/bin/deactivate
done

EOF


set -ex
# OVERVIEW
# This script stops a SageMaker notebook once it's idle for more than 1 hour (default time)
# You can change the idle time for stop using the environment variable below.
# If you want the notebook the stop only if no browsers are open, remove the --ignore-connections flag
#
# Note that this script will fail if either condition is not met
#   1. Ensure the Notebook Instance has internet connectivity to fetch the example config
#   2. Ensure the Notebook Instance execution role permissions to SageMaker:StopNotebookInstance to stop the notebook 
#       and SageMaker:DescribeNotebookInstance to describe the notebook.
#

# PARAMETERS
IDLE_TIME=3600

echo "Fetching the autostop script"
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

REPO_ROOT="/home/ec2-user/SageMaker/MachineLearningModels"

VAR1=PYTHONPATH
VAR2=ENV

INSTANCE_ARN=$(jq '.ResourceArn' /opt/ml/metadata/resource-metadata.json --raw-output)
touch /etc/profile.d/jupyter-env.sh

TAG1=$(aws sagemaker list-tags --resource-arn $NOTEBOOK_ARN | jq -r --arg VAR1 "$VAR1" .'Tags[] | select(.Key == $VAR1).Value' --raw-output)
TAG2=$(aws sagemaker list-tags --resource-arn $NOTEBOOK_ARN | jq -r --arg VAR2 "$VAR2" .'Tags[] | select(.Key == $VAR2).Value' --raw-output)

echo "export $VAR1=$TAG1" >> /etc/profile.d/jupyter-env.sh
echo "export $VAR2=$TAG2" >> /etc/profile.d/jupyter-env.sh



