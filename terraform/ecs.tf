resource "aws_cloudwatch_log_group" "logs" {
  name              = local.name
  retention_in_days = 14
}

resource "aws_ecs_cluster" "cluster" {
  name = local.name

  setting {
    name  = "containerInsights"
    value = "disabled"
  }

  configuration {
    execute_command_configuration {
      kms_key_id = aws_kms_key.log-encryption.arn
      logging    = "OVERRIDE"

      log_configuration {
        cloud_watch_encryption_enabled = true
        cloud_watch_log_group_name     = aws_cloudwatch_log_group.logs.name
      }
    }
  }
}

resource "aws_ecs_task_definition" "nws-bot" {
  family                   = local.name
  requires_compatibilities = ["EC2"]
  task_role_arn            = aws_iam_role.ecs-agent.arn
  execution_role_arn       = aws_iam_role.ecs-agent.arn
  network_mode             = "bridge"
  container_definitions = jsonencode([
    {
      name      = local.name
      image     = var.docker_image
      cpu       = 2000
      memory    = 1536
      essential = true
      portMappings = [
        {
          containerPort = 80
          hostPort      = 80
          appProtocol   = "http2"
          protocol      = "tcp"
          name          = "${local.name}-80-tcp"
        }
      ]
      environment = [{
        name  = "CONFIG_JSON"
        value = var.config_json
      }]
      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://0.0.0.0:80/health || exit 1"]
        interval    = 5
        timeout     = 2
        retries     = 3
        startPeriod = 30
      }
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.logs.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = local.name
        }
      }
    }
  ])
}

resource "aws_ecs_service" "app" {
  name                               = local.name
  cluster                            = aws_ecs_cluster.cluster.id
  task_definition                    = aws_ecs_task_definition.nws-bot.arn
  deployment_maximum_percent         = 100
  deployment_minimum_healthy_percent = 0
  desired_count                      = 1
  launch_type                        = "EC2"
  service_registries {
    registry_arn   = aws_service_discovery_service.service-discovery.arn
    container_name = local.name
    container_port = 80
  }
  service_connect_configuration {
    enabled   = true
    namespace = aws_service_discovery_private_dns_namespace.pdns.arn
    service {
      client_alias {
        dns_name = local.name
        port     = 80
      }
      discovery_name = local.name
      port_name      = "${local.name}-80-tcp"
    }
  }
}
