
# PROD (main) resources
resource "aws_sagemaker_notebook_instance" "models_notebook" {
  name                  = "main-models-notebook"
  role_arn              = aws_iam_role.sagemaker_execution_role.arn
  instance_type         = "ml.t3.medium"
  volume_size           = 5
  lifecycle_config_name = aws_sagemaker_notebook_instance_lifecycle_configuration.models_lifecycle.name

  default_code_repository = aws_sagemaker_code_repository.models_repo.id
}

resource "aws_sagemaker_code_repository" "models_repo" {
  code_repository_name = "main-models-github-repository"

  git_config {
    repository_url = var.github_repository_url
    branch         = "main"
  }
}

resource "aws_sagemaker_notebook_instance_lifecycle_configuration" "models_lifecycle" {
  name     = "main-models-lifecycle"
  on_start = filebase64("scripts/notebooks-on-start.sh")
}

resource "aws_iam_role" "sagemaker_execution_role" {
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

resource "aws_iam_policy" "sagemaker_full_access_policy" {
  name   = "main-sagemaker-full-access-policy"
  policy = templatefile("policy-documents/sagemaker-notebooks-prod.json", { account_id = data.aws_caller_identity.current.account_id })
}

resource "aws_iam_role_policy_attachment" "sagemaker_full_access" {
  role       = aws_iam_role.sagemaker_execution_role.name
  policy_arn = aws_iam_policy.sagemaker_full_access_policy.arn
}


# DEV (default) resources
resource "aws_sagemaker_notebook_instance" "models_notebook" {
  name                  = "default-models-notebook"
  role_arn              = aws_iam_role.sagemaker_execution_role.arn
  instance_type         = "ml.t3.medium"
  volume_size           = 5
  lifecycle_config_name = aws_sagemaker_notebook_instance_lifecycle_configuration.models_lifecycle.name

  default_code_repository = aws_sagemaker_code_repository.models_repo.id
}

resource "aws_sagemaker_code_repository" "models_repo" {
  code_repository_name = "default-models-github-repository"

  git_config {
    repository_url = var.github_repository_url
    branch         = local.workspace_prefix
  }
}

resource "aws_sagemaker_notebook_instance_lifecycle_configuration" "models_lifecycle" {
  name     = "default-models-lifecycle"
  on_start = filebase64("scripts/notebooks-on-start.sh")
}

resource "aws_iam_role" "sagemaker_execution_role" {
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

resource "aws_iam_policy" "sagemaker_full_access_policy" {
  name   = "default-sagemaker-full-access-policy"
  policy = templatefile("policy-documents/sagemaker-notebooks-dev.json", { account_id = data.aws_caller_identity.current.account_id })
}

resource "aws_iam_role_policy_attachment" "sagemaker_full_access" {
  role       = aws_iam_role.sagemaker_execution_role.name
  policy_arn = aws_iam_policy.sagemaker_full_access_policy.arn
}

