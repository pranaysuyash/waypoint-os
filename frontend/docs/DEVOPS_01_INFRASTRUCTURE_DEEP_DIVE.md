# DEVOPS_01: Infrastructure Deep Dive

> Cloud setup, networking, services, and infrastructure as code

---

## Table of Contents

1. [Overview](#overview)
2. [Cloud Architecture](#cloud-architecture)
3. [Networking](#networking)
4. [Compute Services](#compute-services)
5. [Database Infrastructure](#database-infrastructure)
6. [Storage and CDN](#storage-and-cdn)
7. [DNS and SSL](#dns-and-ssl)
8. [Infrastructure as Code](#infrastructure-as-code)

---

## Overview

### Infrastructure Philosophy

```
┌─────────────────────────────────────────────────────────────────┐
│                    INFRASTRUCTURE PRINCIPLES                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ✅ Immutable Infrastructure                                     │
│     • Replace rather than modify                                 │
│     • Blue-green deployments                                     │
│                                                                  │
│  ✅ Infrastructure as Code                                       │
│     • Version controlled                                          │
│     • Reviewable and testable                                    │
│                                                                  │
│  ✅ Everything Monitored                                         │
│     • Metrics, logs, traces                                      │
│     • Alert on symptoms, not causes                              │
│                                                                  │
│  ✅ Security First                                               │
│     • Least privilege                                            │
│     • Defense in depth                                           │
│                                                                  │
│  ✅ Cost Aware                                                   │
│     • Right-sizing resources                                     │
│     • Auto-scale for efficiency                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Rationale |
|-------|-------------|-----------|
| **Cloud** | AWS (primary) / GCP (backup) | Market leader, comprehensive services |
| **Containers** | Docker + Kubernetes/ECS | Industry standard, portable |
| **Database** | PostgreSQL (RDS) | Reliable, feature-rich, SQL |
| **Cache** | ElastiCache (Redis) | Fast, managed, familiar |
| **Storage** | S3 + CloudFront | Durable, global CDN |
| **IaC** | Terraform + CDK | Declarative, multi-cloud |
| **CI/CD** | GitHub Actions | Integrated with code, free tier |

---

## Cloud Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        AWS ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                     INTERNET                               │  │
│  └───────────────────────────┬───────────────────────────────┘  │
│                            │                                     │
│                    ┌───────▼───────┐                            │
│                    │   Route 53    │                            │
│                    │   (DNS/SSL)   │                            │
│                    └───────┬───────┘                            │
│                            │                                     │
│              ┌───────────────┼───────────────┐                  │
│              │               │               │                  │
│         ┌────▼────┐    ┌─────▼─────┐   ┌───▼────┐            │
│         │ Cloud   │    │  ALB /   │   │  API   │            │
│         │ Front   │    │  NLG     │   │ Gateway│            │
│         │ (CDN)   │    └─────┬─────┘   └───┬────┘            │
│         └─────────┘          │              │                 │
│                                │              │                 │
│              ┌─────────────────┼──────────────┼─────────┐     │
│              │                 │              │         │     │
│         ┌────▼────┐      ┌────▼────┐    ┌───▼───┐ ┌──▼────┐ │
│         │  Web    │      │  App    │    │Worker│ │ bg    │ │
│         │ (ECS)   │      │ (EKS)   │    │Jobs  │ │Jobs   │ │
│         └────┬────┘      └────┬────┘    └───┬───┘ └───┬───┘ │
│              │                │             │        │      │
│              └────────────────┼─────────────┼────────┘      │
│                               │             │               │
│                    ┌──────────▼─────┐  ┌───▼────┐          │
│                    │  ElastiCache   │  │  SNS   │          │
│                    │   (Redis)      │  │  SQS   │          │
│                    └────────────────┘  └────────┘          │
│                               │                                │
│                    ┌──────────▼────────┐                     │
│                    │      RDS          │                     │
│                    │   (PostgreSQL)    │                     │
│                    │   Multi-AZ        │                     │
│                    └───────────────────┘                     │
│                                                                  │
│  VPC: 10.0.0.0/16                                                 │
│  • Public subnets: 10.0.1.0/24, 10.0.2.0/24                     │
│  • Private subnets: 10.0.10.0/24, 10.0.11.0/24                   │
│  • Data subnets: 10.0.20.0/24, 10.0.21.0/24                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Multi-Region Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                   MULTI-REGION ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Region: ap-south-1 (Mumbai) — PRIMARY                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  • Full application stack                               │    │
│  │  • Primary database (Master)                            │    │
│  │  • Active user traffic                                   │    │
│  │  • All write operations                                  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                         ┌─────┴─────┐                           │
│                         │  Replication                          │
│                         └─────┬─────┘                           │
│                              │                                   │
│  Region: ap-southeast-1 (Singapore) — DR                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  • Standby application stack                             │    │
│  │  • Read replica (async)                                  │    │
│  │  • DNS failover target                                   │    │
│  │  • Ready for failover                                    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  RTO: 15 minutes (time to operational)                          │
│  RPO: 5 minutes (max data loss)                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Networking

### VPC Configuration

```hcl
# Terraform VPC configuration
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "${var.project}-vpc"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# Public subnets (for ALB, NAT Gateway)
resource "aws_subnet" "public" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 1}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project}-public-${count.index + 1}"
    Type = "public"
  }
}

# Private subnets (for ECS/EKS)
resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 10}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "${var.project}-private-${count.index + 1}"
    Type = "private"
  }
}

# Data subnets (for RDS)
resource "aws_subnet" "data" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 20}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "${var.project}-data-${count.index + 1}"
    Type = "data"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project}-igw"
  }
}

# NAT Gateway for outbound internet access
resource "aws_nat_gateway" "main" {
  count         = 2
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = {
    Name = "${var.project}-nat-${count.index + 1}"
  }

  depends_on = [aws_internet_gateway.main]
}

resource "aws_eip" "nat" {
  count = 2
  vpc   = true

  tags = {
    Name = "${var.project}-eip-${count.index + 1}"
  }
}

# Route tables
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "${var.project}-public-rt"
  }
}

resource "aws_route_table" "private" {
  count  = 2
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[count.index].id
  }

  tags = {
    Name = "${var.project}-private-rt-${count.index + 1}"
  }
}

# Route table associations
resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count          = 2
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

# VPC Endpoints (for private AWS API access)
resource "aws_vpc_endpoint" "s3" {
  vpc_id       = aws_vpc.main.id
  service_name = "com.amazonaws.ap-south-1.s3"

  route_table_ids = aws_route_table.private[*].id

  tags = {
    Name = "${var.project}-s3-endpoint"
  }
}

resource "aws_vpc_endpoint" "ecr_dkr" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.ap-south-1.ecr.dkr"
  vpc_endpoint_type = "Interface"

  security_group_ids = [aws_security_group.vpc_endpoints.id]
  subnet_ids         = aws_subnet.private[*].id

  private_dns_enabled = true

  tags = {
    Name = "${var.project}-ecr-dkr-endpoint"
  }
}

resource "aws_vpc_endpoint" "ecr_api" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.ap-south-1.ecr.api"
  vpc_endpoint_type = "Interface"

  security_group_ids = [aws_security_group.vpc_endpoints.id]
  subnet_ids         = aws_subnet.private[*].id

  private_dns_enabled = true

  tags = {
    Name = "${var.project}-ecr-api-endpoint"
  }
}
```

### Security Groups

```hcl
# Application Load Balancer security group
resource "aws_security_group" "alb" {
  name        = "${var.project}-alb-sg"
  description = "Security group for ALB"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTP from internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS from internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project}-alb-sg"
  }
}

# ECS/EKS tasks security group
resource "aws_security_group" "app" {
  name        = "${var.project}-app-sg"
  description = "Security group for application containers"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "HTTP from ALB"
    from_port       = 3000
    to_port         = 3000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  ingress {
    description     = "Health checks"
    from_port       = 9090
    to_port         = 9090
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project}-app-sg"
  }
}

# RDS security group
resource "aws_security_group" "rds" {
  name        = "${var.project}-rds-sg"
  description = "Security group for RDS"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "PostgreSQL from app"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  tags = {
    Name = "${var.project}-rds-sg"
  }
}

# ElastiCache security group
resource "aws_security_group" "redis" {
  name        = "${var.project}-redis-sg"
  description = "Security group for ElastiCache"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Redis from app"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  tags = {
    Name = "${var.project}-redis-sg"
  }
}
```

---

## Compute Services

### ECS Configuration

```hcl
# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.project}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Environment = var.environment
  }
}

# Capacity Provider (FARGATE)
resource "aws_ecs_capacity_provider" "fargate" {
  name = "${var.project}-fargate"

  auto_scaling_group_provider {
    auto_scaling_group_arn         = aws_autoscaling_group.app.arn
    managed_termination_protection = "ENABLED"
    managed_scaling {
      maximum_scaling_step_size = 10
      minimum_scaling_step_size = 1
      status                    = "ENABLED"
      target_capacity           = 80
    }
  }
}

# Task Definition
resource "aws_ecs_task_definition" "app" {
  family                   = "${var.project}-app"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.app_cpu
  memory                   = var.app_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "app"
      image     = "${var.ecr_repository}/${var.app_image}:${var.app_version}"
      cpu       = var.app_cpu
      memory    = var.app_memory
      essential = true

      portMappings = [
        {
          containerPort = 3000
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "NODE_ENV"
          value = var.environment
        },
        {
          name  = "PORT"
          value = "3000"
        }
      ]

      secrets = [
        {
          name      = "DATABASE_URL"
          valueFrom = aws_secretsmanager_secret.database_url.arn
        },
        {
          name      = "JWT_SECRET"
          valueFrom = aws_secretsmanager_secret.jwt_secret.arn
        },
        {
          name      = "REDIS_URL"
          valueFrom = aws_secretsmanager_secret.redis_url.arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.app.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "app"
          "awslogs-create-group"  = "true"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:3000/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])

  tags = {
    Environment = var.environment
  }
}

# Service
resource "aws_ecs_service" "app" {
  name            = "${var.project}-app"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = var.app_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.app.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.app.arn
    container_name   = "app"
    container_port   = 3000
  }

  # Deployment configuration
  deployment_configuration {
    maximum_percent         = 200
    minimum_healthy_percent = 100
    deployment_circuit_breaker {
      enable   = true
      rollback = true
    }
  }

  # Auto-scaling
  enable_execute_command = true

  tags = {
    Environment = var.environment
  }
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "${var.project}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  enable_deletion_protection = false

  access_logs {
    bucket  = aws_s3_bucket.logs.id
    prefix  = "alb-logs"
    enabled = true
  }

  tags = {
    Environment = var.environment
  }
}

# ALB Target Group
resource "aws_lb_target_group" "app" {
  name        = "${var.project}-tg"
  port        = 3000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    enabled             = true
    path                = "/health"
    matcher             = "200"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }

  tags = {
    Environment = var.environment
  }
}

# ALB Listener
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = 443
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01" # Strict TLS
  certificate_arn   = var.acm_certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}

# Auto-scaling for ECS
resource "aws_appautoscaling_target" "app" {
  max_capacity       = 10
  min_capacity       = 2
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.app.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

# Scale based on CPU
resource "aws_appautoscaling_policy" "cpu" {
  name               = "${var.project}-cpu-autoscaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.app.resource_id
  scalable_dimension = aws_appautoscaling_target.app.scalable_dimension
  service_namespace  = aws_appautoscaling_target.app.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = 70.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}

# Scale based on memory
resource "aws_appautoscaling_policy" "memory" {
  name               = "${var.project}-memory-autoscaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.app.resource_id
  scalable_dimension = aws_appautoscaling_target.app.scalable_dimension
  service_namespace  = aws_appautoscaling_target.app.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
    target_value       = 80.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}
```

---

## Database Infrastructure

### RDS PostgreSQL

```hcl
# RDS Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "${var.project}-db-subnet-group"
  subnet_ids = aws_subnet.data[*].id

  tags = {
    Name = "${var.project}-db-subnet-group"
  }
}

# RDS Parameter Group
resource "aws_db_parameter_group" "main" {
  name   = "${var.project}-db-params"
  family = "postgres15"

  parameter {
    name  = "shared_buffers"
    value = "0.25 * {DBInstanceClassMemory}"
  }

  parameter {
    name  = "effective_cache_size"
    value = "0.75 * {DBInstanceClassMemory}"
  }

  parameter {
    name  = "work_mem"
    value = "4096"
  }

  parameter {
    name  = "maintenance_work_mem"
    value = "1GB"
  }

  parameter {
    name  = "max_connections"
    value = "200"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "1000" # Log slow queries (>1s)
  }

  tags = {
    Environment = var.environment
  }
}

# Primary RDS Instance
resource "aws_db_instance" "main" {
  identifier = "${var.project}-db-${var.environment}"

  engine         = "postgres"
  engine_version = "15.4"
  instance_class = var.db_instance_class

  allocated_storage     = 100
  max_allocated_storage = 1000
  storage_type          = "gp3"
  storage_encrypted     = true
  kms_key_id            = var.kms_key_arn

  db_name  = "travelagency"
  username = var.db_username
  password = var.db_password

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  multi_az               = true
  db_subnet_group_name   = aws_db_subnet_group.main.name

  backup_retention_period = 30
  backup_window          = "03:00-04:00"
  maintenance_window     = "Mon:04:00-Mon:05:00"

  final_snapshot_identifier = "${var.project}-db-final-${var.environment}"
  skip_final_snapshot     = false
  delete_automated_backups = false

  performance_insights_enabled = true
  monitoring_interval         = 60
  monitoring_role_arn         = aws_iam_role.rds_monitoring.arn

  parameter_group_name = aws_db_parameter_group.main.name

  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]

  tags = {
    Environment = var.environment
    Name        = "${var.project}-db"
  }
}

# Read Replica
resource "aws_db_instance" "replica" {
  count = var.environment == "production" ? 1 : 0

  identifier = "${var.project}-db-${var.environment}-replica"

  replicate_source_db = aws_db_instance.main.identifier

  engine         = aws_db_instance.main.engine
  engine_version = aws_db_instance.main.engine_version
  instance_class = var.db_instance_class

  storage_encrypted = true
  kms_key_id       = var.kms_key_arn

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  backup_retention_period = 7
  skip_final_snapshot     = true

  performance_insights_enabled = false

  parameter_group_name = aws_db_parameter_group.main.name

  tags = {
    Environment = var.environment
    Name        = "${var.project}-db-replica"
  }
}

# RDS Proxy (for connection pooling)
resource "aws_rds_proxy" "main" {
  name                   = "${var.project}-proxy"
  debug_logging           = false
  engine_family          = "POSTGRESQL"
  require_tls            = true
  idle_client_timeout    = 1800
  vpc_subnet_ids         = aws_subnet.private[*].id
  vpc_security_group_ids = [aws_security_group.rds.id]

  auth {
    auth_scheme = "SECRETS"
    secret_arn  = aws_secretsmanager_secret.db_creds.arn
  }

  role_arn = aws_iam_role.rds_proxy.arn

  depends_on = [aws_db_instance.main]

  tags = {
    Environment = var.environment
  }
}

resource "aws_rds_proxy_default_target_group" "main" {
  db_proxy_name = aws_rds_proxy.main.name

  connection_pool_config {
    connection_borrow_timeout    = 120
    max_connections_percent      = 100
    max_idle_connections_percent = 50
    session_pinning_filters      = ["EXCLUDE_VARIABLE_SETS"]
  }
}

resource "aws_rds_proxy_target" "main" {
  db_proxy_name          = aws_rds_proxy.main.name
  db_instance_identifier = aws_db_instance.main.identifier
  db_cluster_identifier  = null
  target_group_name      = aws_rds_proxy_default_target_group.main.name
}
```

### ElastiCache Redis

```hcl
# ElastiCache Subnet Group
resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.project}-cache-subnet-group"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "${var.project}-cache-subnet-group"
  }
}

# Redis Parameter Group
resource "aws_elasticache_parameter_group" "main" {
  name   = "${var.project}-redis-params"
  family = "redis7"

  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }

  parameter {
    name  = "timeout"
    value = "300"
  }
}

# Redis Replication Group
resource "aws_elasticache_replication_group" "main" {
  replication_group_id       = "${var.project}-redis-${var.environment}"
  replication_group_description = "${var.project} Redis cluster"

  engine               = "redis"
  engine_version        = "7.0"
  node_type            = var.redis_node_type
  num_cache_clusters   = 2
  port                 = 6379
  parameter_group_name = aws_elasticache_parameter_group.main.name

  automatic_failover_enabled = true
  multi_az_enabled          = true

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                = var.redis_auth_token

  subnet_group_name  = aws_elasticache_subnet_group.main.name
  security_group_ids = [aws_security_group.redis.id]

  snapshot_window          = "03:00-05:00"
  snapshot_retention_limit = 7

  log_delivery_configuration {
    destination      = aws_cloudwatch_log_group.redis.name
    destination_type = "cloudwatch-logs"
  }

  tags = {
    Environment = var.environment
    Name        = "${var.project}-redis"
  }
}
```

---

## Storage and CDN

### S3 Buckets

```hcl
# Application assets bucket
resource "aws_s3_bucket" "assets" {
  bucket = "${var.project}-assets-${var.environment}-${data.aws_caller_identity.current.account_id}"

  tags = {
    Environment = var.environment
  }
}

resource "aws_s3_bucket_versioning" "assets" {
  bucket = aws_s3_bucket.assets.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "assets" {
  bucket = aws_s3_bucket.assets.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "assets" {
  bucket = aws_s3_bucket.assets.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# CloudFront Origin Access Control
resource "aws_cloudfront_origin_access_control" "assets" {
  name                              = "${var.project}-assets-oac"
  description                       = "OAC for assets bucket"
  origin_access_control_origin_type = "s3"
}

# CloudFront Distribution
resource "aws_cloudfront_distribution" "assets" {
  enabled             = true
  is_ipv6_enabled     = true
  price_class         = "PriceClass_100" # India, US, Europe only
  http_version        = "http2and3"
  comment             = "${var.project} assets CDN - ${var.environment}"

  origin {
    domain_name              = aws_s3_bucket.assets.bucket_regional_domain_name
    origin_access_control_id = aws_cloudfront_origin_access_control.assets.id
    origin_id                = "S3-${aws_s3_bucket.assets.id}"

    s3_origin_config {
      origin_access_identity = "" # Use OAC instead
    }
  }

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-${aws_s3_bucket.assets.id}"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 86400    # 1 day
    default_ttl            = 604800   # 7 days
    max_ttl                = 31536000 # 1 year
    compress               = true

    function_association {
      function_arn = aws_cloudfront_function.security_headers.arn
    }
  }

  ordered_cache_behavior {
    path_pattern     = "/assets/*"
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-${aws_s3_bucket.assets.id}"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    min_ttl                = 31536000 # 1 year - immutable assets
    default_ttl            = 31536000
    max_ttl                = 31536000
    compress               = false
    viewer_protocol_policy = "redirect-to-https"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn      = var.acm_certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  tags = {
    Environment = var.environment
  }
}

# CloudFront Function for security headers
resource "aws_cloudfront_function" "security_headers" {
  name    = "${var.project}-security-headers"
  runtime = "cloudfront-js-1.0"
  publish = true
  code    = file("${path.module}/cloudfront-functions/security-headers.js")
}

# Document storage bucket (private)
resource "aws_s3_bucket" "documents" {
  bucket = "${var.project}-documents-${var.environment}-${data.aws_caller_identity.current.account_id}"

  tags = {
    Environment = var.environment
  }
}

resource "aws_s3_bucket_versioning" "documents" {
  bucket = aws_s3_bucket.documents.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "documents" {
  bucket = aws_s3_bucket.documents.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
      kms_key_id   = var.documents_kms_key_arn
    }
  }
}

resource "aws_s3_bucket_public_access_block" "documents" {
  bucket = aws_s3_bucket.documents.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle policy for documents
resource "aws_s3_bucket_lifecycle_configuration" "documents" {
  bucket = aws_s3_bucket.documents.id

  rule {
    id     = "archive-old-documents"
    status = "enabled"

    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 180
      storage_class = "GLACIER"
    }

    expiration {
      days = 2555 # 7 years
    }
  }
}

# Audit logs bucket
resource "aws_s3_bucket" "logs" {
  bucket = "${var.project}-logs-${var.environment}-${data.aws_caller_identity.current.account_id}"

  tags = {
    Environment = var.environment
  }
}

resource "aws_s3_bucket_versioning" "logs" {
  bucket = aws_s3_bucket.logs.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "logs" {
  bucket = aws_s3_bucket.logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id

  rule {
    id     = "archive-old-logs"
    status = "enabled"

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    expiration {
      days = 730 # 2 years
    }
  }
}
```

---

## DNS and SSL

### Route53 Configuration

```hcl
# Hosted Zone
resource "aws_route53_zone" "main" {
  name = var.domain_name

  tags = {
    Environment = var.environment
  }
}

# A record for application
resource "aws_route53_record" "app" {
  name    = var.environment === "production" ? "app" : "${var.environment}-app"
  zone_id = aws_route53_zone.main.zone_id
  type    = "A"

  alias {
    name                   = aws_lb.main.dns_name
    zone_id                = aws_lb.main.zone_id
    evaluate_target_health = true
  }
}

# A record for API
resource "aws_route53_record" "api" {
  name    = var.environment === "production" ? "api" : "${var.environment}-api"
  zone_id = aws_route53_zone.main.zone_id
  type    = "A"

  alias {
    name                   = aws_lb.main.dns_name
    zone_id                = aws_lb.main.zone_id
    evaluate_target_health = true
  }
}

# CNAME for CDN
resource "aws_route53_record" "cdn" {
  name    = var.environment === "production" ? "cdn" : "${var.environment}-cdn"
  zone_id = aws_route53_zone.main.zone_id
  type    = "CNAME"
  ttl     = 300

  records = [aws_cloudfront_distribution.assets.domain_name]
}

# Health check for failover
resource "aws_route53_health_check" "app" {
  fqdn              = "${var.environment}-app.${var.domain_name}"
  port              = 443
  type              = "HTTPS"
  resource_path     = "/health"
  request_interval  = 30
  failure_threshold = 3

  tags = {
    Environment = var.environment
  }
}
```

### SSL Certificate

```hcl
# ACM Certificate
resource "aws_acm_certificate" "main" {
  domain_name       = var.domain_name
  validation_method = "DNS"

  subject_alternative_names = [
    "*.${var.domain_name}",
    "app.${var.domain_name}",
    "api.${var.domain_name}",
    "cdn.${var.domain_name}",
  ]

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Environment = var.environment
  }
}

# DNS validation records
resource "aws_route53_record" "cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.main.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name           = each.value.name
  records        = [each.value.record]
  ttl            = 60
  type           = each.value.type
  zone_id        = aws_route53_zone.main.zone_id
}

# Wait for certificate validation
resource "aws_acm_certificate_validation" "main" {
  certificate_arn         = aws_acm_certificate.main.arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]
}
```

---

## Infrastructure as Code

### Project Structure

```
terraform/
├── modules/
│   ├── vpc/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── ecs/
│   ├── rds/
│   ├── redis/
│   └── s3/
├── environments/
│   ├── development/
│   │   ├── backend.tf
│   │   ├── main.tf
│   │   └── terraform.tfvars
│   ├── staging/
│   └── production/
└── README.md
```

### Main Terraform Config

```hcl
# environments/production/main.tf
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "travel-agency-terraform-state"
    key            = "environments/production/terraform.tfstate"
    region         = "ap-south-1"
    encrypt        = true
    dynamodb_table = "travel-agency-terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# VPC module
module "vpc" {
  source = "../../modules/vpc"

  project     = var.project
  environment = var.environment
  cidr        = "10.0.0.0/16"

  azs             = ["ap-south-1a", "ap-south-1b"]
  public_subnets  = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnets = ["10.0.10.0/24", "10.0.11.0/24"]
  data_subnets    = ["10.0.20.0/24", "10.0.21.0/24"]
}

# ECS module
module "ecs" {
  source = "../../modules/ecs"

  project     = var.project
  environment = var.environment

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnet_ids

  cluster_name = "${var.project}-cluster"

  app = {
    image           = var.app_image
    version         = var.app_version
    cpu             = 1024
    memory          = 2048
    desired_count   = 3
    health_check_path = "/health"
  }

  alb = {
    certificate_arn = var.acm_certificate_arn
    domain_name     = "app.${var.domain_name}"
  }

  secrets = {
    database_url = aws_secretsmanager_secret.database_url.arn
    jwt_secret   = aws_secretsmanager_secret.jwt_secret.arn
    redis_url    = aws_secretsmanager_secret.redis_url.arn
  }
}

# RDS module
module "rds" {
  source = "../../modules/rds"

  project     = var.project
  environment = var.environment

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.data_subnet_ids

  instance_class = "db.r6g.xlarge"
  multi_az       = true

  database_name   = "travelagency"
  master_username = var.db_username

  backup_retention = 30
  enable_read_replica = true
}

# Redis module
module "redis" {
  source = "../../modules/redis"

  project     = var.project
  environment = var.environment

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnet_ids

  node_type = "cache.r6g.large"
  num_cache_clusters = 2
}
```

---

**Last Updated:** 2026-04-25

**Next:** DEVOPS_02 — CI/CD Deep Dive (Build pipeline, deployments, releases)
