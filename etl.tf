provider "aws" {
  region = "us-east-1"
  alias  = "etl"
  default_tags {
    tags = {
      Environment = "ETL"
    }
  }
}

#region COMPUTE ENVIRONMENT
resource "aws_iam_role" "lrm_v2_instance_role" {
  name = "lrm_v2_instance_role"

  assume_role_policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
    {
        "Action": "sts:AssumeRole",
        "Effect": "Allow",
        "Principal": {
            "Service": "ec2.amazonaws.com"
        }
    }
    ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "lrm_v2_instance_role" {
  role       = aws_iam_role.lrm_v2_instance_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role"
}

resource "aws_iam_instance_profile" "lrm_v2_instance_role" {
  name = "lrm_v2_instance_role"
  role = aws_iam_role.lrm_v2_instance_role.name
}

resource "aws_iam_role" "lrm_v2_batch_service_role" {
  name = "lrm_v2_batch_service_role"

  assume_role_policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
    {
        "Action": "sts:AssumeRole",
        "Effect": "Allow",
        "Principal": {
        "Service": "batch.amazonaws.com"
        }
    }
    ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "lrm_v2_batch_service_role" {
  role       = aws_iam_role.lrm_v2_batch_service_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBatchServiceRole"
}

resource "aws_security_group" "lrm_v2_batch_sg" {
  name = "lrm_v2_batch_sg"

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  vpc_id = aws_vpc.lrm_v2.id
}

resource "aws_batch_compute_environment" "lrm_v2_batch_compute_env" {
  compute_environment_name = "LRMV2ETLs"

  compute_resources {


    max_vcpus = 100
    min_vcpus = 0

    security_group_ids = [
      aws_security_group.lrm_v2_batch_sg.id,
    ]

    subnets = [
      "subnet-08ed3f524cc77cbe2", "subnet-0ad555f7510c27a5a", "subnet-09f420a6a3797fe1f"
    ]

    type = "FARGATE"
  }

  service_role = aws_iam_role.lrm_v2_batch_service_role.arn
  type         = "MANAGED"
  depends_on   = [aws_iam_role_policy_attachment.lrm_v2_batch_service_role]
}

#endregion COMPUTE ENVIRONMENT
#region JOB QUEUE

resource "aws_batch_job_queue" "lrm_v2_sales_f1_queue" {
  name     = "lrm_v2_sales_f1_queue"
  state    = "ENABLED"
  priority = 1
  compute_environments = [
    aws_batch_compute_environment.lrm_v2_batch_compute_env.arn,
  ]
}
resource "aws_batch_job_queue" "lrm_v2_sales_f2_queue" {
  name     = "lrm_v2_sales_f2_queue"
  state    = "ENABLED"
  priority = 1
  compute_environments = [
    aws_batch_compute_environment.lrm_v2_batch_compute_env.arn,
  ]
}
resource "aws_batch_job_queue" "lrm_v2_cache_l1_queue" {
  name     = "lrm_v2_cache_l1_queue"
  state    = "ENABLED"
  priority = 1
  compute_environments = [
    aws_batch_compute_environment.lrm_v2_batch_compute_env.arn,
  ]
}
resource "aws_batch_job_queue" "lrm_v2_data_migration_queue" {
  name     = "lrm_v2_dm_queue"
  state    = "ENABLED"
  priority = 1
  compute_environments = [
    aws_batch_compute_environment.lrm_v2_batch_compute_env.arn,
  ]
}

#endregion JOB QUEUE

#region ECR IMAGES
resource "aws_ecr_repository" "lrm_v2_f1_container_registry" {
  name                 = "lrm-v2-f1"
  image_tag_mutability = "MUTABLE"
  image_scanning_configuration {
    scan_on_push = true
  }
  tags = {
    Environment = "shared"
    Proyect     = "lrm"
  }
}

resource "aws_ecr_repository" "lrm_v2_f2_container_registry" {
  name                 = "lrm-v2-f2"
  image_tag_mutability = "MUTABLE"
  image_scanning_configuration {
    scan_on_push = true
  }
  tags = {
    Environment = "shared"
    Proyect     = "lrm"
  }
}
resource "aws_ecr_repository" "lrm_v2_c1_container_registry" {
  name                 = "lrm-v2-c1"
  image_tag_mutability = "MUTABLE"
  image_scanning_configuration {
    scan_on_push = true
  }
  tags = {
    Environment = "shared"
    Proyect     = "lrm"
  }
}

resource "aws_ecr_repository" "lrm_v2_datamigrations_container_registry" {
  name                 = "lrm-v2-dm"
  image_tag_mutability = "MUTABLE"
  image_scanning_configuration {
    scan_on_push = true
  }
  tags = {
    Environment = "shared"
    Proyect     = "lrm"
  }
}


#endregion
#region JOB DEFINITION
resource "aws_iam_role" "lrm_v2_ecs_task_execution_role" {
  name               = "lrm_v2_batch_exec_role"
  assume_role_policy = data.aws_iam_policy_document.lrm_v2_batchdef_assume_role_policy.json
}

data "aws_iam_policy_document" "lrm_v2_batchdef_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy_attachment" "lrm_v2_ecs_task_execution_role_policy" {
  role       = aws_iam_role.lrm_v2_ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_batch_job_definition" "lrm_v2_batch_jobdef_f1" {
  propagate_tags = true
  name           = "lrm_v2_batch_jobdef_f1"
  type           = "container"
  tags = {
    Environment = "shared"
    Proyect     = "lrm"
  }
  platform_capabilities = [
    "FARGATE",
  ]
  timeout {
    attempt_duration_seconds = 15000
  }
  container_properties = <<CONTAINER_PROPERTIES
{
  "command":["python","main.py","Ref::file","Ref::id"],
  "image": "${aws_ecr_repository.lrm_v2_f1_container_registry.repository_url}",
  "fargatePlatformConfiguration": {
    "platformVersion": "LATEST"
  },
   "environment": [ 
         { 
            "name": "BUCKET",
            "value": "etlgscmsales"
         },
         { 
            "name": "SECRET_KEY",
            "value": "i9G7g92xQ7sBQq+ryYaYfgUl/iB8ZCW9W7Yk6Vgj"
         },
         { 
            "name": "ACCESS_KEY",
            "value": "AKIASWI4AZITDQ7SCW2G"
         }
      ],
    "networkConfiguration": { 
         "assignPublicIp": "ENABLED"
      },
  "resourceRequirements": [
    {"type": "VCPU", "value": "2"},
    {"type": "MEMORY", "value": "8192"}
  ],
  "executionRoleArn": "${aws_iam_role.lrm_v2_ecs_task_execution_role.arn}"
}
CONTAINER_PROPERTIES
}

resource "aws_batch_job_definition" "lrm_v2_batch_jobdef_f2" {
  propagate_tags = true
  name           = "lrm_v2_batch_jobdef_f2"
  type           = "container"
  tags = {
    Environment = "shared"
    Proyect     = "lrm"
  }
  platform_capabilities = [
    "FARGATE",
  ]
  timeout {
    attempt_duration_seconds = 15000
  }
  container_properties = <<CONTAINER_PROPERTIES
{
  "command":["python","main.py","Ref::file","Ref::id"],
  "image": "${aws_ecr_repository.lrm_v2_f2_container_registry.repository_url}",
  "fargatePlatformConfiguration": {
    "platformVersion": "LATEST"
  },
   "environment": [ 
    
         { 
            "name": "DB_USER",
            "value": "${aws_db_instance.lrm_v2_dev_db.username}"
         },
         { 
            "name": "DB_PWD",
            "value": "${aws_db_instance.lrm_v2_dev_db.password}"
         },
         { 
            "name": "DB_SCHEMA",
            "value": "${aws_db_instance.lrm_v2_dev_db.db_name}"
         },
         { 
            "name": "DB_HOSTNAME",
            "value": "${aws_db_instance.lrm_v2_dev_db.address}"
         },
         { 
            "name": "SECRET_KEY",
            "value": "i9G7g92xQ7sBQq+ryYaYfgUl/iB8ZCW9W7Yk6Vgj"
         },
         { 
            "name": "ACCESS_KEY",
            "value": "AKIASWI4AZITDQ7SCW2G"
         }
      ],
    "networkConfiguration": { 
         "assignPublicIp": "ENABLED"
      },
  "resourceRequirements": [
    {"type": "VCPU", "value": "0.5"},
    {"type": "MEMORY", "value": "1024"}
  ],
  "executionRoleArn": "${aws_iam_role.lrm_v2_ecs_task_execution_role.arn}"
}
CONTAINER_PROPERTIES
}
resource "aws_batch_job_definition" "lrm_v2_batch_jobdef_c1" {
  propagate_tags = true
  name           = "lrm_v2_batch_jobdef_c1"
  type           = "container"
  tags = {
    Environment = "shared"
    Proyect     = "lrm"
  }
  platform_capabilities = [
    "FARGATE",
  ]
  timeout {
    attempt_duration_seconds = 86000
  }
  container_properties = <<CONTAINER_PROPERTIES
{
  "command":["python","main.py","0"],
  "image": "${aws_ecr_repository.lrm_v2_c1_container_registry.repository_url}",
  "fargatePlatformConfiguration": {
    "platformVersion": "LATEST"
  },
   "environment": [ 
         { 
            "name": "API_PWD",
            "value": "EEmp10200!"
         },
         { 
            "name": "SUBNETS",
            "value": "${aws_subnet.dev_a.id},${aws_subnet.dev_b.id},${aws_subnet.dev_c.id}"
         },
         {
            "name":"CREATE_NEW_CONTAINER",
            "value":"0"
         },
         { 
            "name": "SECURITY_GROUPS",
            "value": "${aws_security_group.lrm_v2_dev_sg.id}"
         },
         { 
            "name": "DB_HOSTNAME",
            "value": "${aws_db_instance.lrm_v2_dev_db.address}"
         },
         { 
            "name": "ECS_CLUSTER",
            "value": "${aws_ecs_cluster.lrm_v2_dev_ecs_cluster.name}"
         },
         { 
            "name": "ELB_ARN",
            "value": "${aws_lb_target_group.lrm_v2_dev_tg.arn}"
         },
         { 
            "name": "LOT_SIZE",
            "value": "5"
         }
      ],
    "networkConfiguration": { 
         "assignPublicIp": "ENABLED"
      },
  "resourceRequirements": [
    {"type": "VCPU", "value": "0.25"},
    {"type": "MEMORY", "value": "1024"}
  ],
  "executionRoleArn": "${aws_iam_role.lrm_v2_ecs_task_execution_role.arn}"
}
CONTAINER_PROPERTIES
}

resource "aws_batch_job_definition" "lrm_v2_batch_jobdef_datamigration" {
  propagate_tags = true
  name           = "lrm_v2_batch_jobdef_dm"
  type           = "container"
  tags = {
    Environment = "shared"
    Proyect     = "lrm"
  }
  platform_capabilities = [
    "FARGATE",
  ]
  timeout {
    attempt_duration_seconds = 86000
  }
  container_properties = <<CONTAINER_PROPERTIES
{
  "command":["python","migrate.py","redis"],
  "image": "${aws_ecr_repository.lrm_v2_datamigrations_container_registry.repository_url}",
  "fargatePlatformConfiguration": {
    "platformVersion": "LATEST"
  },
   "environment": [ 
    
         { 
            "name": "REDIS_TARGET",
            "value": "${aws_elasticache_cluster.lrm_v2_redis.cache_nodes[0].address}"
         },
         { 
            "name": "REDIS_SOURCE",
            "value": "${aws_elasticache_cluster.lrm_v2_redis_dev.cache_nodes[0].address}"
         },
         {
            "name":"MISSING_DATA",
            "value":"False"
         },
         {
            "name":"THREAD_SIZE",
            "value":"10000"
         }
         
      ],
    "networkConfiguration": { 
         "assignPublicIp": "ENABLED"
      },
  "resourceRequirements": [
    {"type": "VCPU", "value": "4"},
    {"type": "MEMORY", "value": "16384"}
  ],
  "executionRoleArn": "${aws_iam_role.lrm_v2_ecs_task_execution_role.arn}"
}
CONTAINER_PROPERTIES
}

resource "aws_batch_job_definition" "lrm_v2_batch_jobdef_datamigration_wsv2" {
  propagate_tags = true
  name           = "lrm_v2_batch_jobdef_dm_wsv2"
  type           = "container"
  tags = {
    Environment = "shared"
    Proyect     = "lrm"
  }
  platform_capabilities = [
    "FARGATE",
  ]
  timeout {
    attempt_duration_seconds = 86000
  }
  container_properties = <<CONTAINER_PROPERTIES
{
  "command":["python","migrate.py","weeklysales"],
  "image": "${aws_ecr_repository.lrm_v2_datamigrations_container_registry.repository_url}",
  "fargatePlatformConfiguration": {
    "platformVersion": "LATEST"
  },
   "environment": [ 
    
         
         
      ],
    "networkConfiguration": { 
         "assignPublicIp": "ENABLED"
      },
  "resourceRequirements": [
    {"type": "VCPU", "value": "4"},
    {"type": "MEMORY", "value": "16384"}
  ],
  "executionRoleArn": "${aws_iam_role.lrm_v2_ecs_task_execution_role.arn}"
}
CONTAINER_PROPERTIES
}

#endregion JOB DEFINITION

