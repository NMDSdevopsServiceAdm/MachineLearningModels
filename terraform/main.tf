provider "aws" {
  region = "eu-west-2"
}

terraform {
  backend "s3" {
    bucket         = "sfc-models-terraform-state"
    key            = "statefiles/workspace=default/backend.tfstate"
    region         = "eu-west-2"
    dynamodb_table = "models-terraform-locks"
    encrypt        = true
  }
}

data "aws_caller_identity" "current" {}

locals {
  workspace_prefix           = substr(lower(replace(terraform.workspace, "/[^a-zA-Z0-9]+/", "-")), 0, 30)
  is_development_environment = local.workspace_prefix != "main"
}
