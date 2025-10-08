variable "region" {
  default = "eu-west-2"
}

variable "env_config" {
  description = "Map of environment configurations"
  type = map(object({
    instance_type      = string
    volume_size        = number
    config_bucket_name = string
  }))
  default = {
    dev = {
      instance_type      = "ml.m5.2xlarge"
      volume_size        = 10
      config_bucket_name = "sfc-sagemaker-model-config-dev"
    }
    prod = {
      instance_type      = "ml.m5.2xlarge"
      volume_size        = 10
      config_bucket_name = "sfc-sagemaker-model-config"
    }
  }
}

variable "github_repository_url" {
  description = "URL of the GitHub repository containing the machine learning notebooks"
  type        = string
  default     = "https://github.com/NMDSdevopsServiceAdm/MachineLearningModels.git"
}

