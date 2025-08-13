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
      instance_type = "ml.t3.medium"
      volume_size   = 5
    }
    prod = {
      instance_type = "ml.t3.medium"
      volume_size   = 5
    }
  }
}

variable "github_repository_url" {
  description = "URL of the GitHub repository containing the machine learning notebooks"
  type        = string
  default     = "https://github.com/NMDSdevopsServiceAdm/MachineLearningModels.git"
}

