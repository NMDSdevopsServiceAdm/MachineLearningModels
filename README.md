# MachineLearningModels

This repository contains the code required to run, train and deploy machine learning models used by the Skills For Care
data team on AWS SageMaker.

The main components are:
- Jupyter notebooks containing the model build and training code
- Python utility code used by the notebooks
- Terraform code defining the instances used to run the notebooks

## Notebook development
To edit existing notebooks, or create new ones, you should work directly on the notebooks through the notebook instances.

1. Sign in the Skills For Care Data Team AWS account.
2. Select SageMaker AI.
3. Select Notebooks.
4. Select "dev-modes-notebook" and then Actions -> Start.
5. When the instance is ready, click "Open JupyterLab" Under "Actions". The notebook server will open a new browser tab.
6. In the "notebooks" folder, select the notebook you want to edit, or create a new one using the File menu.
7. See the Confluence documentation for details on model construction, training and deployment.
8. Changes can be committed and pushed using the Git UI included on the browser page.

All changes should be prototyped first on the dev instance, then pushed to the dev branch of the repository. After a 
pull request, the new code will be merged to main, from where it can be pulled to run live on the production notebook
instance.

## Python or Terraform development


