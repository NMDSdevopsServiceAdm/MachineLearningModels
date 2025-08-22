variable "region" {
  default = "eu-west-2"
}

variable "config_bucket_name" {
  type    = string
  default = "sfc-sagemaker-model-config"
}

variable "env" {
  type        = set(string)
  default     = ["dev"]
  description = "The required environments for deployment"
}

variable "env_config" {
  description = "Map of environment configurations"
  type = map(object({
    instance_type = string
    volume_size   = number
  }))
  default = {
    dev = {
      instance_type = "ml.m5.2xlarge"
      volume_size   = 10
    }
    prod = {
      instance_type = "ml.m5.2xlarge"
      volume_size   = 10
    }
  }
}

variable "github_repository_url" {
  description = "URL of the GitHub repository containing the machine learning notebooks"
  type        = string
  default     = "git@github.com:NMDSdevopsServiceAdm/MachineLearningModels.git"
}

