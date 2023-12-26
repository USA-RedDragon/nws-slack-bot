terraform {
  backend "s3" {
    bucket = "mcswain-dev-tf-states"
    key    = "nws-slack-bot"
    region = "us-east-1"
  }
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.31.0"
    }
    template = {
      source  = "hashicorp/template"
      version = "2.2.0"
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "4.21.0"
    }
  }
}

locals {
  name     = "nws-slack-bot"
  vpc_cidr = "10.0.0.0/16"
}

provider "aws" {
  region = var.aws_region
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}

data "aws_availability_zones" "available_zones" {
  state = "available"
}

module "vpc" {
  source = "terraform-aws-modules/vpc/aws"

  name = local.name
  cidr = local.vpc_cidr

  azs = data.aws_availability_zones.available_zones.names
  public_subnets = [
    cidrsubnet(local.vpc_cidr, 8, 0),
    cidrsubnet(local.vpc_cidr, 8, 1),
    cidrsubnet(local.vpc_cidr, 8, 2)
  ]
}

data "aws_ami" "ecs" {
  most_recent = true

  filter {
    name   = "name"
    values = ["amzn2-ami-ecs-hvm-*-*-ebs"]
  }

  filter {
    name   = "architecture"
    values = [var.arch]
  }

  owners = ["amazon"]
}
