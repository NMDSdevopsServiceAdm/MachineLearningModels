resource "aws_sagemaker_notebook_instance" "models_notebook" {
  name                  = "${local.workspace_prefix}-models-notebook"
  role_arn              = aws_iam_role.sagemaker_execution_role.arn
  instance_type         = "ml.t3.medium"
  volume_size           = 5
  lifecycle_config_name = aws_sagemaker_notebook_instance_lifecycle_configuration.models_lifecycle.name

  default_code_repository = aws_sagemaker_code_repository.models_repo.id
}

resource "aws_sagemaker_code_repository" "models_repo" {
  code_repository_name = "${local.workspace_prefix}-models-github-repository"

  git_config {
    repository_url = var.github_repository_url
    branch         = local.workspace_prefix
  }
}

resource "aws_sagemaker_notebook_instance_lifecycle_configuration" "models_lifecycle" {
  name     = "${local.workspace_prefix}-models-lifecycle"
  on_start = filebase64(templatefile("scripts/notebooks-on-start.sh", {workspace_prefix = "${local.workspace_prefix}"}))
}

resource "aws_iam_role" "sagemaker_execution_role" {
  name = "${local.workspace_prefix}-sagemaker-execution-role"

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

# may need more frorm here: https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-roles.html#sagemaker-roles-createnotebookinstance-perms
resource "aws_iam_policy" "sagemaker_full_access_policy" {
  name   = "${local.workspace_prefix}-sagemaker-full-access-policy"
  policy = templatefile("policy-documents/sagemaker-notebooks.json", { account_id = data.aws_caller_identity.current.account_id })
}

resource "aws_iam_role_policy_attachment" "sagemaker_full_access" {
  role       = aws_iam_role.sagemaker_execution_role.name
  policy_arn = aws_iam_policy.sagemaker_full_access_policy.arn
}
