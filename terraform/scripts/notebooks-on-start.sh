#!/bin/bash

set -e

# OVERVIEW
# This script gets value from Notebook Instance's tag and sets it as environment
# variable for all process including Jupyter in SageMaker Notebook Instance
# Note that this script will fail this condition is not met
#   1. Ensure the Notebook Instance execution role has permission of SageMaker:ListTags
#

sudo -u ec2-user -i <<'EOF'

touch /etc/profile.d/jupyter-env.sh
echo "export MODELS_BUCKET=${workspace_prefix}-pipeline-resources" >> /etc/profile.d/jupyter-env.sh

# restart command is dependent on current running Amazon Linux and JupyterLab
CURR_VERSION=$(cat /etc/os-release)
if [[ $CURR_VERSION == *$"http://aws.amazon.com/amazon-linux-ami/"* ]]; then
	sudo initctl restart jupyter-server --no-wait
else
	sudo systemctl --no-block restart jupyter-server.service
fi

EOF


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

    export MODELS_BUCKET_2=${workspace_prefix}-pipeline-resources

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
wget https://raw.githubusercontent.com/aws-samples/amazon-sagemaker-notebook-instance-lifecycle-config-samples/master/scripts/auto-stop-idle/autostop.py
# TODO: point to self once merging into main
# wget https://raw.githubusercontent.com/NMDSdevopsServiceAdm/MachineLearningModels/tree/main/terraform/scripts/autostop.py

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
