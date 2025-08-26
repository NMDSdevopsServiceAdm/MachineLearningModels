# MachineLearningModels

This repository contains the code required to run, train and deploy machine learning models used by the Skills For Care
data team on AWS SageMaker.

The main components are:
- Jupyter notebooks containing the model build and training code
- Python utility code used by the notebooks
- Terraform code defining the instances used to run the notebooks

The CI/CD process is run in Circle CI.

- Pushes to all branches are checked for unit tests and coverage (_pytest_), security (_pip-audit_ and _bandit_),
formatting (_black_), type safety (_mypy_), docstring validation (_pydoclint_) and Terraform validity.
- Pushes to branches other than `dev` or `prod` are planned by Terraform but not applied.
- Pushes or merges to `dev` result in a Terraform build of the `dev` instance (after approval).
- Pushes or merges to `main` result in a Terraform build of the `prod` instance (after approval).

## Notebook development
To edit existing notebooks, or create new ones, you should work directly on the notebooks through the notebook instances.

1. Sign in the Skills For Care Data Team AWS account.
2. Select SageMaker AI.
3. Select Notebooks.
4. Select `dev-models-notebook` and then Actions -> Start.
5. When the instance is ready, click "Open JupyterLab" Under "Actions". The notebook server will open a new browser tab.
6. In the "notebooks" folder, select the notebook you want to edit, or create a new one using the File menu.
7. See the [Confluence documentation](https://skillsforcare.atlassian.net/wiki/spaces/DE/pages/1517682694/Sagemaker+Polars+ML+Models)
for details on model construction, training and deployment.
8. Changes can be committed and pushed using the Git UI included on the browser page.

All changes should be prototyped first on the `dev` instance, then pushed to the `dev` branch of the repository. After a 
pull request, the new code will be merged to `main`, from where it can be pulled to run live on the production notebook
instance.

Notebooks have access to an environment variable called `ENV`, which will be either "dev" or "prod" as appropriate. This
allows users to write code that adapts to the instance - for example, specify a different S3 bucket for each instance:
```python
env = os.environ['ENV']
S3_BUCKET = f'my-model-repository-{env}'
```

## Python or Terraform development
Changes to the Python utility functions or the Terraform code should be made on a new branch from your local machine. 
The intended workflow is then to push the code to the new branch in GitHub, ensuring that all tests pass in CircleCI.
Then, pull request to the `dev` branch. This will trigger a redeployment of the `dev` instance. When you have tested
that the changes have worked correctly on the redeployed `dev` instance, then pull request and merge the `dev` branch 
into `main`. That will trigger the deployment of the `prod` instance with the new code.

## Local development
To develop the project locally, you will need [pipenv](https://pipenv.pypa.io/en/latest/index.html) installed. Then:
1. Clone this repository.
2. Run `pipenv install` to set up the project.
3. If using a Unix-like operating system, check the tests are passing using the utility script: `./run_checks.sh`. 
If not, you can run individual tests using individual commands (listed below).
4. As noted above, create a new branch for changes.

## Tests
The following tests are standard:
1. Unit tests and coverage: `pipenv run pytest -vrrP --cov`
2. Type checking: `pipenv run mypy --follow-untyped-imports utilities`
3. Formatting: `pipenv run black . --check`
4. Docstrings: `pipenv run pydoclint --style=google --quiet .`
5. Dependency checks: `pipenv run pip-audit`
6. Code vulnerability check: `pipenv run bandit -c bandit.yaml -r utilities`
7. You can also do Terraform checks using the `terraform fmt` and `terraform validate` commands.



