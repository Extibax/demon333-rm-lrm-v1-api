

provider "aws" {
  region = "us-east-1"
  alias  = "dev"
  default_tags {
    tags = {
      Environment = "development"
    }
  }
}


resource "aws_subnet" "dev_a" {
  vpc_id                  = aws_vpc.lrm_v2.id
  cidr_block              = "10.0.48.0/20"
  availability_zone       = "us-east-1a"
  map_public_ip_on_launch = "true"
  tags = {
    Name = "dev_a"
  }
}
resource "aws_subnet" "dev_b" {
  vpc_id                  = aws_vpc.lrm_v2.id
  cidr_block              = "10.0.64.0/20"
  map_public_ip_on_launch = "true"
  availability_zone       = "us-east-1b"
  tags = {
    Name = "dev_b"
  }
}
resource "aws_subnet" "dev_c" {
  vpc_id                  = aws_vpc.lrm_v2.id
  cidr_block              = "10.0.80.0/20"
  availability_zone       = "us-east-1c"
  map_public_ip_on_launch = "true"
  tags = {
    Name = "dev_c"
  }
}

resource "aws_security_group" "lrm_v2_dev_sg" {
  name        = "lrm_v2_dev_sg"
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
    Name = "lrm_v2_dev_sg"
  }
}

resource "aws_security_group" "lrm_v2_vpn_sg_dev" {
  name        = "lrm_v2_vpn_sg"
  description = "Main security group for LRM V2 vpn"
  vpc_id      = aws_vpc.lrm_v2.id

  ingress {
    description = "HTTPS from public internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    #ipv6_cidr_blocks = ["::/0"]
  }
  ingress {
    #description      = "HTTP for internal traffic from ELB to ECS"
    from_port   = 943
    to_port     = 943
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    #ipv6_cidr_blocks = ["::/0"]
  }
  ingress {
    description = "Redis Port"
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    #ipv6_cidr_blocks = ["::/0"]
  }
  ingress {
    description = "MySQL DB"
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    #ipv6_cidr_blocks = ["::/0"]
  }
  ingress {
    #description      = "MySQL DB"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    #ipv6_cidr_blocks = ["::/0"]
  }
  ingress {
    #description      = "MySQL DB"
    from_port   = 1194
    to_port     = 1194
    protocol    = "udp"
    cidr_blocks = ["0.0.0.0/0"]
    #ipv6_cidr_blocks = ["::/0"]
  }

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }
}

resource "aws_s3_bucket" "lrm_v2_elb_logs_dev" {
  bucket = "lrm-v2-elb-logs-dev"

  tags = {
    Environment = "development"
    Proyect     = "lrm"
    Name        = "lrm-v2-elb-logs-dev"
  }
}


data "aws_iam_policy_document" "allow_access_for_elb_logging_dev" {
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
      aws_s3_bucket.lrm_v2_elb_logs_dev.arn,
      "${aws_s3_bucket.lrm_v2_elb_logs_dev.arn}/lrm-v2-dev-elb/AWSLogs/185279236646/*",
    ]
  }
}
resource "aws_s3_bucket_policy" "lrm_v2_elb_logs_dev_put_permission" {
  bucket = aws_s3_bucket.lrm_v2_elb_logs_dev.id
  policy = data.aws_iam_policy_document.allow_access_for_elb_logging_dev.json
}
resource "aws_lb" "lrm_v2_dev_elb" {
  name                       = "lrm-v2-dev-elb"
  internal                   = false
  load_balancer_type         = "application"
  security_groups            = [aws_security_group.lrm_v2_dev_sg.id]
  subnets                    = [aws_subnet.dev_a.id, aws_subnet.dev_b.id, aws_subnet.dev_c.id]
  idle_timeout               = 500
  enable_deletion_protection = true

  access_logs {
    bucket  = aws_s3_bucket.lrm_v2_elb_logs_dev.bucket
    prefix  = "lrm-v2-dev-elb"
    enabled = true
  }
  tags = {
    Environment = "development"
    Proyect     = "lrm"
  }
}

resource "aws_lb_target_group" "lrm_v2_dev_tg" {
  name        = "lrm-v2-dev-tg"
  target_type = "ip"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = aws_vpc.lrm_v2.id
  health_check {
    path = "/healthcheck"
  }
  tags = {
    Environment = "development"
    Proyect     = "lrm"
  }
}

resource "aws_acm_certificate" "lrm_v2_dev_domain_cert" {
  domain_name       = "lrm-api-dev.cheilbidx.io"
  validation_method = "DNS"
  tags = {
    Environment = "development"
    Proyect     = "lrm"
  }
}


resource "aws_route53_record" "lrm_v2_dev_domain_records" {
  for_each = {
    for dvo in aws_acm_certificate.lrm_v2_dev_domain_cert.domain_validation_options : dvo.domain_name => {
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

resource "aws_acm_certificate_validation" "lrm_v2_dev_domain_cert_validation" {
  certificate_arn         = aws_acm_certificate.lrm_v2_dev_domain_cert.arn
  validation_record_fqdns = [for record in aws_route53_record.lrm_v2_dev_domain_records : record.fqdn]
}

resource "aws_lb_listener" "lrm_v2_dev_elb_listener" {
  load_balancer_arn = aws_lb.lrm_v2_dev_elb.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"

  certificate_arn = aws_acm_certificate_validation.lrm_v2_dev_domain_cert_validation.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.lrm_v2_dev_tg.arn
  }
}

resource "aws_route53_record" "lrm_v2_dev_elb_records" {
  name            = "lrm-api-dev"
  records         = [aws_lb.lrm_v2_dev_elb.dns_name]
  type            = "CNAME"
  allow_overwrite = true
  ttl             = 60
  zone_id         = aws_route53_zone.lrm_v2_dns_zone.zone_id
}

resource "aws_ecr_repository" "lrm_v2_dev_container_registry" {
  name                 = "lrm-v2-dev-api"
  image_tag_mutability = "MUTABLE"
  image_scanning_configuration {
    scan_on_push = true
  }
  tags = {
    Environment = "development"
    Proyect     = "lrm"
  }
}
# DATA LAYER

resource "aws_elasticache_subnet_group" "lrm_v2_dev_subnet_group" {
  name       = "lrm-v2-dev-subnet-group"
  subnet_ids = [aws_subnet.dev_a.id, aws_subnet.dev_b.id, aws_subnet.dev_c.id]
}
resource "aws_elasticache_cluster" "lrm_v2_redis_dev" {
  cluster_id      = "lrm-v2-dev"
  engine          = "redis"
  node_type       = "cache.t4g.medium"
  num_cache_nodes = 1
  #parameter_group_name = "default.redis6.x"
  #engine_version     = "6.2.6"
  port               = 6379
  security_group_ids = [aws_security_group.lrm_v2_dev_sg.id]
  subnet_group_name  = aws_elasticache_subnet_group.lrm_v2_dev_subnet_group.name
  tags = {
    Environment = "development"
    Proyect     = "lrm"
  }
}

resource "aws_db_subnet_group" "lrm_v2_dev_db_subnet_group" {
  name       = "lrm-v2-dev-subnet-group"
  subnet_ids = [aws_subnet.dev_a.id, aws_subnet.dev_b.id, aws_subnet.dev_c.id]

}
resource "aws_db_instance" "lrm_v2_dev_db" {
  allocated_storage         = 50
  engine                    = "mysql"
  engine_version            = "8.0.28"
  instance_class            = "db.t3.medium"
  username                  = "admin"
  password                  = "977bf9abf3c3e3fd6b8fd79775c66a33"
  parameter_group_name      = "default.mysql8.0"
  skip_final_snapshot       = false
  final_snapshot_identifier = "final-snapshot-lrmv2-dev"
  db_name                   = "lrm_dev"
  identifier                = "lrm-v2-dev"
  db_subnet_group_name      = aws_db_subnet_group.lrm_v2_dev_db_subnet_group.name
  multi_az                  = false
  backup_retention_period   = 15
  backup_window             = "03:00-05:00"
  maintenance_window        = "Sun:00:00-Sun:03:00"
  storage_type              = "gp2"
  vpc_security_group_ids    = [aws_security_group.lrm_v2_dev_sg.id]
  copy_tags_to_snapshot     = true
  tags = {
    Environment = "development"
    Proyect     = "lrm"
  }
}

# ECS CLUSTER RESOURCES

resource "aws_ecs_task_definition" "lrm_v2_dev_ecs_task_definition" {

  family                   = "lrm-v2-dev"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 4096
  memory                   = 25600
  execution_role_arn       = "arn:aws:iam::185279236646:role/ecsTaskExecutionRole"
  container_definitions = jsonencode([
    {
      name      = "lrm_v2_dev"
      image     = aws_ecr_repository.lrm_v2_dev_container_registry.repository_url
      essential = true
      environment = [
        { name = "ACCESS_KEY", value = "AKIASWI4AZITDQ7SCW2G" },
        { name = "ALLOWED_HOSTS", value = "*" },
        { name = "CORS_ALLOWED_DOMAINS", value = "http://localhost:4200,https://dev.dcntd.cloud,https://dev.cheilbidx.io,https://cheilbidx.io,https://rm.cheilbidx.io" },

        { name = "DB_ENGINE", value = "django.db.backends.mysql" },
        { name = "DB_HOST", value = aws_db_instance.lrm_v2_dev_db.address },
        { name = "DB_PASSWORD", value = aws_db_instance.lrm_v2_dev_db.password },
        { name = "DB_SCHEMA", value = "lrm_dev" },
        { name = "DB_USER", value = aws_db_instance.lrm_v2_dev_db.username },
        { name = "EMAIL_BACKEND", value = "django.core.mail.backends.smtp.EmailBackend" },
        { name = "EMAIL_HOST", value = "email-smtp.us-east-1.amazonaws.com" },
        { name = "EMAIL_HOST_PASSWORD", value = "BF8V59hH0JqtkVoy+QNysyF+YEuVWVev/Q3gQeNrdHAh" },
        { name = "EMAIL_HOST_USER", value = "AKIASWI4AZITB2TNIIY5" },
        { name = "EMAIL_PORT", value = "587" },
        { name = "EMAIL_USE_TLS", value = "True" },
        { name = "FRONTEND_HOST", value = "https://dev.cheilbidx.io" },
        { name = "PYTHONHASHSEED", value = "0" },
        { name = "REDIS_ENABLED", value = "True" },
        { name = "REDIS_HOST", value = aws_elasticache_cluster.lrm_v2_redis_dev.cache_nodes[0].address },
        { name = "REDIS_PORT", value = format("%s", aws_elasticache_cluster.lrm_v2_redis_dev.cache_nodes[0].port) },
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
    Environment = "development"
    Proyect     = "lrm"
    Domain      = "backend"
  }
}
resource "aws_cloudwatch_log_group" "lrm_v2_dev_ecs_lg" {
  name = "lrm_v2_dev_ecs_lg"

  retention_in_days = 3
  tags = {
    Environment = "development"
    Proyect     = "lrm"
  }
}

resource "aws_ecs_cluster" "lrm_v2_dev_ecs_cluster" {
  name = "lrm-v2-dev"
  configuration {
    execute_command_configuration {
      logging = "OVERRIDE"
      log_configuration {
        cloud_watch_encryption_enabled = true
        cloud_watch_log_group_name     = aws_cloudwatch_log_group.lrm_v2_dev_ecs_lg.name
      }
    }
  }
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
  tags = {
    Environment = "development"
    Proyect     = "lrm"
  }
}

resource "aws_ecs_service" "lrm_v2_dev_ecs_service" {
  name            = "lrm-v2-dev-ecs-service"
  cluster         = aws_ecs_cluster.lrm_v2_dev_ecs_cluster.id
  task_definition = aws_ecs_task_definition.lrm_v2_dev_ecs_task_definition.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  load_balancer {
    target_group_arn = aws_lb_target_group.lrm_v2_dev_tg.arn
    container_name   = "lrm_v2_dev"
    container_port   = 80
  }
  network_configuration {
    subnets          = [aws_subnet.dev_a.id, aws_subnet.dev_b.id, aws_subnet.dev_c.id]
    security_groups  = [aws_security_group.lrm_v2_dev_sg.id]
    assign_public_ip = "true"
  }
  propagate_tags = "TASK_DEFINITION"
  tags = {
    Environment = "development"
    Proyect     = "lrm"
  }
}

