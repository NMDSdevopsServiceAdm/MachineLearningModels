provider "aws" {
  region = "eu-west-2"
  default_tags {
    tags = {
      CreatedBy   = "MadeTech"
      CreatedWith = "Terraform"
      Repository  = "MachineLearningModels"
    }
  }
}

terraform {
  backend "s3" {
    bucket         = "sfc-sagemaker-model-config"
    key            = "terraform/statefiles/machine-learning-models/backend.tfstate"
    region         = "eu-west-2"
    dynamodb_table = "models-terraform-locks"
    encrypt        = true
  }
}

data "aws_caller_identity" "current" {}

