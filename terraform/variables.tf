variable "region" {
  default = "eu-west-2"
}

variable "env" {
  description = "Map of environment configurations"
  type = map(object({
    instance_type = string
    volume_size   = number
  }))
  default = {
    dev = {
      instance_type = "ml.m5.xlarge"
      volume_size   = 10
    }
    prod = {
      instance_type = "ml.m5.xlarge"
      volume_size   = 10
    }
  }
}

variable "github_repository_url" {
  description = "URL of the GitHub repository containing the machine learning notebooks"
  type        = string
  default     = "https://github.com/NMDSdevopsServiceAdm/MachineLearningModels.git"
}

