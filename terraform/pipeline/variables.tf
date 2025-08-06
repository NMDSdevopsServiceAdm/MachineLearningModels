variable "aws_access_key" {
  description = "Access key for AWS - find this in IAM"
  type        = string
  sensitive   = true
}
variable "aws_secret_key" {
  description = "Secret key for AWS - displayed when IAM user is created"
  type        = string
  sensitive   = true
}

variable "region" {
  default = "eu-west-2"
}

variable "github_repository_url" {
  description = "URL of the GitHub repository containing the machine learning motebooks"
  type        = string
  default     = "https://github.com/NMDSdevopsServiceAdm/MachineLearningModels.git"
}
