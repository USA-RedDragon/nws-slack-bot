variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "instance-type" {
  default     = "t4g.small"
  description = "The AWS instance type to use for the infrastructure"
}

variable "arch" {
  default     = "arm64"
  description = "The CPU architecture to use for the infrastructure"
}

variable "docker_image" {
  type    = string
  default = "ghcr.io/usa-reddragon/nws-slack-bot:latest"
}

variable "config_json" {
  type      = string
  sensitive = true
}

variable "hostname" {
  type = string
}

variable "base_hostname" {
  type = string
}

variable "cloudflare_api_token" {
  type      = string
  sensitive = true
}
