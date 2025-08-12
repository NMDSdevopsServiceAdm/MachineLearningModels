resource "aws_sagemaker_notebook_instance" "models_notebook" {
  for_each              = var.env
  name                  = "${each.key}-models-notebook"
  role_arn              = aws_iam_role.sagemaker_execution_role[each.key].arn
  instance_type         = each.value.instance_type
  volume_size           = each.value.volume_size
  lifecycle_config_name = aws_sagemaker_notebook_instance_lifecycle_configuration.models_lifecycle_config[each.key].name

  default_code_repository = aws_sagemaker_code_repository.models_repo[each.key].id
}

resource "aws_sagemaker_code_repository" "models_repo" {
  for_each = var.env

  code_repository_name = "${each.key}-models-github-repository"

  git_config {
    repository_url = var.github_repository_url
    branch         = each.key == "prod" ? "main" : each.key
  }
}

resource "aws_sagemaker_notebook_instance_lifecycle_configuration" "models_lifecycle_config" {
  for_each = var.env
  name     = "${each.key}-models-lifecycle"
  on_start = filebase64("scripts/notebooks-on-start.sh")
}

