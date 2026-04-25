# DEVOPS_04: Scaling & Performance Deep Dive

> Comprehensive guide to scaling strategies, load balancing, caching, and performance optimization for the Travel Agency Agent platform

---

## Table of Contents

1. [Overview](#overview)
2. [Scaling Philosophy](#scaling-philosophy)
3. [Horizontal Scaling](#horizontal-scaling)
4. [Vertical Scaling](#vertical-scaling)
5. [Auto-Scaling Strategies](#auto-scaling-strategies)
6. [Load Balancing](#load-balancing)
7. [Caching Architecture](#caching-architecture)
8. [Database Scaling](#database-scaling)
9. [Queue-Based Processing](#queue-based-processing)
10. [Rate Limiting](#rate-limiting)
11. [Cost Optimization](#cost-optimization)

---

## Overview

### Goals

- **Elasticity**: Automatically scale resources based on demand
- **Performance**: Maintain low latency under high load
- **Efficiency**: Optimize resource utilization and cost
- **Resilience**: Handle component failures gracefully

### Scaling Dimensions

```
┌─────────────────────────────────────────────────────────────────┐
│                    SCALING DIMENSIONS                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   SCALE OUT     │  │   SCALE UP      │  │   CACHE         │ │
│  │  (Horizontal)   │  │  (Vertical)     │  │  (Read-heavy)   │ │
│  │                 │  │                 │  │                 │ │
│  │ • Add instances │  │ • Bigger VMs    │  │ • Redis         │ │
│  │ • Multi-AZ      │  │ • More CPU/RAM  │  │ • CDN           │ │
│  │ • Containers    │  │ • Better I/O    │  │ • Edge          │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│                                                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   DATABASE      │  │   ASYNC         │  │   SHARD         │ │
│  │   (Data Layer)  │  │   (Queue)       │  │   (Partition)   │ │
│  │                 │  │                 │  │                 │ │
│  │ • Read replicas │  │ • Job queues   │  │ • By customer   │ │
│  │ • Connection    │  │ • Event driven │  │ • By region     │ │
│  │   pooling       │  │ • Background   │  │ • By time       │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Scaling Approach |
|-------|-----------|------------------|
| **Application** | ECS/EKS, Cloud Run | Horizontal auto-scaling |
| **Load Balancer** | ALB, NLB, Cloud LB | Managed, auto-scales |
| **Cache** | ElastiCache, Memorystore | Horizontal, read replicas |
| **Database** | RDS, Cloud SQL | Vertical + read replicas |
| **CDN** | CloudFront, Cloud CDN | Global edge network |
| **Queue** | SQS, Pub/Sub | Horizontal consumers |

---

## Scaling Philosophy

### Scale Triggers

```
┌────────────────────────────────────────────────────────────────┐
│                     SCALING DECISION TREE                       │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Current Load                                                  │
│       │                                                        │
│       ▼                                                        │
│  ┌─────────┐                                                   │
│  │ CPU < 60%│  → No action needed                             │
│  └────┬────┘                                                   │
│       │                                                        │
│       ▼ CPU > 80%                                              │
│  ┌─────────┐                                                   │
│  │ Spike?  │                                                   │
│  └────┬────┘                                                   │
│    ┌──┴──┐                                                      │
│    │     │                                                      │
│   Yes   No                                                     │
│    │     │                                                      │
│    ▼     ▼                                                      │
│  ┌──────┐ ┌──────────┐                                        │
│  │Queue │ │Scale Out │                                        │
│  │Jobs  │ │+2 inst.  │                                        │
│  └──────┘ └──────────┘                                        │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Scaling Metrics

| Metric | Scale Out Threshold | Scale In Threshold |
|--------|---------------------|-------------------|
| **CPU Utilization** | > 70% for 3 minutes | < 30% for 10 minutes |
| **Memory Utilization** | > 80% for 3 minutes | < 40% for 10 minutes |
| **Request Rate** | > 1000 req/min per instance | < 200 req/min per instance |
| **Response Time** | p95 > 1 second | p95 < 200ms |
| **Queue Depth** | > 1000 messages | < 100 messages |

### Scaling Policies

```typescript
// lib/scaling/policies.ts

export interface ScalingPolicy {
  name: string;
  resourceType: 'ecs' | 'rds' | 'elasticache' | 'sqs';
  metric: string;
  target: number;
  scaleOutCooldown: number; // seconds
  scaleInCooldown: number; // seconds
  minCapacity: number;
  maxCapacity: number;
}

export const scalingPolicies: ScalingPolicy[] = [
  {
    name: 'api-server-scaling',
    resourceType: 'ecs',
    metric: 'CPUUtilization',
    target: 70,
    scaleOutCooldown: 300,
    scaleInCooldown: 600,
    minCapacity: 2,
    maxCapacity: 50,
  },
  {
    name: 'worker-scaling',
    resourceType: 'ecs',
    metric: 'CPUUtilization',
    target: 80,
    scaleOutCooldown: 60,
    scaleInCooldown: 300,
    minCapacity: 1,
    maxCapacity: 100,
  },
  {
    name: 'redis-scaling',
    resourceType: 'elasticache',
    metric: 'DatabaseMemoryUsagePercentage',
    target: 80,
    scaleOutCooldown: 600,
    scaleInCooldown: 1800,
    minCapacity: 1,
    maxCapacity: 6,
  },
];
```

---

## Horizontal Scaling

### Container Orchestration

```typescript
// infrastructure/terraform/ecs-service.tf

resource "aws_ecs_task_definition" "api" {
  family                   = "travel-agency-api"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.task_cpu
  memory                   = var.task_memory
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "api"
      image     = "${var.ecr_repository_url}:${var.image_tag}"
      cpu       = var.task_cpu
      memory    = var.task_memory
      essential = true

      environment = [
        { name = "NODE_ENV", value = var.environment },
        { name = "PORT", value = "3000" },
      ]

      secrets = [
        { name = "DATABASE_URL", valueFrom = aws_secretsmanager_secret.database_url.arn },
        { name = "JWT_SECRET", valueFrom = aws_secretsmanager_secret.jwt_secret.arn },
      ]

      portMappings = [
        {
          containerPort = 3000
          protocol      = "tcp"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.api.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "api"
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

      readonlyRootFilesystem = false
      tmpfs = {
        "/tmp" = "size=100"
      }

      ulimits = [
        {
          name = "nofile"
          soft = 65536
          hard = 65536
        }
      ]
    }
  ])

  tags = var.common_tags
}

resource "aws_ecs_service" "api" {
  name            = "travel-agency-api"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = var.api_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.api.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = 3000
  }

  # Enable deployment circuit breaker
  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  # Deployment configuration
  deployment_configuration {
    maximum_percent         = 200
    minimum_healthy_percent = 50
    deployment_circuit_breaker {
      enable   = true
      rollback = true
    }
  }

  # Enable service discovery
  service_registries {
    registry_arn = aws_service_discovery_service.api.arn
  }

  tags = var.common_tags

  # Enable auto-scaling
  depends_on = [aws_appautoscaling_target.api]
}

# Auto-scaling target
resource "aws_appautoscaling_target" "api" {
  max_capacity       = var.api_max_capacity
  min_capacity       = var.api_min_capacity
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.api.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

# Scale out policy
resource "aws_appautoscaling_policy" "api_scale_out" {
  name               = "api-scale-out"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.api.resource_id
  scalable_dimension = aws_appautoscaling_target.api.scalable_dimension
  service_namespace  = aws_appautoscaling_target.api.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = 70.0
    scale_in_cooldown  = 600
    scale_out_cooldown = 300
  }
}

# Scale in policy (memory-based)
resource "aws_appautoscaling_policy" "api_scale_in_memory" {
  name               = "api-scale-in-memory"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.api.resource_id
  scalable_dimension = aws_appautoscaling_target.api.scalable_dimension
  service_namespace  = aws_appautoscaling_target.api.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
    target_value       = 80.0
    scale_in_cooldown  = 600
    scale_out_cooldown = 300
  }
}
```

### Multi-AZ Deployment

```hcl
# infrastructure/terraform/multi-az.tf

# Application Load Balancer with cross-zone load balancing
resource "aws_lb" "api" {
  name               = "travel-agency-api-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.public_subnet_ids

  enable_deletion_protection = false
  enable_http2              = true

  # Cross-zone load balancing
  enable_cross_zone_load_balancing = true

  # Access logs
  access_logs {
    bucket  = aws_s3_bucket.alb_logs.id
    prefix  = "api-alb-logs"
    enabled = true
  }

  tags = var.common_tags
}

# Target group spread across multiple AZs
resource "aws_lb_target_group" "api" {
  name        = "travel-agency-api-tg"
  port        = 3000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    path                = "/health"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    matcher             = "200"
  }

  # Stickiness for session affinity
  stickiness {
    type            = "lb_cookie"
    cookie_duration = 86400
    enabled         = true
  }

  tags = var.common_tags
}

# ECS Service spread across AZs
resource "aws_ecs_service" "api" {
  name            = "travel-agency-api"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = var.api_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = var.private_subnet_ids
    security_groups = [aws_security_group.api.id]
  }

  # Spread tasks across AZs
  ordered_placement_strategy {
    type  = "spread"
    field = "attribute:ecs.availability-zone"
  }

  # Capacity provider strategy
  capacity_provider_strategy {
    capacity_provider = "FARGATE"
    weight            = 1
    base              = 1
  }

  capacity_provider_strategy {
    capacity_provider = "FARGATE_SPOT"
    weight            = 4
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = 3000
  }

  tags = var.common_tags
}
```

---

## Vertical Scaling

### Database Instance Scaling

```hcl
# infrastructure/terraform/rds.tf

resource "aws_db_instance" "main" {
  identifier = "travel-agency-db"

  engine         = "postgres"
  engine_version = "15.4"
  instance_class = var.db_instance_class  # db.t3.medium, db.r6g.large, etc.

  allocated_storage     = 100
  max_allocated_storage = 1000  # Enable auto-scaling storage
  storage_type          = "gp3"
  storage_encrypted     = true
  kms_key_id           = var.kms_key_id

  db_name  = "travel_agency"
  username = var.db_username
  password = var.db_password

  vpc_security_group_ids = [aws_security_group.database.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  multi_az               = var.enable_multi_az
  db_subnet_group_name   = aws_db_subnet_group.main.name

  # Backup and maintenance
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "Mon:04:00-Mon:05:00"

  # Performance
  performance_insights_enabled = true
  monitoring_interval         = 60
  monitoring_role_arn        = aws_iam_role.rds_monitoring.arn

  # Parameters
  parameter_group_name = aws_db_parameter_group.main.name

  # Deletion protection
  deletion_protection = true
  skip_final_snapshot = false
  final_snapshot_identifier = "travel-agency-final-snapshot"

  tags = var.common_tags
}

# Parameter group for performance tuning
resource "aws_db_parameter_group" "main" {
  name   = "travel-agency-pg"
  family = "postgres15"

  # Connection pooling
  parameter {
    name  = "shared_buffers"
    value = "{DBInstanceClassMemory/32}"
  }

  parameter {
    name  = "effective_cache_size"
    value = "{DBInstanceClassMemory/4}"
  }

  parameter {
    name  = "max_connections"
    value = "200"
  }

  # Workload optimization
  parameter {
    name  = "random_page_cost"
    value = "1.1"  # For SSD storage
  }

  parameter {
    name  = "work_mem"
    value = "4096"
  }

  # Logging
  parameter {
    name  = "log_statement"
    value = "ddl"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "1000"  # Log queries > 1s
  }
}

# Instance class upgrade (vertical scaling)
resource "aws_db_instance" "main_upgrade" {
  # For vertical scaling, create new instance with larger class
  # and migrate via snapshot restore

  identifier     = "travel-agency-db-upgraded"
  instance_class = "db.r6g.2xlarge"  # Larger instance

  # Snapshot from existing instance
  snapshot_identifier = aws_db_instance.main.final_snapshot_identifier

  # ... rest of configuration
}
```

### Scaling Decision Service

```typescript
// lib/scaling/scaling-decision.ts

export interface ScalingRecommendation {
  action: 'scale_out' | 'scale_in' | 'scale_up' | 'scale_down' | 'none';
  resource: string;
  currentValue: number;
  threshold: number;
  recommendedSize?: string;
  reason: string;
}

export class ScalingDecisionService {
  async analyzeResource(resourceId: string): Promise<ScalingRecommendation> {
    const metrics = await this.getCurrentMetrics(resourceId);
    const policy = this.getPolicyForResource(resourceId);

    // Check scale out conditions
    if (metrics.cpu > policy.scaleOutThreshold) {
      return {
        action: 'scale_out',
        resource: resourceId,
        currentValue: metrics.cpu,
        threshold: policy.scaleOutThreshold,
        reason: `CPU usage (${metrics.cpu}%) exceeds threshold (${policy.scaleOutThreshold}%)`,
      };
    }

    // Check scale in conditions
    if (metrics.cpu < policy.scaleInThreshold && metrics.instanceCount > policy.minInstances) {
      return {
        action: 'scale_in',
        resource: resourceId,
        currentValue: metrics.cpu,
        threshold: policy.scaleInThreshold,
        recommendedSize: String(Math.max(policy.minInstances, metrics.instanceCount - 1)),
        reason: `CPU usage (${metrics.cpu}%) below threshold (${policy.scaleInThreshold}%)`,
      };
    }

    // Check for memory pressure (vertical scaling indicator)
    if (metrics.memory > 90 && metrics.memoryUtilizationTrend === 'increasing') {
      return {
        action: 'scale_up',
        resource: resourceId,
        currentValue: metrics.memory,
        threshold: 90,
        reason: 'Sustained high memory usage indicates need for larger instance type',
      };
    }

    return {
      action: 'none',
      resource: resourceId,
      currentValue: metrics.cpu,
      threshold: policy.scaleOutThreshold,
      reason: 'Current metrics within acceptable range',
    };
  }

  private async getCurrentMetrics(resourceId: string): Promise<any> {
    // Fetch from CloudWatch
  }

  private getPolicyForResource(resourceId: string): any {
    // Fetch scaling policy
  }
}
```

---

## Auto-Scaling Strategies

### Predictive Scaling

```typescript
// lib/scaling/predictive-scaling.ts

export interface TrafficPattern {
  timestamp: Date;
  requestCount: number;
  dayOfWeek: number;
  hour: number;
}

export class PredictiveScalingService {
  private historicalData: TrafficPattern[] = [];
  private readonly PREDICTION_WINDOW = 24 * 60 * 60 * 1000; // 24 hours

  async trainModel(): Promise<void> {
    // Load last 30 days of traffic data
    const endDate = new Date();
    const startDate = new Date(endDate.getTime() - 30 * 24 * 60 * 60 * 1000);

    this.historicalData = await this.loadTrafficData(startDate, endDate);
  }

  async predictLoad(hoursAhead: number): Promise<number> {
    const now = new Date();
    const targetTime = new Date(now.getTime() + hoursAhead * 60 * 60 * 1000);
    const dayOfWeek = targetTime.getDay();
    const hour = targetTime.getHours();

    // Find similar historical periods
    const similarPeriods = this.historicalData.filter(
      (d) => d.dayOfWeek === dayOfWeek && Math.abs(d.hour - hour) < 1
    );

    if (similarPeriods.length === 0) {
      return this.getAverageLoad();
    }

    // Calculate weighted average (more recent = higher weight)
    let weightedSum = 0;
    let totalWeight = 0;

    similarPeriods.forEach((period) => {
      const age = now.getTime() - period.timestamp.getTime();
      const weight = Math.exp(-age / (7 * 24 * 60 * 60 * 1000)); // 7-day half-life
      weightedSum += period.requestCount * weight;
      totalWeight += weight;
    });

    return weightedSum / totalWeight;
  }

  async generateScalingSchedule(): Promise<Map<number, number>> {
    const schedule = new Map<number, number>();

    for (let hour = 0; hour < 24; hour++) {
      const predictedLoad = await this.predictLoad(hour);
      const requiredInstances = Math.ceil(predictedLoad / this.getRequestsPerInstance());
      schedule.set(hour, requiredInstances);
    }

    return schedule;
  }

  private getRequestsPerInstance(): number {
    return 500; // Each instance handles 500 requests/minute
  }

  private getAverageLoad(): number {
    return this.historicalData.reduce((sum, d) => sum + d.requestCount, 0) / this.historicalData.length;
  }

  private async loadTrafficData(start: Date, end: Date): Promise<TrafficPattern[]> {
    // Fetch from CloudWatch or analytics database
    return [];
  }
}
```

### Scheduled Scaling

```typescript
// lib/scaling/scheduled-scaling.ts

export interface ScheduledScalingAction {
  name: string;
  startTime: string; // cron format
  endTime: string;
  minCapacity: number;
  maxCapacity: number;
  desiredCapacity: number;
}

export const scheduledScalingActions: ScheduledScalingAction[] = [
  {
    name: 'morning-ramp-up',
    startTime: '0 6 * * MON-FRI', // 6 AM weekdays
    endTime: '0 9 * * MON-FRI',
    minCapacity: 4,
    maxCapacity: 20,
    desiredCapacity: 8,
  },
  {
    name: 'business-hours',
    startTime: '0 9 * * MON-FRI', // 9 AM weekdays
    endTime: '0 18 * * MON-FRI',
    minCapacity: 8,
    maxCapacity: 50,
    desiredCapacity: 15,
  },
  {
    name: 'evening-ramp-down',
    startTime: '0 18 * * MON-FRI', // 6 PM weekdays
    endTime: '0 22 * * MON-FRI',
    minCapacity: 4,
    maxCapacity: 20,
    desiredCapacity: 6,
  },
  {
    name: 'off-hours',
    startTime: '0 22 * * MON-FRI', // 10 PM weekdays
    endTime: '0 6 * * MON-FRI',
    minCapacity: 2,
    maxCapacity: 10,
    desiredCapacity: 2,
  },
  {
    name: 'weekend-baseline',
    startTime: '0 0 * * SAT,SUN',
    endTime: '0 0 * * MON',
    minCapacity: 2,
    maxCapacity: 10,
    desiredCapacity: 2,
  },
];
```

### Step Scaling

```typescript
// lib/scaling/step-scaling.ts

export interface StepAdjustment {
  metricIntervalLowerBound?: number;
  metricIntervalUpperBound: number;
  scalingAdjustment: number;
}

export interface StepScalingPolicy {
  name: string;
  metric: string;
  steps: StepAdjustment[];
  cooldown: number;
}

export const stepScalingPolicies: StepScalingPolicy[] = [
  {
    name: 'aggressive-scale-out',
    metric: 'CPUUtilization',
    cooldown: 300,
    steps: [
      {
        metricIntervalUpperBound: 50,
        scalingAdjustment: 0, // No change below 50%
      },
      {
        metricIntervalLowerBound: 50,
        metricIntervalUpperBound: 70,
        scalingAdjustment: 1, // Add 1 instance at 50-70%
      },
      {
        metricIntervalLowerBound: 70,
        metricIntervalUpperBound: 85,
        scalingAdjustment: 2, // Add 2 instances at 70-85%
      },
      {
        metricIntervalLowerBound: 85,
        metricIntervalUpperBound: 100,
        scalingAdjustment: 4, // Add 4 instances at 85-100%
      },
    ],
  },
];
```

---

## Load Balancing

### Application Load Balancer Configuration

```hcl
# infrastructure/terraform/alb.tf

resource "aws_lb" "main" {
  name               = "travel-agency-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.public_subnet_ids

  enable_deletion_protection       = false
  enable_http2                     = true
  enable_cross_zone_load_balancing = true
  idle_timeout                     = 60

  # ALB access logs
  access_logs {
    bucket  = aws_s3_bucket.alb_logs.id
    prefix  = "alb-logs"
    enabled = true
  }

  # WAF integration
  web_acl_id = var.waf_acl_id

  tags = var.common_tags
}

# HTTP to HTTPS redirect
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

# HTTPS listener
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = var.acm_certificate_arn

  default_action {
    type = "fixed-response"

    fixed_response {
      content_type = "text/plain"
      message_body = "Service not found"
      status_code  = "404"
    }
  }
}

# API target group
resource "aws_lb_target_group" "api" {
  name        = "travel-agency-api-tg"
  port        = 3000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    path                = "/health"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    matcher             = "200"
  }

  stickiness {
    type            = "lb_cookie"
    cookie_duration = 86400
    enabled         = true
  }

  tags = var.common_tags
}

# Listener rule for API
resource "aws_lb_listener_rule" "api" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }

  condition {
    path_pattern {
      values = ["/api/*"]
    }
  }
}
```

### Weighted Routing (Blue-Green)

```hcl
# infrastructure/terraform/blue-green.tf

# Blue target group (current version)
resource "aws_lb_target_group" "blue" {
  name        = "travel-agency-api-blue"
  port        = 3000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    path                = "/health"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
  }
}

# Green target group (new version)
resource "aws_lb_target_group" "green" {
  name        = "travel-agency-api-green"
  port        = 3000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    path                = "/health"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
  }
}

# Listener rule for weighted routing
resource "aws_lb_listener_rule" "weighted" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 50

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.blue.arn

    forward {
      target_group {
        arn = aws_lb_target_group.blue.arn
        weight = var.blue_weight  # e.g., 90
      }

      target_group {
        arn = aws_lb_target_group.green.arn
        weight = var.green_weight  # e.g., 10
      }
    }
  }

  condition {
    path_pattern {
      values = ["/api/*"]
    }
  }
}
```

### Circuit Breaker Pattern

```typescript
// lib/load-balancing/circuit-breaker.ts

export enum CircuitState {
  CLOSED = 'closed',
  OPEN = 'open',
  HALF_OPEN = 'half_open',
}

export interface CircuitBreakerConfig {
  failureThreshold: number;
  recoveryTimeout: number;
  halfOpenMaxCalls: number;
}

export class CircuitBreaker {
  private state: CircuitState = CircuitState.CLOSED;
  private failureCount = 0;
  private lastFailureTime = 0;
  private halfOpenCallCount = 0;

  constructor(private config: CircuitBreakerConfig) {}

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === CircuitState.OPEN) {
      if (this.shouldAttemptReset()) {
        this.state = CircuitState.HALF_OPEN;
        this.halfOpenCallCount = 0;
      } else {
        throw new Error('Circuit breaker is OPEN');
      }
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private onSuccess(): void {
    if (this.state === CircuitState.HALF_OPEN) {
      this.halfOpenCallCount++;
      if (this.halfOpenCallCount >= this.config.halfOpenMaxCalls) {
        this.state = CircuitState.CLOSED;
        this.failureCount = 0;
      }
    } else {
      this.failureCount = 0;
    }
  }

  private onFailure(): void {
    this.failureCount++;
    this.lastFailureTime = Date.now();

    if (this.failureCount >= this.config.failureThreshold) {
      this.state = CircuitState.OPEN;
    }
  }

  private shouldAttemptReset(): boolean {
    return Date.now() - this.lastFailureTime >= this.config.recoveryTimeout;
  }

  getState(): CircuitState {
    return this.state;
  }

  reset(): void {
    this.state = CircuitState.CLOSED;
    this.failureCount = 0;
    this.lastFailureTime = 0;
    this.halfOpenCallCount = 0;
  }
}

// Usage example
export const apiCircuitBreaker = new CircuitBreaker({
  failureThreshold: 5,
  recoveryTimeout: 60000, // 1 minute
  halfOpenMaxCalls: 3,
});
```

---

## Caching Architecture

### Multi-Layer Caching Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                     CACHING HIERARCHY                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  L1: Browser Cache                                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Static assets (1 hour)                                  │   │
│  │ Cache-Control: public, max-age=3600                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           │                                     │
│  L2: CDN (CloudFront)                                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Static assets, images (24 hours)                        │   │
│  │ API responses (5 minutes)                               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           │                                     │
│  L3: Application Cache (In-Memory)                             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Session data, user preferences (memory)                 │   │
│  │ Config, feature flags (5 minutes)                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           │                                     │
│  L4: Redis Cache                                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Session store (1 day)                                   │   │
│  │ Query results (5 minutes)                               │   │
│  │ Computed data (1 hour)                                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           │                                     │
│  L5: Database Query Cache                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Prepared statements (implicit)                          │   │
│  │ Materialized views (manual)                             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Redis Configuration

```typescript
// lib/cache/redis.ts

import { Redis } from 'ioredis';

export interface CacheConfig {
  host: string;
  port: number;
  password?: string;
  db: number;
  keyPrefix: string;
  defaultTTL: number;
}

export class CacheService {
  private client: Redis;
  private keyPrefix: string;

  constructor(config: CacheConfig) {
    this.client = new Redis({
      host: config.host,
      port: config.port,
      password: config.password,
      db: config.db,
      retryStrategy: (times) => Math.min(times * 50, 2000),
      maxRetriesPerRequest: 3,
      enableReadyCheck: true,
      enableOfflineQueue: true,
    });

    this.keyPrefix = config.keyPrefix;

    // Error handling
    this.client.on('error', (error) => {
      console.error('Redis error:', error);
    });
  }

  private makeKey(key: string): string {
    return `${this.keyPrefix}:${key}`;
  }

  async get<T>(key: string): Promise<T | null> {
    const fullKey = this.makeKey(key);
    const value = await this.client.get(fullKey);

    if (!value) return null;

    try {
      return JSON.parse(value) as T;
    } catch {
      return value as T;
    }
  }

  async set<T>(key: string, value: T, ttl?: number): Promise<void> {
    const fullKey = this.makeKey(key);
    const serialized = JSON.stringify(value);

    if (ttl) {
      await this.client.setex(fullKey, ttl, serialized);
    } else {
      await this.client.set(fullKey, serialized);
    }
  }

  async delete(key: string): Promise<void> {
    const fullKey = this.makeKey(key);
    await this.client.del(fullKey);
  }

  async invalidatePattern(pattern: string): Promise<number> {
    const fullPattern = this.makeKey(pattern);
    const keys = await this.client.keys(fullPattern);

    if (keys.length === 0) return 0;

    return await this.client.del(...keys);
  }

  async getMany<T>(keys: string[]): Promise<(T | null)[]> {
    const pipeline = this.client.pipeline();

    keys.forEach((key) => {
      pipeline.get(this.makeKey(key));
    });

    const results = await pipeline.exec();

    return results.map(([err, value]) => {
      if (err || !value) return null;
      try {
        return JSON.parse(value as string) as T;
      } catch {
        return value as T;
      }
    });
  }

  async setMany<T>(entries: Array<{ key: string; value: T; ttl?: number }>): Promise<void> {
    const pipeline = this.client.pipeline();

    entries.forEach(({ key, value, ttl }) => {
      const serialized = JSON.stringify(value);
      const fullKey = this.makeKey(key);

      if (ttl) {
        pipeline.setex(fullKey, ttl, serialized);
      } else {
        pipeline.set(fullKey, serialized);
      }
    });

    await pipeline.exec();
  }

  // Atomic operations
  async increment(key: string, amount = 1): Promise<number> {
    const fullKey = this.makeKey(key);
    return await this.client.incrby(fullKey, amount);
  }

  async getOrSet<T>(
    key: string,
    factory: () => Promise<T>,
    ttl?: number
  ): Promise<T> {
    const cached = await this.get<T>(key);

    if (cached !== null) {
      return cached;
    }

    const value = await factory();
    await this.set(key, value, ttl);

    return value;
  }

  // Cache stampede protection
  async getOrSetWithLock<T>(
    key: string,
    factory: () => Promise<T>,
    ttl: number,
    lockTimeout = 10
  ): Promise<T> {
    const lockKey = `${this.makeKey(key)}:lock`;

    // Try to acquire lock
    const lockAcquired = await this.client.set(
      lockKey,
      '1',
      'PX',
      lockTimeout * 1000,
      'NX'
    );

    if (lockAcquired === 'OK') {
      try {
        // We have the lock, fetch and cache
        const value = await factory();
        await this.set(key, value, ttl);
        return value;
      } finally {
        await this.client.del(lockKey);
      }
    }

    // Lock not acquired, wait and retry get
    await new Promise((resolve) => setTimeout(resolve, 100));
    const cached = await this.get<T>(key);

    if (cached !== null) {
      return cached;
    }

    // Still no cache, fetch directly
    return await factory();
  }

  async disconnect(): Promise<void> {
    await this.client.quit();
  }
}

// Cache configuration by type
export const cacheConfigs = {
  session: {
    defaultTTL: 86400, // 24 hours
    keyPrefix: 'session',
  },
  api: {
    defaultTTL: 300, // 5 minutes
    keyPrefix: 'api',
  },
  query: {
    defaultTTL: 600, // 10 minutes
    keyPrefix: 'query',
  },
  static: {
    defaultTTL: 3600, // 1 hour
    keyPrefix: 'static',
  },
};
```

### Cache Invalidation Strategy

```typescript
// lib/cache/invalidation.ts

export interface CacheInvalidationRule {
  pattern: string;
  trigger: 'create' | 'update' | 'delete';
  tables: string[];
}

export class CacheInvalidationService {
  private rules: CacheInvalidationRule[] = [
    {
      pattern: 'trip:*',
      trigger: 'update',
      tables: ['trips', 'bookings'],
    },
    {
      pattern: 'agency:*',
      trigger: 'update',
      tables: ['agencies', 'users'],
    },
    {
      pattern: 'search:*',
      trigger: 'create',
      tables: ['trips', 'bookings', 'customers'],
    },
  ];

  async invalidateOnMutation(
    table: string,
    operation: 'create' | 'update' | 'delete',
    recordId?: string
  ): Promise<void> {
    for (const rule of this.rules) {
      if (rule.tables.includes(table) && rule.trigger === operation) {
        await this.invalidatePattern(rule.pattern);
      }
    }

    // Invalidate specific record cache
    if (recordId) {
      await this.invalidatePattern(`${table}:${recordId}*`);
    }
  }

  private async invalidatePattern(pattern: string): Promise<void> {
    const cache = getCacheService();
    await cache.invalidatePattern(pattern);
  }
}
```

### CDN Configuration

```typescript
// next.config.js - CDN cache headers

module.exports = {
  async headers() {
    return [
      {
        source: '/static/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
      {
        source: '/images/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=86400, s-maxage=604800', // 1 day browser, 7 days CDN
          },
        ],
      },
      {
        source: '/api/public/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=300, s-maxage=600', // 5 min browser, 10 min CDN
          },
        ],
      },
    ];
  },
};
```

---

## Database Scaling

### Read Replicas

```hcl
# infrastructure/terraform/rds-read-replicas.tf

# Primary database
resource "aws_db_instance" "primary" {
  identifier = "travel-agency-primary"

  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.r6g.xlarge"

  allocated_storage     = 500
  max_allocated_storage = 2000
  storage_type          = "gp3"
  storage_encrypted     = true

  multi_az = true

  # Backup configuration
  backup_retention_period = 30
  backup_window          = "03:00-04:00"

  # Performance
  performance_insights_enabled = true

  tags = var.common_tags
}

# Read replica 1
resource "aws_db_instance" "replica_1" {
  identifier = "travel-agency-replica-1"

  replicate_source_db = aws_db_instance.primary.identifier

  instance_class = "db.r6g.large"  # Can be smaller than primary

  # Replicas are in single AZ by default
  multi_az = false

  # Different backup window to avoid primary impact
  backup_retention_period = 7
  backup_window          = "05:00-06:00"

  # Performance monitoring
  monitoring_interval = 60

  # No deletion protection for replicas
  deletion_protection  = false
  skip_final_snapshot  = true

  tags = var.common_tags
}

# Read replica 2 (different AZ)
resource "aws_db_instance" "replica_2" {
  identifier = "travel-agency-replica-2"

  replicate_source_db = aws_db_instance.primary.identifier
  availability_zone   = "${var.aws_region}b"

  instance_class = "db.r6g.large"

  backup_retention_period = 7
  backup_window          = "07:00-08:00"

  monitoring_interval = 60

  deletion_protection = false
  skip_final_snapshot  = true

  tags = var.common_tags
}
```

### Read-Write Routing

```typescript
// lib/database/read-write-routing.ts

import { PrismaClient } from '@prisma/client';

export class DatabaseRouter {
  private primary: PrismaClient;
  private replicas: PrismaClient[];
  private replicaIndex = 0;

  constructor(primaryUrl: string, replicaUrls: string[]) {
    this.primary = new PrismaClient({
      datasources: {
        db: { url: primaryUrl },
      },
    });

    this.replicas = replicaUrls.map(
      (url) =>
        new PrismaClient({
          datasources: { db: { url } },
        })
    );
  }

  getReadClient(): PrismaClient {
    // Round-robin through replicas
    const replica = this.replicas[this.replicaIndex];
    this.replicaIndex = (this.replicaIndex + 1) % this.replicas.length;
    return replica;
  }

  getWriteClient(): PrismaClient {
    return this.primary;
  }

  // For transactions that need consistency
  getPrimaryClient(): PrismaClient {
    return this.primary;
  }

  async disconnect(): Promise<void> {
    await this.primary.$disconnect();
    await Promise.all(this.replicas.map((r) => r.$disconnect()));
  }
}

// Usage in repository
export class TripRepository {
  constructor(private dbRouter: DatabaseRouter) {}

  async findById(id: string) {
    // Read from replica
    return this.dbRouter.getReadClient().trip.findUnique({ where: { id } });
  }

  async create(data: CreateTripDTO) {
    // Write to primary
    return this.dbRouter.getWriteClient().trip.create({ data });
  }

  async findByIdForUpdate(id: string) {
    // Read from primary for locking
    return this.dbRouter.getPrimaryClient().trip.findUnique({
      where: { id },
    });
  }
}
```

### Connection Pooling

```typescript
// lib/database/connection-pool.ts

import { Pool, PoolConfig } from 'pg';

export interface ConnectionPoolConfig {
  host: string;
  port: number;
  database: string;
  user: string;
  password: string;
  min: number;
  max: number;
  idleTimeoutMillis: number;
  connectionTimeoutMillis: number;
}

export class ConnectionPoolManager {
  private pools: Map<string, Pool> = new Map();

  getPool(config: ConnectionPoolConfig): Pool {
    const key = this.getPoolKey(config);

    if (!this.pools.has(key)) {
      const poolConfig: PoolConfig = {
        host: config.host,
        port: config.port,
        database: config.database,
        user: config.user,
        password: config.password,
        min: config.min,
        max: config.max,
        idleTimeoutMillis: config.idleTimeoutMillis,
        connectionTimeoutMillis: config.connectionTimeoutMillis,

        // Statement caching
        statement_timeout: 30000,

        // Application name for monitoring
        application_name: 'travel-agency-api',
      };

      const pool = new Pool(poolConfig);

      // Pool event monitoring
      pool.on('error', (err) => {
        console.error('Unexpected pool error', err);
      });

      pool.on('connect', (client) => {
        console.debug('New client connected to pool');
      });

      pool.on('remove', (client) => {
        console.debug('Client removed from pool');
      });

      this.pools.set(key, pool);
    }

    return this.pools.get(key)!;
  }

  async closeAll(): Promise<void> {
    const closePromises = Array.from(this.pools.values()).map((pool) => pool.end());
    await Promise.all(closePromises);
    this.pools.clear();
  }

  private getPoolKey(config: ConnectionPoolConfig): string {
    return `${config.host}:${config.port}:${config.database}`;
  }
}

// Connection pool configuration
export const poolConfig: ConnectionPoolConfig = {
  host: process.env.DB_HOST!,
  port: parseInt(process.env.DB_PORT || '5432'),
  database: process.env.DB_NAME!,
  user: process.env.DB_USER!,
  password: process.env.DB_PASSWORD!,
  min: 2,  // Minimum connections
  max: 20, // Maximum connections
  idleTimeoutMillis: 30000,     // Close idle connections after 30s
  connectionTimeoutMillis: 5000, // Timeout when acquiring connection
};
```

---

## Queue-Based Processing

### Job Queue Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     QUEUE ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Producers                      Queue                          Consumers
│  ┌───────────┐                 ┌─────────┐      ┌───────────┐  │
│  │  API      │ ────produce────► │   SQS   │─────►│ Worker 1  │  │
│  │  Server   │                 │         │      └───────────┘  │
│  └───────────┘                 └─────────┘              │       │
│       │                           │               ┌───────▼──────┐│
│       │                      ┌─────┴─────┐        │   Worker 2  ││
│       ▼                      │  DLQ      │        └───────┬──────┘│
│  ┌───────────┐               │ (failed)  │                │       │
│  │ Scheduled │               └───────────┘           ┌───────▼──────┐
│  │ Jobs      │                                       │   Worker N  │
│  └───────────┘                                       └─────────────┘
│                                                                 │
│  Queue Types:                                                  │
│  • High Priority: Urgent notifications, payment confirmations   │
│  • Standard: Booking processing, email sending                  │
│  • Low Priority: Analytics, reporting, batch operations        │
│  • Dead Letter: Failed jobs for investigation                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Job Queue Implementation

```typescript
// lib/queues/job-queue.ts

import { Queue, Worker, Job } from 'bullmq';
import { Redis } from 'ioredis';

export interface JobDefinition {
  name: string;
  handler: (job: Job) => Promise<void>;
  options?: {
    attempts?: number;
    backoff?: {
      type: 'exponential' | 'fixed';
      delay: number;
    };
    limiter?: {
      max: number;
      duration: number;
    };
    priority?: number;
  };
}

export class JobQueueManager {
  private queues: Map<string, Queue> = new Map();
  private workers: Map<string, Worker> = new Map();
  private connection: Redis;

  constructor(redisConfig: { host: string; port: number }) {
    this.connection = new Redis({
      host: redisConfig.host,
      port: redisConfig.port,
      maxRetriesPerRequest: null,
    });
  }

  getQueue(name: string, priority = false): Queue {
    const queueName = priority ? `${name}:priority` : name;

    if (!this.queues.has(queueName)) {
      const queue = new Queue(queueName, {
        connection: this.connection,
        defaultJobOptions: {
          attempts: 3,
          backoff: {
            type: 'exponential',
            delay: 2000,
          },
          removeOnComplete: {
            age: 3600, // Keep completed jobs for 1 hour
            count: 1000,
          },
          removeOnFail: {
            age: 7 * 24 * 3600, // Keep failed jobs for 7 days
          },
        },
      });

      this.queues.set(queueName, queue);
    }

    return this.queues.get(queueName)!;
  }

  async registerWorker(jobDef: JobDefinition): Promise<void> {
    const queue = this.getQueue(jobDef.name);

    const worker = new Worker(
      jobDef.name,
      async (job: Job) => {
        await jobDef.handler(job);
      },
      {
        connection: this.connection,
        concurrency: jobDef.options?.limiter?.max || 5,
        limiter: jobDef.options?.limiter,
      }
    );

    worker.on('completed', (job) => {
      console.debug(`Job ${job.id} completed`);
    });

    worker.on('failed', (job, err) => {
      console.error(`Job ${job?.id} failed:`, err);
    });

    this.workers.set(jobDef.name, worker);
  }

  async addJob<T>(
    queueName: string,
    jobName: string,
    data: T,
    options?: {
      delay?: number;
      priority?: number;
      jobId?: string;
    }
  ): Promise<Job<T>> {
    const queue = this.getQueue(queueName, options?.priority !== undefined);

    return await queue.add(jobName, data, {
      delay: options?.delay,
      priority: options?.priority,
      jobId: options?.jobId,
    });
  }

  async getJobCounts(queueName: string): Promise<{
    waiting: number;
    active: number;
    completed: number;
    failed: number;
    delayed: number;
  }> {
    const queue = this.getQueue(queueName);
    return await queue.getJobCounts();
  }

  async close(): Promise<void> {
    const closePromises = [
      ...Array.from(this.queues.values()).map((q) => q.close()),
      ...Array.from(this.workers.values()).map((w) => w.close()),
    ];

    await Promise.all(closePromises);

    await this.connection.quit();
  }
}

// Job definitions
export const jobDefinitions: JobDefinition[] = [
  {
    name: 'booking-creation',
    handler: async (job) => {
      const { tripId, bookingData } = job.data;
      // Process booking creation
    },
    options: {
      attempts: 5,
      backoff: { type: 'exponential', delay: 5000 },
      priority: 10, // High priority
    },
  },
  {
    name: 'email-sending',
    handler: async (job) => {
      const { to, template, data } = job.data;
      // Send email
    },
    options: {
      attempts: 3,
      backoff: { type: 'fixed', delay: 10000 },
      limiter: { max: 100, duration: 60000 }, // 100 emails per minute
    },
  },
  {
    name: 'analytics-aggregation',
    handler: async (job) => {
      const { startDate, endDate } = job.data;
      // Aggregate analytics
    },
    options: {
      attempts: 2,
      priority: 1, // Low priority
    },
  },
];
```

### Auto-Scaling Workers

```typescript
// lib/queues/auto-scaling-worker.ts

export interface WorkerScalingConfig {
  minWorkers: number;
  maxWorkers: number;
  scaleUpThreshold: number;  // Queue depth to trigger scale up
  scaleDownThreshold: number; // Queue depth to trigger scale down
  cooldownPeriod: number;     // Milliseconds between scaling actions
}

export class AutoScalingWorkerPool {
  private workers: Worker[] = [];
  private lastScaleAction = 0;

  constructor(
    private queue: Queue,
    private jobDefinition: JobDefinition,
    private config: WorkerScalingConfig
  ) {}

  async start(): Promise<void> {
    // Start with minimum workers
    for (let i = 0; i < this.config.minWorkers; i++) {
      await this.addWorker();
    }

    // Start monitoring loop
    this.monitorQueue();
  }

  private async addWorker(): Promise<void> {
    const worker = new Worker(
      this.jobDefinition.name,
      async (job: Job) => {
        await this.jobDefinition.handler(job);
      },
      {
        connection: this.queue.client as any,
        concurrency: 10,
      }
    );

    this.workers.push(worker);
  }

  private async removeWorker(): Promise<void> {
    const worker = this.workers.pop();
    if (worker) {
      await worker.close();
    }
  }

  private monitorQueue(): void {
    setInterval(async () => {
      const now = Date.now();

      // Check cooldown
      if (now - this.lastScaleAction < this.config.cooldownPeriod) {
        return;
      }

      const counts = await this.queue.getJobCounts();
      const queueDepth = counts.waiting + counts.delayed;

      // Scale up
      if (
        queueDepth > this.config.scaleUpThreshold &&
        this.workers.length < this.config.maxWorkers
      ) {
        const workersToAdd = Math.min(
          Math.ceil(queueDepth / this.config.scaleUpThreshold),
          this.config.maxWorkers - this.workers.length
        );

        for (let i = 0; i < workersToAdd; i++) {
          await this.addWorker();
        }

        this.lastScaleAction = now;
        console.info(`Scaled up to ${this.workers.length} workers`);
      }

      // Scale down
      if (
        queueDepth < this.config.scaleDownThreshold &&
        this.workers.length > this.config.minWorkers
      ) {
        await this.removeWorker();
        this.lastScaleAction = now;
        console.info(`Scaled down to ${this.workers.length} workers`);
      }
    }, 30000); // Check every 30 seconds
  }

  async stop(): Promise<void> {
    await Promise.all(this.workers.map((w) => w.close()));
    this.workers = [];
  }
}
```

---

## Rate Limiting

### Token Bucket Algorithm

```typescript
// lib/rate-limiting/token-bucket.ts

export interface TokenBucketConfig {
  capacity: number;      // Maximum tokens
  refillRate: number;    // Tokens per second
  interval: number;      // Calculation interval in ms
}

export class TokenBucket {
  private tokens: number;
  private lastRefill: number;

  constructor(private config: TokenBucketConfig) {
    this.tokens = config.capacity;
    this.lastRefill = Date.now();
  }

  async tryConsume(tokens = 1): Promise<boolean> {
    await this.refill();

    if (this.tokens >= tokens) {
      this.tokens -= tokens;
      return true;
    }

    return false;
  }

  private async refill(): Promise<void> {
    const now = Date.now();
    const elapsed = now - this.lastRefill;

    if (elapsed >= this.config.interval) {
      const tokensToAdd = Math.floor(
        (elapsed / this.config.interval) * this.config.refillRate
      );

      this.tokens = Math.min(
        this.config.capacity,
        this.tokens + tokensToAdd
      );

      this.lastRefill = now;
    }
  }

  getAvailableTokens(): number {
    return this.tokens;
  }
}

// Rate limiter service
export class RateLimiterService {
  private buckets: Map<string, TokenBucket> = new Map();

  constructor(
    private defaultConfig: TokenBucketConfig,
    private limits: Map<string, TokenBucketConfig> = new Map()
  ) {}

  async checkLimit(
    identifier: string,
    limitType?: string
  ): Promise<{ allowed: boolean; remaining: number }> {
    const config = limitType
      ? this.limits.get(limitType) || this.defaultConfig
      : this.defaultConfig;

    const key = limitType ? `${identifier}:${limitType}` : identifier;

    let bucket = this.buckets.get(key);

    if (!bucket) {
      bucket = new TokenBucket(config);
      this.buckets.set(key, bucket);
    }

    const allowed = await bucket.tryConsume(1);

    return {
      allowed,
      remaining: bucket.getAvailableTokens(),
    };
  }

  // Clean up old buckets
  cleanup(): void {
    // Remove buckets that haven't been used recently
    // Implementation depends on your requirements
  }
}

// Usage
export const rateLimiter = new RateLimiterService(
  {
    capacity: 100,
    refillRate: 10,  // 10 tokens per second
    interval: 1000,
  },
  new Map([
    [
      'api-strict',
      {
        capacity: 20,
        refillRate: 2,
        interval: 1000,
      },
    ],
    [
      'api-generous',
      {
        capacity: 1000,
        refillRate: 100,
        interval: 1000,
      },
    ],
  ])
);
```

### Distributed Rate Limiting

```typescript
// lib/rate-limiting/distributed.ts

export class DistributedRateLimiter {
  constructor(private redis: Redis) {}

  async checkLimit(
    identifier: string,
    limit: number,
    window: number // milliseconds
  ): Promise<{ allowed: boolean; remaining: number; resetAt: Date }> {
    const key = `ratelimit:${identifier}`;
    const now = Date.now();
    const windowStart = now - window;
    const pipeline = this.redis.pipeline();

    // Remove old entries
    pipeline.zremrangebyscore(key, 0, windowStart);

    // Count current requests
    pipeline.zcard(key);

    // Add current request
    pipeline.zadd(key, now, `${now}-${Math.random()}`);

    // Set expiration
    pipeline.pexpire(key, window);

    const results = await pipeline.exec();

    // zcard result is at index 1
    const currentCount = (results?.[1]?.[1] as number) || 0;
    const allowed = currentCount < limit;
    const remaining = Math.max(0, limit - currentCount - 1);
    const resetAt = new Date(now + window);

    return { allowed, remaining, resetAt };
  }

  async checkSlidingWindow(
    identifier: string,
    limit: number,
    window: number
  ): Promise<{ allowed: boolean; remaining: number }> {
    const key = `ratelimit:sliding:${identifier}`;
    const now = Date.now();
    const windowStart = now - window;

    const pipeline = this.redis.pipeline();

    // Remove old entries
    pipeline.zremrangebyscore(key, 0, windowStart);

    // Count current requests
    pipeline.zcard(key);

    // Add current request if allowed
    const script = `
      local count = redis.call('zcard', KEYS[1])
      if count < tonumber(ARGV[1]) then
        redis.call('zadd', KEYS[1], ARGV[2], ARGV[3])
        redis.call('pexpire', KEYS[1], ARGV[4])
        return {1, count}
      else
        return {0, count}
      end
    `;

    const result = await this.redis.eval(
      script,
      1,
      key,
      limit,
      now,
      `${now}-${Math.random()}`,
      window
    );

    const [allowed, currentCount] = result as [number, number];

    return {
      allowed: allowed === 1,
      remaining: Math.max(0, limit - currentCount - 1),
    };
  }
}
```

### Rate Limit Middleware

```typescript
// middleware/rate-limit.ts

import { NextRequest, NextResponse } from 'next/server';
import { distributedRateLimiter } from '@/lib/rate-limiting/distributed';

export interface RateLimitConfig {
  endpoint: string;
  limit: number;
  window: number;
  skipSuccessfulRequests?: boolean;
}

export const rateLimitConfigs: RateLimitConfig[] = [
  { endpoint: '/api/auth/login', limit: 5, window: 60000 }, // 5 per minute
  { endpoint: '/api/auth/register', limit: 3, window: 3600000 }, // 3 per hour
  { endpoint: '/api/search', limit: 60, window: 60000 }, // 60 per minute
  { endpoint: '/api/booking', limit: 20, window: 60000 }, // 20 per minute
  { endpoint: '/api/ai', limit: 100, window: 3600000 }, // 100 per hour
];

export async function rateLimitMiddleware(
  request: NextRequest,
  context: { userId?: string; agencyId?: string }
): Promise<{ allowed: boolean; limit: number; remaining: number; resetAt: Date }> {
  const identifier =
    context.userId ||
    context.agencyId ||
    request.headers.get('x-forwarded-for') ||
    'anonymous';

  const path = new URL(request.url).pathname;

  // Find matching rate limit config
  const config = rateLimitConfigs.find((c) => path.startsWith(c.endpoint));

  if (!config) {
    return {
      allowed: true,
      limit: 0,
      remaining: 0,
      resetAt: new Date(),
    };
  }

  const result = await distributedRateLimiter.checkLimit(
    `${identifier}:${path}`,
    config.limit,
    config.window
  );

  return result;
}

export function rateLimitResponse(result: ReturnType<typeof distributedRateLimiter.checkLimit> extends Promise<infer T> ? T : never) {
  return NextResponse.json(
    { error: 'Rate limit exceeded' },
    {
      status: 429,
      headers: {
        'X-RateLimit-Limit': String(result.limit),
        'X-RateLimit-Remaining': String(result.remaining),
        'X-RateLimit-Reset': result.resetAt.toISOString(),
        'Retry-After': String(Math.ceil((result.resetAt.getTime() - Date.now()) / 1000)),
      },
    }
  );
}
```

---

## Cost Optimization

### Right-Sizing Recommendations

```typescript
// lib/cost/right-sizing.ts

export interface ResourceMetrics {
  resourceId: string;
  type: 'ecs' | 'rds' | 'elasticache';
  currentSize: string;
  avgCpu: number;
  avgMemory: number;
  peakCpu: number;
  peakMemory: number;
  cost: number;
}

export interface RightSizingRecommendation {
  resourceId: string;
  action: 'up' | 'down' | 'none';
  currentSize: string;
  recommendedSize: string;
  reason: string;
  estimatedSavings: number;
}

export class RightSizingService {
  async analyzeResource(metrics: ResourceMetrics): Promise<RightSizingRecommendation> {
    const { resourceId, type, avgCpu, avgMemory, peakCpu, peakMemory, currentSize } = metrics;

    // Check if underutilized (scale down opportunity)
    if (avgCpu < 20 && avgMemory < 40 && peakCpu < 60 && peakMemory < 70) {
      const recommendedSize = this.getNextSizeDown(type, currentSize);
      const estimatedSavings = this.calculateSavings(type, currentSize, recommendedSize);

      return {
        resourceId,
        action: 'down',
        currentSize,
        recommendedSize,
        reason: `Resource underutilized: ${avgCpu.toFixed(1)}% CPU, ${avgMemory.toFixed(1)}% Memory average`,
        estimatedSavings,
      };
    }

    // Check if overutilized (scale up needed)
    if (peakCpu > 90 || peakMemory > 90) {
      const recommendedSize = this.getNextSizeUp(type, currentSize);
      const additionalCost = this.calculateCostIncrease(type, currentSize, recommendedSize);

      return {
        resourceId,
        action: 'up',
        currentSize,
        recommendedSize,
        reason: `Resource overutilized: ${peakCpu.toFixed(1)}% CPU, ${peakMemory.toFixed(1)}% Memory peak`,
        estimatedSavings: -additionalCost,
      };
    }

    return {
      resourceId,
      action: 'none',
      currentSize,
      recommendedSize: currentSize,
      reason: 'Resource utilization within acceptable range',
      estimatedSavings: 0,
    };
  }

  private getNextSizeUp(type: string, currentSize: string): string {
    const sizeMap: Record<string, string[]> = {
      rds: ['db.t3.micro', 'db.t3.small', 'db.t3.medium', 'db.t3.large', 'db.r6g.large', 'db.r6g.xlarge', 'db.r6g.2xlarge'],
      ecs: ['0.25 vCPU', '0.5 vCPU', '1 vCPU', '2 vCPU', '4 vCPU', '8 vCPU'],
      elasticache: ['cache.t3.micro', 'cache.t3.small', 'cache.t3.medium', 'cache.m6g.large', 'cache.m6g.xlarge'],
    };

    const sizes = sizeMap[type] || [];
    const currentIndex = sizes.indexOf(currentSize);

    return currentIndex < sizes.length - 1 ? sizes[currentIndex + 1] : currentSize;
  }

  private getNextSizeDown(type: string, currentSize: string): string {
    const sizeMap: Record<string, string[]> = {
      rds: ['db.t3.micro', 'db.t3.small', 'db.t3.medium', 'db.t3.large', 'db.r6g.large', 'db.r6g.xlarge', 'db.r6g.2xlarge'],
      ecs: ['0.25 vCPU', '0.5 vCPU', '1 vCPU', '2 vCPU', '4 vCPU', '8 vCPU'],
      elasticache: ['cache.t3.micro', 'cache.t3.small', 'cache.t3.medium', 'cache.m6g.large', 'cache.m6g.xlarge'],
    };

    const sizes = sizeMap[type] || [];
    const currentIndex = sizes.indexOf(currentSize);

    return currentIndex > 0 ? sizes[currentIndex - 1] : currentSize;
  }

  private calculateSavings(type: string, currentSize: string, recommendedSize: string): number {
    // Simplified cost calculation
    const pricing: Record<string, Record<string, number>> = {
      rds: {
        'db.r6g.xlarge': 200,
        'db.r6g.large': 100,
        'db.t3.medium': 30,
      },
      ecs: {
        '4 vCPU': 80,
        '2 vCPU': 40,
        '1 vCPU': 20,
      },
    };

    const currentCost = pricing[type]?.[currentSize] || 0;
    const recommendedCost = pricing[type]?.[recommendedSize] || 0;

    return (currentCost - recommendedCost) * 730; // Monthly savings
  }

  private calculateCostIncrease(type: string, currentSize: string, recommendedSize: string): number {
    return -this.calculateSavings(type, recommendedSize, currentSize);
  }
}
```

### Spot Instance Strategy

```typescript
// lib/scaling/spot-strategy.ts

export interface SpotStrategy {
  useSpot: boolean;
  spotPercentage: number; // 0-100
  fallbackToOnDemand: boolean;
}

export const spotStrategies: Record<string, SpotStrategy> = {
  // Non-critical workloads: 100% spot
  workers: {
    useSpot: true,
    spotPercentage: 100,
    fallbackToOnDemand: true,
  },

  // API servers: 75% spot, 25% on-demand for baseline
  api: {
    useSpot: true,
    spotPercentage: 75,
    fallbackToOnDemand: true,
  },

  // Critical services: 0% spot
  database: {
    useSpot: false,
    spotPercentage: 0,
    fallbackToOnDemand: false,
  },

  // Analytics: 100% spot, interruptible jobs
  analytics: {
    useSpot: true,
    spotPercentage: 100,
    fallbackToOnDemand: false,
  },
};

// ECS Capacity Provider Strategy
export function getCapacityProviderStrategy(workloadType: string) {
  const strategy = spotStrategies[workloadType] || spotStrategies.api;

  if (!strategy.useSpot) {
    return [
      {
        capacityProvider: 'FARGATE',
        weight: 1,
        base: 1,
      },
    ];
  }

  const spotWeight = strategy.spotPercentage / 100;
  const onDemandWeight = 1 - spotWeight;

  return [
    {
      capacityProvider: 'FARGATE_SPOT',
      weight: Math.round(spotWeight * 10),
      base: 0,
    },
    {
      capacityProvider: 'FARGATE',
      weight: Math.round(onDemandWeight * 10),
      base: 1,
    },
  ];
}
```

### Scheduled Resource Shutdown

```typescript
// lib/cost/scheduled-shutdown.ts

export interface ScheduleConfig {
  name: string;
  resources: string[];
  timezone: string;
  shutdownTime: string; // HH:MM format
  startupTime: string;  // HH:MM format
  daysOfWeek: number[]; // 0-6 (Sunday-Saturday)
}

export const nonProdSchedules: ScheduleConfig[] = [
  {
    name: 'dev-environment-shutdown',
    resources: ['ecs-cluster-dev', 'rds-dev', 'elasticache-dev'],
    timezone: 'America/Los_Angeles',
    shutdownTime: '22:00',
    startupTime: '06:00',
    daysOfWeek: [1, 2, 3, 4, 5], // Weekdays only
  },
  {
    name: 'staging-environment-shutdown',
    resources: ['ecs-cluster-staging', 'rds-staging'],
    timezone: 'America/Los_Angeles',
    shutdownTime: '20:00',
    startupTime: '08:00',
    daysOfWeek: [1, 2, 3, 4, 5],
  },
];

export class ScheduledShutdownService {
  async shouldShutdown(config: ScheduleConfig): Promise<boolean> {
    const now = new Date();
    const timeZone = config.timezone;

    // Get current time in configured timezone
    const currentTime = new Date(
      now.toLocaleString('en-US', { timeZone })
    );

    const hours = currentTime.getHours();
    const minutes = currentTime.getMinutes();
    const currentTimeMinutes = hours * 60 + minutes;
    const dayOfWeek = currentTime.getDay();

    // Check if it's a scheduled day
    if (!config.daysOfWeek.includes(dayOfWeek)) {
      return false;
    }

    const [shutdownHour, shutdownMinute] = config.shutdownTime.split(':').map(Number);
    const [startupHour, startupMinute] = config.startupTime.split(':').map(Number);

    const shutdownMinutes = shutdownHour * 60 + shutdownMinute;
    const startupMinutes = startupHour * 60 + startupMinute;

    // Handle overnight case
    if (startupMinutes > shutdownMinutes) {
      return currentTimeMinutes >= shutdownMinutes || currentTimeMinutes < startupMinutes;
    }

    return currentTimeMinutes >= shutdownMinutes && currentTimeMinutes < startupMinutes;
  }

  async executeShutdown(config: ScheduleConfig): Promise<void> {
    for (const resource of config.resources) {
      await this.shutdownResource(resource);
    }
  }

  async executeStartup(config: ScheduleConfig): Promise<void> {
    for (const resource of config.resources) {
      await this.startupResource(resource);
    }
  }

  private async shutdownResource(resourceId: string): Promise<void> {
    // Implement resource-specific shutdown logic
    // For ECS: update service desired count to 0
    // For RDS: stop instance (if not Multi-AZ)
    console.log(`Shutting down resource: ${resourceId}`);
  }

  private async startupResource(resourceId: string): Promise<void> {
    // Implement resource-specific startup logic
    console.log(`Starting up resource: ${resourceId}`);
  }
}
```

---

## Summary

The Scaling & Performance system provides comprehensive strategies for:

- **Horizontal Scaling**: Container orchestration, multi-AZ deployment, auto-scaling policies
- **Vertical Scaling**: Database instance sizing, resource upgrades
- **Auto-Scaling**: Predictive scaling, scheduled scaling, step scaling
- **Load Balancing**: ALB/NLB configuration, weighted routing, circuit breakers
- **Caching**: Multi-layer architecture, Redis, CDN, invalidation strategies
- **Database Scaling**: Read replicas, connection pooling, read-write routing
- **Queue Processing**: Job queues, auto-scaling workers, priority queues
- **Rate Limiting**: Token bucket, distributed rate limiting, middleware
- **Cost Optimization**: Right-sizing, spot instances, scheduled shutdown

### Scaling Checklist

| Area | Recommendation |
|------|----------------|
| **Application** | Enable FARGATE with FARGATE_SPOT for non-critical workloads |
| **Database** | Use read replicas for read-heavy workloads |
| **Cache** | Implement multi-layer caching (browser, CDN, Redis) |
| **Workers** | Auto-scale based on queue depth |
| **Cost** | Use spot instances and scheduled shutdown for non-prod |

### Key Metrics to Monitor

| Metric | Target | Action |
|--------|--------|--------|
| **CPU Utilization** | 60-70% | Scale out if > 80% for 3 min |
| **Memory Utilization** | < 80% | Scale out if > 90% |
| **Response Time p95** | < 500ms | Scale out if > 1s |
| **Queue Depth** | < 1000 | Scale workers if > 1000 |
| **Cache Hit Rate** | > 80% | Investigate if < 60% |

---

**DevOps & Infrastructure Series Complete!**

All 4 documents in the DevOps series are now complete:
1. ✅ DEVOPS_01: Infrastructure Deep Dive
2. ✅ DEVOPS_02: CI/CD Deep Dive
3. ✅ DEVOPS_03: Monitoring & Observability Deep Dive
4. ✅ DEVOPS_04: Scaling & Performance Deep Dive

---

**Last Updated:** 2026-04-25
