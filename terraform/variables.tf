variable "region" {
  default = "eu-west-2"
}

variable "github_repository_url" {
  description = "URL of the GitHub repository containing the machine learning motebooks"
  type        = string
  default     = "https://github.com/NMDSdevopsServiceAdm/MachineLearningModels.git"
}
