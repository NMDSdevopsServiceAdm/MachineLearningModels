resource "aws_sagemaker_notebook_instance" "models_notebook" {
  name                  = "${local.env}-models-notebook"
  role_arn              = aws_iam_role.sagemaker_execution_role.arn
  instance_type         = var.env_config[local.env].instance_type
  volume_size           = var.env_config[local.env].volume_size
  lifecycle_config_name = aws_sagemaker_notebook_instance_lifecycle_configuration.models_lifecycle_config.name

  default_code_repository = aws_sagemaker_code_repository.models_repo.id

  tags = {
    PYTHONPATH = "/home/ec2-user/SageMaker/MachineLearningModels"
    ENV        = local.env
  }
}

resource "aws_sagemaker_code_repository" "models_repo" {
  code_repository_name = "${local.env}-models-github-repository"

  git_config {
    repository_url = var.github_repository_url
    branch         = local.env == "prod" ? "main" : local.env
  }
}

resource "aws_sagemaker_notebook_instance_lifecycle_configuration" "models_lifecycle_config" {
  name = "${local.env}-models-lifecycle"
  on_start = base64encode(templatefile("${path.module}/scripts/notebooks-on-start.sh.tpl", { env = local.env,
  bucket = var.env_config[local.env].config_bucket_name }))

  depends_on = [aws_s3_object.autostop_script]
}

resource "aws_s3_object" "autostop_script" {
  bucket = var.env_config[local.env].config_bucket_name
  key    = "scripts/python/${local.env}/autostop.py"
  source = "scripts/autostop.py"
  etag   = filemd5("scripts/autostop.py")
}
