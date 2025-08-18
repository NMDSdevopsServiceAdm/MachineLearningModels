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
  on_start = base64encode(templatefile("${path.module}/scripts/notebooks-on-start.sh.tpl", { env = each.key,
  bucket = var.config_bucket_name }))

  depends_on = [aws_s3_object.autostop_script]
}

resource "aws_s3_object" "autostop_script" {
  for_each = var.env
  bucket   = var.config_bucket_name
  key      = "scripts/python/${each.key}/autostop.py"
  source   = "scripts/autostop.py"
  etag     = filemd5("scripts/autostop.py")
}
