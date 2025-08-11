
# PROD (main) resources
resource "aws_sagemaker_notebook_instance" "models_notebook_prod" {
  name                  = "main-models-notebook"
  role_arn              = aws_iam_role.sagemaker_execution_role_prod.arn
  instance_type         = "ml.t3.medium"
  volume_size           = 5
  lifecycle_config_name = aws_sagemaker_notebook_instance_lifecycle_configuration.models_lifecycle_prod.name

  default_code_repository = aws_sagemaker_code_repository.models_repo_prod.id
}

resource "aws_sagemaker_code_repository" "models_repo_prod" {
  code_repository_name = "main-models-github-repository"

  git_config {
    repository_url = var.github_repository_url
    branch         = "main"
  }
}

resource "aws_sagemaker_notebook_instance_lifecycle_configuration" "models_lifecycle_prod" {
  name     = "main-models-lifecycle"
  on_start = filebase64("scripts/notebooks-on-start.sh")
}

resource "aws_iam_role" "sagemaker_execution_role_prod" {
  name = "main-sagemaker-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "sagemaker.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_policy" "sagemaker_full_access_policy_prod" {
  name   = "main-sagemaker-full-access-policy"
  policy = templatefile("policy-documents/sagemaker-notebooks-prod.json", { account_id = data.aws_caller_identity.current.account_id })
}

resource "aws_iam_role_policy_attachment" "sagemaker_full_access" {
  role       = aws_iam_role.sagemaker_execution_role_prod.name
  policy_arn = aws_iam_policy.sagemaker_full_access_policy_prod.arn
}


# DEV (default) resources
resource "aws_sagemaker_notebook_instance" "models_notebook_dev" {
  name                  = "default-models-notebook"
  role_arn              = aws_iam_role.sagemaker_execution_role_dev.arn
  instance_type         = "ml.t3.medium"
  volume_size           = 5
  lifecycle_config_name = aws_sagemaker_notebook_instance_lifecycle_configuration.models_lifecycle_dev.name

  default_code_repository = aws_sagemaker_code_repository.models_repo_dev.id
}

resource "aws_sagemaker_code_repository" "models_repo_dev" {
  code_repository_name = "default-models-github-repository"

  git_config {
    repository_url = var.github_repository_url
    branch         = local.workspace_prefix
  }
}

resource "aws_sagemaker_notebook_instance_lifecycle_configuration" "models_lifecycle_dev" {
  name     = "default-models-lifecycle"
  on_start = filebase64("scripts/notebooks-on-start.sh")
}

resource "aws_iam_role" "sagemaker_execution_role_dev" {
  name = "default-sagemaker-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "sagemaker.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_policy" "sagemaker_full_access_policy_dev" {
  name   = "default-sagemaker-full-access-policy"
  policy = templatefile("policy-documents/sagemaker-notebooks-dev.json", { account_id = data.aws_caller_identity.current.account_id })
}

resource "aws_iam_role_policy_attachment" "sagemaker_full_access_dev" {
  role       = aws_iam_role.sagemaker_execution_role_dev.name
  policy_arn = aws_iam_policy.sagemaker_full_access_policy_dev.arn
}

