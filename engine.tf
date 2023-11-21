provider "aws" {
  region = "us-east-1"
  alias  = "engine"
  default_tags {
    tags = {
      Environment = "shared"
    }
  }
}
resource "aws_security_group" "lrm_engine_sg" {
  name        = "lrm_engine_sg"
  description = "Main security group for LRM V2 devuction network"
  vpc_id      = aws_vpc.lrm_v2.id

  ingress {
    description      = "HTTPS from public internet"
    from_port        = 443
    to_port          = 443
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }
  ingress {
    description      = "HTTP for internal traffic from ELB to ECS"
    from_port        = 80
    to_port          = 80
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }
  ingress {
    description      = "Redis Port"
    from_port        = 6379
    to_port          = 6379
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }
  ingress {
    description      = "MySQL DB"
    from_port        = 3306
    to_port          = 3306
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name = "lrm_engine_sg"
  }
}

resource "aws_s3_bucket" "lrm_engine_elb_logs" {
  bucket = "lrm-engine-elb-logs"

  tags = {
    Environment = "shared"
    Proyect     = "lrm"
    Name        = "lrm-engine-elb-logs"
  }
}

data "aws_iam_policy_document" "lrm_engine_allow_access_for_elb_logging" {
  statement {
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::127311923021:root"]
    }
    effect = "Allow"
    actions = [
      "s3:PutObject",
    ]

    resources = [
      aws_s3_bucket.lrm_engine_elb_logs.arn,
      "${aws_s3_bucket.lrm_engine_elb_logs.arn}/lrm-engine-elb/AWSLogs/185279236646/*",
    ]
  }
}
resource "aws_s3_bucket_policy" "lrm_engine_elb_logs_put_permission" {
  bucket = aws_s3_bucket.lrm_engine_elb_logs.id
  policy = data.aws_iam_policy_document.lrm_engine_allow_access_for_elb_logging.json
}

resource "aws_lb" "lrm_engine_elb" {
  name                       = "lrm-engine-elb"
  internal                   = false
  load_balancer_type         = "application"
  security_groups            = [aws_security_group.lrm_engine_sg.id]
  subnets                    = [aws_subnet.dev_a.id, aws_subnet.dev_b.id, aws_subnet.dev_c.id]
  idle_timeout               = 500
  enable_deletion_protection = true

  access_logs {
    bucket  = aws_s3_bucket.lrm_engine_elb_logs.bucket
    prefix  = "lrm-engine-elb"
    enabled = true
  }
  tags = {
    Environment = "shared"
    Proyect     = "lrm"
  }
}

resource "aws_lb_target_group" "lrm_engine_tg" {
  name        = "lrm-engine-tg"
  target_type = "ip"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = aws_vpc.lrm_v2.id
  health_check {
    path = "/healthcheck"
  }
  tags = {
    Environment = "shared"
    Proyect     = "lrm"
  }
}

resource "aws_acm_certificate" "lrm_engine_domain_cert" {
  domain_name       = "engine.cheilbidx.io"
  validation_method = "DNS"
  tags = {
    Environment = "shared"
    Proyect     = "lrm"
  }
}


resource "aws_route53_record" "lrm_engine_domain_records" {
  for_each = {
    for dvo in aws_acm_certificate.lrm_engine_domain_cert.domain_validation_options : dvo.domain_name => {
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
  zone_id         = aws_route53_zone.lrm_v2_dns_zone.zone_id
}

resource "aws_acm_certificate_validation" "lrm_engine_domain_cert_validation" {
  certificate_arn         = aws_acm_certificate.lrm_engine_domain_cert.arn
  validation_record_fqdns = [for record in aws_route53_record.lrm_engine_domain_records : record.fqdn]
}

resource "aws_lb_listener" "lrm_engine_elb_listener" {
  load_balancer_arn = aws_lb.lrm_engine_elb.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"

  certificate_arn = aws_acm_certificate_validation.lrm_engine_domain_cert_validation.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.lrm_engine_tg.arn
  }
}

resource "aws_route53_record" "lrm_engine_elb_records" {
  name            = "engine"
  records         = [aws_lb.lrm_engine_elb.dns_name]
  type            = "CNAME"
  allow_overwrite = true
  ttl             = 60
  zone_id         = aws_route53_zone.lrm_v2_dns_zone.zone_id
}

resource "aws_ecr_repository" "lrm_engine_container_registry" {
  name                 = "lrm-engine-api"
  image_tag_mutability = "MUTABLE"
  image_scanning_configuration {
    scan_on_push = true
  }
  tags = {
    Environment = "shared"
    Proyect     = "lrm"
  }
}

resource "aws_ecs_task_definition" "lrm_engine_ecs_task_definition" {

  family                   = "lrm-engine"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 4 * 1024
  memory                   = 8 * 1024
  execution_role_arn       = "arn:aws:iam::185279236646:role/ecsTaskExecutionRole"
  container_definitions = jsonencode([
    {
      name      = "lrm_engine"
      image     = aws_ecr_repository.lrm_engine_container_registry.repository_url
      essential = true
      environment = [
        { name = "ACCESS_KEY", value = "AKIASWI4AZITDQ7SCW2G" },
        { name = "ALLOWED_HOSTS", value = "*" },
        { name = "CORS_ALLOWED_DOMAINS", value = "localhost:3000" },

        { name = "DB_ENGINE", value = "django.db.backends.mysql" },
        #{ name = "DB_HOST", value = aws_db_instance.lrm_engine_db.address },
        #{ name = "DB_PASSWORD", value = aws_db_instance.lrm_engine_db.password },
        { name = "DB_SCHEMA", value = "lrm_dev" },
        #{ name = "DB_USER", value = aws_db_instance.lrm_engine_db.username },
        { name = "EMAIL_BACKEND", value = "django.core.mail.backends.smtp.EmailBackend" },
        { name = "EMAIL_HOST", value = "email-smtp.us-east-1.amazonaws.com" },
        { name = "EMAIL_HOST_PASSWORD", value = "BF8V59hH0JqtkVoy+QNysyF+YEuVWVev/Q3gQeNrdHAh" },
        { name = "EMAIL_HOST_USER", value = "AKIASWI4AZITB2TNIIY5" },
        { name = "EMAIL_PORT", value = "587" },
        { name = "EMAIL_USE_TLS", value = "True" },
        { name = "FRONTEND_HOST", value = "https://dev.cheilbidx.io" },
        { name = "PYTHONHASHSEED", value = "0" },
        { name = "REDIS_ENABLED", value = "True" },
        #{ name = "REDIS_HOST", value = aws_elasticache_cluster.lrm_v2_redis_dev.cache_nodes[0].address },
        #{ name = "REDIS_PORT", value = format("%s", aws_elasticache_cluster.lrm_v2_redis_dev.cache_nodes[0].port) },
        { name = "SECRET_KEY", value = "i9G7g92xQ7sBQq+ryYaYfgUl/iB8ZCW9W7Yk6Vgj" },
        { name = "PYTHON_ENV", value = "dev" },
        { name = "MSO_HOSTNAME", value = "https://api.msocheil.com" },
        { name = "MSO_USER", value = "RM" },
        { name = "MSO_CRED", value = "Samsung!234" },
        { name = "LOAD_W2", value = "True" },
        #{ name = "LOG_RESOURCES", value = "True" }
      ]
      portMappings = [
        {
          containerPort = 80
          hostPort      = 80
        }
      ]
    }
  ])
  tags = {
    Environment = "shared"
    Proyect     = "lrm"
    Domain      = "data"
  }
}
resource "aws_cloudwatch_log_group" "lrm_engine_ecs_lg" {
  name = "lrm_engine_ecs_lg"

  retention_in_days = 3
  tags = {
    Environment = "shared"
    Proyect     = "lrm"
  }
}

resource "aws_ecs_cluster" "lrm_engine_ecs_cluster" {
  name = "lrm-engine"
  configuration {
    execute_command_configuration {
      logging = "OVERRIDE"
      log_configuration {
        cloud_watch_encryption_enabled = true
        cloud_watch_log_group_name     = aws_cloudwatch_log_group.lrm_engine_ecs_lg.name
      }
    }
  }
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
  tags = {
    Environment = "shared"
    Proyect     = "lrm"
  }
}

resource "aws_ecs_service" "lrm_engine_ecs_service" {
  name            = "lrm-engine-ecs-service"
  cluster         = aws_ecs_cluster.lrm_engine_ecs_cluster.id
  task_definition = aws_ecs_task_definition.lrm_engine_ecs_task_definition.arn
  desired_count   = 0
  launch_type     = "FARGATE"

  load_balancer {
    target_group_arn = aws_lb_target_group.lrm_engine_tg.arn
    container_name   = "lrm_engine"
    container_port   = 80
  }
  network_configuration {
    subnets          = [aws_subnet.dev_a.id, aws_subnet.dev_b.id, aws_subnet.dev_c.id]
    security_groups  = [aws_security_group.lrm_engine_sg.id]
    assign_public_ip = "true"
  }
  propagate_tags = "TASK_DEFINITION"
  tags = {
    Environment = "shared"
    Proyect     = "lrm"
  }
}

