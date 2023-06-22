resource "aws_route53_zone" "site" {
  name = var.hostname
}

resource "aws_acm_certificate" "site" {
  domain_name       = var.hostname
  validation_method = "DNS"
}

resource "aws_acm_certificate_validation" "validation" {
  certificate_arn         = aws_acm_certificate.site.arn
  validation_record_fqdns = [for record in aws_route53_record.validation : record.name]
}

data "cloudflare_zone" "site-zone" {
  name = var.base_hostname
}

resource "cloudflare_record" "ns" {
  zone_id = data.cloudflare_zone.site-zone.id
  name    = var.hostname
  value   = aws_route53_zone.site.name_servers[0]
  type    = "NS"
  proxied = false
}

resource "cloudflare_record" "ns1" {
  zone_id = data.cloudflare_zone.site-zone.id
  name    = var.hostname
  value   = aws_route53_zone.site.name_servers[1]
  type    = "NS"
  proxied = false
}

resource "cloudflare_record" "ns2" {
  zone_id = data.cloudflare_zone.site-zone.id
  name    = var.hostname
  value   = aws_route53_zone.site.name_servers[2]
  type    = "NS"
  proxied = false
}

resource "cloudflare_record" "ns3" {
  zone_id = data.cloudflare_zone.site-zone.id
  name    = var.hostname
  value   = aws_route53_zone.site.name_servers[3]
  type    = "NS"
  proxied = false
}

resource "aws_route53_record" "validation" {
  for_each = {
    for dvo in aws_acm_certificate.site.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = aws_route53_zone.site.zone_id
}

resource "aws_route53_record" "caa" {
  allow_overwrite = false
  name            = var.hostname
  records         = ["0 issue \"amazonaws.com\""]
  ttl             = 60
  type            = "CAA"
  zone_id         = aws_route53_zone.site.zone_id
}

resource "aws_apigatewayv2_domain_name" "api-domain" {
  domain_name = var.hostname
  domain_name_configuration {
    certificate_arn = aws_acm_certificate_validation.validation.certificate_arn
    endpoint_type   = "REGIONAL"
    security_policy = "TLS_1_2"
  }
}


resource "aws_route53_record" "app" {
  allow_overwrite = true
  name            = var.hostname
  type            = "A"
  zone_id         = aws_route53_zone.site.zone_id
  alias {
    name                   = aws_apigatewayv2_domain_name.api-domain.domain_name_configuration[0].target_domain_name
    zone_id                = aws_apigatewayv2_domain_name.api-domain.domain_name_configuration[0].hosted_zone_id
    evaluate_target_health = false
  }
}

resource "aws_service_discovery_private_dns_namespace" "pdns" {
  name = "${var.hostname}.local"
  vpc  = module.vpc.vpc_id
}

resource "aws_security_group" "vpc-link" {
  name   = "${local.name}-vpc-link"
  vpc_id = module.vpc.vpc_id

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }
}

resource "aws_apigatewayv2_vpc_link" "vpc-link" {
  name               = "${local.name}-vpc-link"
  security_group_ids = [aws_security_group.vpc-link.id]
  subnet_ids         = module.vpc.public_subnets
}

resource "aws_service_discovery_service" "service-discovery" {
  name = "${local.name}-service-discovery"

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.pdns.id

    dns_records {
      ttl  = 10
      type = "SRV"
    }
  }

  health_check_custom_config {
    failure_threshold = 1
  }
}

resource "aws_apigatewayv2_api" "apigw" {
  name          = "${local.name}-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "integration" {
  api_id             = aws_apigatewayv2_api.apigw.id
  connection_id      = aws_apigatewayv2_vpc_link.vpc-link.id
  connection_type    = "VPC_LINK"
  integration_method = "ANY"
  integration_type   = "HTTP_PROXY"
  integration_uri    = aws_service_discovery_service.service-discovery.arn
}

resource "aws_apigatewayv2_stage" "stage" {
  api_id      = aws_apigatewayv2_api.apigw.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_apigatewayv2_route" "apigw-route" {
  api_id    = aws_apigatewayv2_api.apigw.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.integration.id}"
}

resource "aws_apigatewayv2_api_mapping" "mapping" {
  api_id      = aws_apigatewayv2_api.apigw.id
  domain_name = aws_apigatewayv2_domain_name.api-domain.id
  stage       = aws_apigatewayv2_stage.stage.id
}
