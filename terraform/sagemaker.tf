resource "aws_sagemaker_notebook_instance" "models_notebook" {
  for_each              = var.env
  name                  = "${each.value}-models-notebook"
  role_arn              = aws_iam_role.sagemaker_execution_role[each.value].arn
  instance_type         = var.env_config[each.value].instance_type
  volume_size           = var.env_config[each.value].volume_size
  lifecycle_config_name = aws_sagemaker_notebook_instance_lifecycle_configuration.models_lifecycle_config[each.value].name

  default_code_repository = aws_sagemaker_code_repository.models_repo[each.value].id

  tags = {
    PYTHONPATH = "/home/ec2-user/SageMaker/MachineLearningModels"
    ENV        = each.value
  }
}

resource "aws_sagemaker_code_repository" "models_repo" {
  for_each = var.env

  code_repository_name = "${each.value}-models-github-repository"

  git_config {
    repository_url = var.github_repository_url
    branch         = each.value == "prod" ? "main" : each.value
  }
}

resource "aws_sagemaker_notebook_instance_lifecycle_configuration" "models_lifecycle_config" {
  for_each = var.env
  name     = "${each.value}-models-lifecycle"
  on_start = base64encode(templatefile("${path.module}/scripts/notebooks-on-start.sh.tpl", { env = each.value,
  bucket = var.config_bucket_name }))
  on_create = base64encode(templatefile("${path.module}/scripts/notebook-instance-on-create.sh.tpl", { env = each.value }))

  depends_on = [aws_s3_object.autostop_script]
}

resource "aws_s3_object" "autostop_script" {
  for_each = var.env
  bucket   = var.config_bucket_name
  key      = "scripts/python/${each.value}/autostop.py"
  source   = "scripts/autostop.py"
  etag     = filemd5("scripts/autostop.py")
}
