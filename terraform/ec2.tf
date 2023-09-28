resource "aws_launch_template" "ecs" {
  name_prefix   = "${local.name}-ecs"
  instance_type = var.instance-type
  image_id      = data.aws_ami.ecs.id
  iam_instance_profile {
    arn = aws_iam_instance_profile.ecs-agent.arn
  }
  network_interfaces {
    associate_public_ip_address = true
    subnet_id                   = module.vpc.public_subnets[0]
    security_groups             = [aws_security_group.deny-all-inbound.id]
  }
  user_data = base64encode("#!/bin/bash\necho ECS_CLUSTER=${aws_ecs_cluster.cluster.name} >> /etc/ecs/ecs.config\n")
}

resource "aws_security_group" "deny-all-inbound" {
  name        = "${local.name}-deny-all-inbound"
  description = "Deny all inbound traffic"
  vpc_id      = module.vpc.vpc_id

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  ingress {
    security_groups = [aws_security_group.vpc-link.id]
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
  }
}

resource "aws_autoscaling_group" "asg" {
  availability_zones = [data.aws_availability_zones.available_zones.names[0]]
  desired_capacity   = 1
  max_size           = 2
  min_size           = 1

  launch_template {
    id      = aws_launch_template.ecs.id
    version = aws_launch_template.ecs.latest_version
  }

  instance_refresh {
    strategy = "Rolling"
    preferences {
      min_healthy_percentage = 100
    }
    triggers = ["tag"]
  }
}

data "aws_iam_policy_document" "allow-cloudwatch-logs" {
  statement {
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]

    resources = [
      aws_cloudwatch_log_group.logs.arn,
    ]
  }
}
