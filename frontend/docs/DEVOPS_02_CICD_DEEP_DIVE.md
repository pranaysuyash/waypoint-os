# DEVOPS_02: CI/CD Deep Dive

> Build pipeline, deployments, releases, and delivery strategies

---

## Table of Contents

1. [Overview](#overview)
2. [Build Pipeline](#build-pipeline)
3. [Docker Containerization](#docker-containerization)
4. [Multi-Environment Deployments](#multi-environment-deployments)
5. [Database Migrations](#database-migrations)
6. [Feature Flags](#feature-flags)
7. [Rollback Strategies](#rollback-strategies)
8. [Release Strategies](#release-strategies)

---

## Overview

### CI/CD Philosophy

```
┌─────────────────────────────────────────────────────────────────┐
│                      CI/CD PRINCIPLES                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Continuous Integration (CI)                                     │
│  • Every commit is built and tested                              │
│  • Fast feedback loops (< 10 min)                               │
│  • Fail fast, fix fast                                           │
│                                                                  │
│  Continuous Delivery (CD)                                        │
│  • Every commit is deployable                                   │
│  • Deploy to production with one command                        │
│  • Automated deployments to lower environments                   │
│                                                                  │
│  Continuous Deployment                                          │
│  • Every commit that passes tests is auto-deployed              │
│  • Progressive delivery (canary, blue-green)                    │
│  • Instant rollback capability                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Pipeline Stages

```
┌─────────────────────────────────────────────────────────────────┐
│                    PIPELINE STAGES                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. BUILD                                                        │
│     ├── Install dependencies                                     │
│     ├── Compile TypeScript                                        │
│     ├── Run unit tests                                           │
│     ├── Generate source maps                                      │
│     └── Build Docker image                                       │
│                                                                  │
│  2. TEST                                                         │
│     ├── Run integration tests                                    │
│     ├── Run E2E tests                                            │
│     ├── Security scanning                                        │
│     └── Performance benchmarks                                   │
│                                                                  │
│  3. DEPLOY - DEV                                                 │
│     ├── Deploy to development                                    │
│     ├── Run smoke tests                                          │
│     └── Notify team                                              │
│                                                                  │
│  4. DEPLOY - STAGING (on main branch)                           │
│     ├── Deploy to staging                                        │
│     ├── Run full test suite                                      │
│     └── Create release candidate                                 │
│                                                                  │
│  5. DEPLOY - PRODUCTION (manual approval)                        │
│     ├── Run database migrations                                  │
│     ├── Blue-green deployment                                    │
│     ├── Smoke tests                                              │
│     └── Monitor metrics                                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Build Pipeline

### GitHub Actions Workflow

```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
    tags: ['v*']
  pull_request:
    branches: [main, develop]

env:
  NODE_VERSION: '20.x'
  AWS_REGION: 'ap-south-1'
  ECR_REGISTRY: ${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.ap-south-1.amazonaws.com
  ECR_REPOSITORY: travel-agency-app

jobs:
  # Build and test job
  build:
    name: Build & Test
    runs-on: ubuntu-latest

    outputs:
      image-tag: ${{ steps.meta.outputs.tags }}
      version: ${{ steps.version.outputs.version }}

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for versioning

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run linter
        run: npm run lint

      - name: Run type check
        run: npm run type-check

      - name: Run unit tests
        run: npm run test:unit -- --coverage

      - name: Upload coverage reports
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/lcov.info
          flags: unittests
          name: codecov-umbrella

      - name: Build application
        run: npm run build
        env:
          NODE_ENV: production

      - name: Run integration tests
        run: npm run test:integration

      - name: Generate Docker metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.ECR_REGISTRY }}/${{ env.ECR_REPOSITORY }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha,prefix={{branch}}-
            type=raw,value=latest,enable={{is_default_branch}}

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build and push Docker image
        id: build-and-push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          build-args: |
            BUILD_DATE=${{ github.event.repository.updated_at }}
            VCS_REF=${{ github.sha }}
            VERSION=${{ steps.version.outputs.version }}

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ env.ECR_REGISTRY }}/${{ env.ECR_REPOSITORY }}:${{ github.sha }}
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy results to GitHub Security
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'

      - name: Extract version
        id: version
        run: |
          VERSION=$(node -p "require('./package.json').version")
          echo "version=$VERSION" >> $GITHUB_OUTPUT

  # Security scanning job
  security:
    name: Security Scan
    runs-on: ubuntu-latest
    needs: build

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run npm audit
        run: npm audit --audit-level=moderate
        continue-on-error: true

      - name: Run Snyk security scan
        uses: snyk/actions/node@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: --severity-threshold=high

      - name: CodeQL Analysis
        uses: github/codeql-action/analyze@v2
        with:
          languages: javascript, typescript

  # Deploy to development
  deploy-dev:
    name: Deploy to Development
    runs-on: ubuntu-latest
    needs: [build, security]
    if: github.ref == 'refs/heads/develop' && github.event_name == 'push'
    environment:
      name: development
      url: https://dev-app.travelagency.com

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Deploy to ECS (Development)
        run: |
          aws ecs update-service \
            --cluster travel-agency-dev \
            --service app \
            --force-new-deployment \
            --region ${{ env.AWS_REGION }}

      - name: Wait for deployment
        run: |
          aws ecs wait services-stable \
            --cluster travel-agency-dev \
            --services app \
            --region ${{ env.AWS_REGION }}

      - name: Run smoke tests
        run: |
          npm run test:smoke -- --base-url https://dev-app.travelagency.com

      - name: Notify Slack
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "✅ Deployed to Development",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*Development Deploy*\n• Branch: `${{ github.ref_name }}`\n• Commit: `${{ github.sha }}`\n• Author: ${{ github.actor }}\n• <https://dev-app.travelagency.com|View App>"
                  }
                }
              ]
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}

  # Deploy to staging
  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: [build, security]
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    environment:
      name: staging
      url: https://staging-app.travelagency.com

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Run database migrations
        run: |
          aws ecs run-task \
            --cluster travel-agency-staging \
            --task-definition migrate-task \
            --launch-type FARGATE \
            --network-configuration "awsvpcConfiguration={subnets=${{ secrets.PRIVATE_SUBNETS }},securityGroups=${{ secrets.APP_SG }},assignPublicIp=DISABLED}" \
            --region ${{ env.AWS_REGION }}

      - name: Deploy to ECS (Staging)
        run: |
          aws ecs update-service \
            --cluster travel-agency-staging \
            --service app \
            --force-new-deployment \
            --region ${{ env.AWS_REGION }}

      - name: Wait for deployment
        run: |
          aws ecs wait services-stable \
            --cluster travel-agency-staging \
            --services app \
            --region ${{ env.AWS_REGION }}

      - name: Run full test suite
        run: |
          npm run test:e2e -- --base-url https://staging-app.travelagency.com

      - name: Run performance tests
        run: |
          npm run test:performance -- --base-url https://staging-app.travelagency.com

  # Deploy to production (manual approval)
  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: [build, security, deploy-staging]
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    environment:
      name: production
      url: https://app.travelagency.com

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Create pre-deployment backup
        run: |
          BACKUP_ID=$(aws rds create-db-snapshot \
            --db-instance-identifier travelagency-db \
            --db-snapshot-identifier "pre-deploy-$(date +%Y%m%d-%H%M%S)" \
            --query 'DBSnapshot.DBSnapshotIdentifier' \
            --output text)
          echo "BACKUP_ID=$BACKUP_ID" >> $GITHUB_ENV

      - name: Run database migrations
        run: |
          aws ecs run-task \
            --cluster travel-agency-prod \
            --task-definition migrate-task \
            --launch-type FARGATE \
            --network-configuration "awsvpcConfiguration={subnets=${{ secrets.PRIVATE_SUBNETS }},securityGroups=${{ secrets.APP_SG }},assignPublicIp=DISABLED}" \
            --region ${{ env.AWS_REGION }}

      - name: Blue-green deployment
        run: |
          # Update task set with new version
          TASK_DEF_ARN=$(aws ecs describe-task-definition \
            --task-definition travel-agency-app \
            --query 'taskDefinition.taskDefinitionArn' \
            --output text)

          # Create new task set
          TASK_SET_ID=$(aws ecs create-task-set \
            --cluster travel-agency-prod \
            --service travel-agency-prod \
            --task-definition $TASK_DEF_ARN \
            --launch-type FARGATE \
            --network-configuration "awsvpcConfiguration={subnets=${{ secrets.PRIVATE_SUBNETS }},securityGroups=${{ secrets.APP_SG }},assignPublicIp=DISABLED}" \
            --load-balancers "targetGroupArn=${{ secrets.TARGET_GROUP_BLUE }},containerName=app,containerPort=3000" \
            --query 'taskSets[0].taskSetArn' \
            --output text)

          echo "TASK_SET_ID=$TASK_SET_ID" >> $GITHUB_ENV

      - name: Wait for task set to be stable
        run: |
          aws ecs wait tasks-running \
            --cluster travel-agency-prod \
            --tasks $TASK_SET_ID

      - name: Run smoke tests against new version
        run: |
          npm run test:smoke -- --base-url https://app.travelagency.com

      - name: Switch traffic to new version
        run: |
          aws ecs update-service-primary-task-set \
            --cluster travel-agency-prod \
            --service travel-agency-prod \
            --primary-task-set $TASK_SET_ID

      - name: Wait for service stabilization
        run: |
          aws ecs wait services-stable \
            --cluster travel-agency-prod \
            --services travel-agency-prod

      - name: Monitor for errors (5 minute window)
        run: |
          sleep 300
          ERROR_COUNT=$(aws cloudwatch get-metric-statistics \
            --namespace ApplicationELB \
            --metric-name HTTPCode_ELB_5XX \
            --dimensions Name=LoadBalancer,Value=${{ secrets.ALB_ARN }} \
            --start-time $(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%S) \
            --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
            --period 60 \
            --statistics Sum \
            --query 'Datapoints[0].Sum' \
            --output text)

          if (( $(echo "$ERROR_COUNT > 10" | bc -l) )); then
            echo "Too many errors detected: $ERROR_COUNT"
            exit 1
          fi

      - name: Cleanup old task set
        run: |
          # Delete old task set after successful deployment
          aws ecs delete-task-set \
            --cluster travel-agency-prod \
            --service travel-agency-prod \
            --task-set $OLD_TASK_SET_ID

      - name: Notify Slack on success
        if: success()
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "🚀 Deployed to Production",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*Production Deploy*\n• Version: `${{ needs.build.outputs.version }}`\n• Commit: `${{ github.sha }}`\n• <https://app.travelagency.com|View App>"
                  }
                }
              ]
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}

      - name: Rollback on failure
        if: failure()
        run: |
          # Revert to previous task set
          aws ecs update-service-primary-task-set \
            --cluster travel-agency-prod \
            --service travel-agency-prod \
            --primary-task-set $OLD_TASK_SET_ID

          # Notify team
          curl -X POST ${{ secrets.SLACK_WEBHOOK_URL }} \
            -H 'Content-Type: application/json' \
            -d '{"text":"🚨 PRODUCTION ROLLBACK", "blocks":[{"type":"section","text":{"type":"mrkdwn","text":"*Deployment failed - rolled back*\n• Version: `${{ needs.build.outputs.version }}`"}}]}'
```

---

## Docker Containerization

### Multi-Stage Dockerfile

```dockerfile
# Dockerfile
# Stage 1: Dependencies
FROM node:20-alpine AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./
RUN npm ci --only=production && \
    npm cache clean --force

# Stage 2: Builder
FROM node:20-alpine AS builder
WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build arguments
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

ENV NODE_ENV=production \
    BUILD_DATE=${BUILD_DATE} \
    VCS_REF=${VCS_REF} \
    VERSION=${VERSION}

# Build application
RUN npm run build

# Stage 3: Production image
FROM node:20-alpine AS runner
WORKDIR /app

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy built application
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Set environment
ENV NODE_ENV=production \
    PORT=3000 \
    HOSTNAME="0.0.0.0"

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000/health', (r) => {if(r.statusCode !== 200) throw new Error(r.statusCode)})"

# Start application
CMD ["node", "server.js"]
```

### Docker Compose for Development

```yaml
# docker-compose.yml
version: '3.9'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.dev
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/travelagency
      - REDIS_URL=redis://redis:6379
    volumes:
      - .:/app
      - /app/node_modules
      - /app/.next
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=travelagency
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # Mailhog for email testing
  mailhog:
    image: mailhog/mailhog
    ports:
      - "1025:1025"
      - "8025:8025"

volumes:
  postgres_data:
  redis_data:
```

---

## Multi-Environment Deployments

### Environment Configuration

```typescript
// config/environment.ts
interface EnvironmentConfig {
  name: 'development' | 'staging' | 'production';
  apiUrl: string;
  wsUrl: string;
  cdnUrl: string;
  sentryDsn?: string;
  features: Record<string, boolean>;
  limits: {
    maxFileSize: number;
    maxUploadSize: number;
  };
}

const configs: Record<string, EnvironmentConfig> = {
  development: {
    name: 'development',
    apiUrl: 'http://localhost:3000/api',
    wsUrl: 'ws://localhost:3000',
    cdnUrl: 'http://localhost:3000',
    features: {
      debugMode: true,
      newDashboard: true,
      aiRecommendations: true,
    },
    limits: {
      maxFileSize: 10 * 1024 * 1024, // 10MB
      maxUploadSize: 50 * 1024 * 1024,
    },
  },

  staging: {
    name: 'staging',
    apiUrl: 'https://staging-api.travelagency.com',
    wsUrl: 'wss://staging-api.travelagency.com',
    cdnUrl: 'https://staging-cdn.travelagency.com',
    sentryDsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
    features: {
      debugMode: false,
      newDashboard: true,
      aiRecommendations: true,
    },
    limits: {
      maxFileSize: 5 * 1024 * 1024,
      maxUploadSize: 20 * 1024 * 1024,
    },
  },

  production: {
    name: 'production',
    apiUrl: 'https://api.travelagency.com',
    wsUrl: 'wss://api.travelagency.com',
    cdnUrl: 'https://cdn.travelagency.com',
    sentryDsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
    features: {
      debugMode: false,
      newDashboard: false,
      aiRecommendations: false,
    },
    limits: {
      maxFileSize: 5 * 1024 * 1024,
      maxUploadSize: 20 * 1024 * 1024,
    },
  },
};

export function getConfig(): EnvironmentConfig {
  const env = process.env.NEXT_PUBLIC_APP_ENV || 'development';
  return configs[env] || configs.development;
}
```

### Deployment Script

```typescript
// scripts/deploy.ts
import { execSync } from 'child_process';
import { ECSClient } from '@aws-sdk/client-ecs';
import { readFileSync } from 'fs';

interface DeployOptions {
  environment: 'development' | 'staging' | 'production';
  version: string;
  skipMigrations?: boolean;
  force?: boolean;
}

async function deploy(options: DeployOptions) {
  console.log(`🚀 Deploying version ${options.version} to ${options.environment}`);

  // Validate environment
  const validEnvs = ['development', 'staging', 'production'];
  if (!validEnvs.includes(options.environment)) {
    throw new Error(`Invalid environment: ${options.environment}`);
  }

  // Get cluster and service names
  const cluster = `travel-agency-${options.environment}`;
  const service = 'app';

  // Run database migrations
  if (!options.skipMigrations) {
    console.log('📊 Running database migrations...');
    await runMigrations(options.environment);
  }

  // Get current task definition
  const ecs = new ECSClient({ region: 'ap-south-1' });
  const currentService = await ecs.describeServices({
    cluster,
    services: [service],
  });

  const currentTaskDef = currentService.services[0].taskDefinition;

  // Create new task definition
  console.log('📦 Creating new task definition...');
  const taskDefArn = await createTaskDefinition(options.version);

  // Update service
  console.log('🔄 Updating service...');
  await ecs.updateService({
    cluster,
    service,
    taskDefinition: taskDefArn,
    forceNewDeployment: options.force,
  });

  // Wait for stability
  console.log('⏳ Waiting for deployment to stabilize...');
  await waitForStability(cluster, service);

  // Run smoke tests
  console.log('🧪 Running smoke tests...');
  await runSmokeTests(options.environment);

  console.log('✅ Deployment complete!');
}

async function runMigrations(environment: string): Promise<void> {
  // Run migrations in a one-off task
  const ecs = new ECSClient({ region: 'ap-south-1' });
  const cluster = `travel-agency-${environment}`;

  await ecs.runTask({
    cluster,
    taskDefinition: 'migrate-task',
    launchType: 'FARGATE',
    networkConfiguration: {
      awsvpcConfiguration: {
        subnets: process.env.PRIVATE_SUBNETS!.split(','),
        securityGroups: [process.env.APP_SG!],
        assignPublicIp: 'DISABLED',
      },
    },
  });

  // Wait for task to complete
  await new Promise((resolve) => setTimeout(resolve, 30000));
}

async function createTaskDefinition(version: string): Promise<string> {
  const ecs = new ECSClient({ region: 'ap-south-1' });
  const imageUrl = `${process.env.ECR_REGISTRY}/travel-agency-app:${version}`;

  const taskDef = await ecs.registerTaskDefinition({
    family: 'travel-agency-app',
    containerDefinitions: [
      {
        name: 'app',
        image: imageUrl,
        cpu: 1024,
        memory: 2048,
        essential: true,
        portMappings: [{ containerPort: 3000, protocol: 'tcp' }],
        environment: [
          { name: 'NODE_ENV', value: 'production' },
          { name: 'VERSION', value },
        ],
        secrets: [
          { name: 'DATABASE_URL', valueFrom: process.env.DATABASE_URL_ARN! },
          { name: 'JWT_SECRET', valueFrom: process.env.JWT_SECRET_ARN! },
        ],
        logConfiguration: {
          logDriver: 'awslogs',
          options: {
            'awslogs-group': '/ecs/travel-agency',
            'awslogs-region': 'ap-south-1',
            'awslogs-stream-prefix': 'app',
          },
        },
      },
    ],
    networkMode: 'awsvpc',
    requiresCompatibilities: ['FARGATE'],
    cpu: '1024',
    memory: '2048',
    executionRoleArn: process.env.ECS_EXECUTION_ROLE!,
    taskRoleArn: process.env.ECS_TASK_ROLE!,
  });

  return taskDef.taskDefinition!.taskDefinitionArn!;
}

async function waitForStability(cluster: string, service: string): Promise<void> {
  const ecs = new ECSClient({ region: 'ap-south-1' });

  const maxWait = 10 * 60 * 1000; // 10 minutes
  const startTime = Date.now();

  while (Date.now() - startTime < maxWait) {
    const { services } = await ecs.describeServices({ cluster, services: [service] });
    const deployments = services[0].deployments;

    const primaryDeployment = deployments.find((d) => d.status === 'PRIMARY');
    if (primaryDeployment && primaryDeployment.rolloutState === 'COMPLETED') {
      return;
    }

    if (primaryDeployment && primaryDeployment.rolloutState === 'FAILED') {
      throw new Error('Deployment failed');
    }

    await new Promise((resolve) => setTimeout(resolve, 10000));
  }

  throw new Error('Deployment timed out');
}

async function runSmokeTests(environment: string): Promise<void> {
  const baseUrl = environment === 'production'
    ? 'https://app.travelagency.com'
    : environment === 'staging'
    ? 'https://staging-app.travelagency.com'
    : 'https://dev-app.travelagency.com';

  const response = await fetch(`${baseUrl}/health`);
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }

  const data = await response.json();
  if (data.status !== 'healthy') {
    throw new Error('Application not healthy');
  }
}

// CLI
const args = process.argv.slice(2);
const environment = args[0] as DeployOptions['environment'];
const version = args[1];

deploy({ environment, version })
  .catch((err) => {
    console.error('❌ Deployment failed:', err);
    process.exit(1);
  });
```

---

## Database Migrations

### Migration System

```typescript
// migrations/migrate.ts
import { Pool } from 'pg';
import { readdirSync } from 'fs';
import { join } from 'path';

interface Migration {
  name: string;
  filename: string;
  appliedAt?: Date;
}

export class MigrationRunner {
  constructor(private pool: Pool) {}

  async createMigrationsTable(): Promise<void> {
    await this.pool.query(`
      CREATE TABLE IF NOT EXISTS schema_migrations (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL UNIQUE,
        filename VARCHAR(255) NOT NULL UNIQUE,
        applied_at TIMESTAMPTZ DEFAULT NOW()
      );
    `);
  }

  async getAppliedMigrations(): Promise<Migration[]> {
    const result = await this.pool.query(`
      SELECT name, filename, applied_at
      FROM schema_migrations
      ORDER BY applied_at ASC
    `);
    return result.rows;
  }

  async getPendingMigrations(): Promise<Migration[]> {
    const applied = await this.getAppliedMigrations();
    const appliedNames = new Set(applied.map((m) => m.name));

    const migrationFiles = readdirSync(join(__dirname, 'migrations'))
      .filter((f) => f.endsWith('.sql'))
      .sort();

    return migrationFiles
      .filter((f) => !appliedNames.has(f.replace('.sql', '')))
      .map((filename) => ({
        name: filename.replace('.sql', ''),
        filename,
      }));
  }

  async runMigration(migration: Migration): Promise<void> {
    const migrationPath = join(__dirname, 'migrations', migration.filename);
    const sql = readFileSync(migrationPath, 'utf-8');

    await this.pool.query('BEGIN');

    try {
      // Execute migration
      await this.pool.query(sql);

      // Record migration
      await this.pool.query(
        'INSERT INTO schema_migrations (name, filename) VALUES ($1, $2)',
        [migration.name, migration.filename]
      );

      await this.pool.query('COMMIT');
      console.log(`✅ Applied: ${migration.name}`);
    } catch (error) {
      await this.pool.query('ROLLBACK');
      console.error(`❌ Failed: ${migration.name}`, error);
      throw error;
    }
  }

  async migrate(): Promise<void> {
    await this.createMigrationsTable();
    const pending = await this.getPendingMigrations();

    if (pending.length === 0) {
      console.log('No pending migrations');
      return;
    }

    console.log(`Running ${pending.length} migrations...`);

    for (const migration of pending) {
      await this.runMigration(migration);
    }

    console.log('✅ All migrations applied');
  }

  async rollback(steps = 1): Promise<void> {
    const applied = await this.getPendingMigrations();
    const toRollback = applied.slice(-steps);

    if (toRollback.length === 0) {
      console.log('No migrations to rollback');
      return;
    }

    for (const migration of toRollback.reverse()) {
      const rollbackPath = join(__dirname, 'migrations', `${migration.name}.down.sql`);
      if (!existsSync(rollbackPath)) {
        console.log(`⚠️  No rollback file for: ${migration.name}`);
        continue;
      }

      const sql = readFileSync(rollbackPath, 'utf-8');

      await this.pool.query('BEGIN');

      try {
        await this.pool.query(sql);

        await this.pool.query(
          'DELETE FROM schema_migrations WHERE name = $1',
          [migration.name]
        );

        await this.pool.query('COMMIT');
        console.log(`✅ Rolled back: ${migration.name}`);
      } catch (error) {
        await this.pool.query('ROLLBACK');
        console.error(`❌ Rollback failed: ${migration.name}`, error);
        throw error;
      }
    }
  }
}

// Migration file example: migrations/20240115000001_create_trips_table.sql
/*
CREATE TABLE trips (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  customer_id UUID NOT NULL REFERENCES customers(id),
  destination VARCHAR(255) NOT NULL,
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  budget DECIMAL(12, 2),
  status VARCHAR(50) DEFAULT 'inquiry',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_trips_customer_id ON trips(customer_id);
CREATE INDEX idx_trips_status ON trips(status);
CREATE INDEX idx_trips_dates ON trips(start_date, end_date);
*/
```

---

## Feature Flags

### Feature Flag Service

```typescript
interface FeatureFlag {
  name: string;
  enabled: boolean;
  description: string;
  rolloutPercentage: number;
  whitelist: string[]; // User IDs
  blacklist: string[]; // User IDs
  conditions?: FlagCondition[];
}

interface FlagCondition {
  type: 'user_attribute' | 'agency_tier' | 'geolocation';
  field: string;
  operator: 'eq' | 'neq' | 'in' | 'contains';
  value: any;
}

export class FeatureFlagService {
  private flags: Map<string, FeatureFlag> = new Map();

  constructor() {
    this.loadFlags();
    // Reload flags every minute
    setInterval(() => this.loadFlags(), 60000);
  }

  private async loadFlags(): Promise<void> {
    const flags = await FeatureFlagRepository.findAll();
    this.flags.clear();

    for (const flag of flags) {
      this.flags.set(flag.name, flag);
    }
  }

  isEnabled(
    flagName: string,
    context: {
      userId?: string;
      agencyId?: string;
      attributes?: Record<string, any>;
    }
  ): boolean {
    const flag = this.flags.get(flagName);

    // Flag doesn't exist = disabled
    if (!flag) return false;

    // Explicitly disabled
    if (!flag.enabled) return false;

    // Blacklist check
    if (context.userId && flag.blacklist.includes(context.userId)) {
      return false;
    }

    // Whitelist check
    if (context.userId && flag.whitelist.includes(context.userId)) {
      return true;
    }

    // Rollout percentage
    if (flag.rolloutPercentage < 100) {
      const hash = this.hashUserId(flag.name, context.userId || context.agencyId || '');
      const bucket = hash % 100;
      if (bucket >= flag.rolloutPercentage) {
        return false;
      }
    }

    // Condition checks
    if (flag.conditions) {
      return this.evaluateConditions(flag.conditions, context);
    }

    return true;
  }

  private hashUserId(flagName: string, userId: string): number {
    const str = `${flagName}:${userId}`;
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      hash = ((hash << 5) - hash) + str.charCodeAt(i);
      hash |= 0;
    }
    return Math.abs(hash);
  }

  private evaluateConditions(
    conditions: FlagCondition[],
    context: Record<string, any>
  ): boolean {
    return conditions.every((condition) => {
      const value = this.getValueByPath(context, condition.field);

      switch (condition.operator) {
        case 'eq':
          return value === condition.value;
        case 'neq':
          return value !== condition.value;
        case 'in':
          return Array.isArray(condition.value) && condition.value.includes(value);
        case 'contains':
          return typeof value === 'string' && value.includes(condition.value);
        default:
          return false;
      }
    });
  }

  private getValueByPath(obj: any, path: string): any {
    return path.split('.').reduce((current, key) => current?.[key], obj);
  }

  // React hook
  useFlag(flagName: string, initialContext?: Record<string, any>): boolean {
    const [enabled, setEnabled] = useState(false);
    const user = useUser();

    useEffect(() => {
      const result = this.isEnabled(flagName, {
        userId: user?.id,
        agencyId: user?.agencyId,
        attributes: initialContext,
      });
      setEnabled(result);
    }, [flagName, user, initialContext]);

    return enabled;
  }
}

// Usage example
const featureFlags = new FeatureFlagService();

// In component
function NewDashboard() {
  const isEnabled = featureFlags.useFlag('newDashboard');

  if (!isEnabled) {
    return <LegacyDashboard />;
  }

  return <ModernDashboard />;
}
```

---

## Rollback Strategies

### Rollback Automation

```typescript
export class RollbackService {
  constructor(private ecs: ECSClient) {}

  async rollbackService(
    cluster: string,
    service: string,
    options: {
      toTaskDefinition?: string;
      keepTaskSet?: boolean;
    } = {}
  ): Promise<void> {
    // Get current service state
    const { services } = await this.ecs.describeServices({ cluster, services: [service] });
    const currentService = services[0];

    // Get current primary task set
    const primaryTaskSet = currentService.taskSets.find((ts) => ts.status === 'PRIMARY');
    const activeTaskSets = currentService.taskSets.filter((ts) => ts.status === 'ACTIVE');

    if (activeTaskSets.length === 0) {
      throw new Error('No active task sets to roll back to');
    }

    // Determine rollback target
    let rollbackTarget: string;

    if (options.toTaskDefinition) {
      // Rollback to specific task definition
      rollbackTarget = options.toTaskDefinition;
    } else {
      // Rollback to previous task set (before current primary)
      const previousTaskSet = activeTaskSets.find((ts) =>
        ts.taskDefinition !== primaryTaskSet.taskDefinition
      );

      if (!previousTaskSet) {
        throw new Error('No previous task set found');
      }

      rollbackTarget = previousTaskSet.taskDefinition || previousTaskSet.taskSetArn;
    }

    console.log(`Rolling back to: ${rollbackTarget}`);

    // Perform rollback
    if (primaryTaskSet.status === 'PRIMARY') {
      // Blue-green rollback: switch primary back
      const previousPrimary = activeTaskSets.find((ts) =>
        ts.taskDefinition === rollbackTarget
      );

      if (previousPrimary) {
        await this.ecs.updateService_primary_task_set({
          cluster,
          service,
          primaryTaskSet: previousPrimary.taskSetArn,
        });

        console.log('✅ Rolled back to previous task set');
      }
    } else {
      // Standard rollback: update service with old task definition
      await this.ecs.updateService({
        cluster,
        service,
        taskDefinition: rollbackTarget,
        forceNewDeployment: true,
      });

      console.log('✅ Rolled back to previous task definition');
    }

    // Wait for stability
    await this.waitForStability(cluster, service);

    // Optionally delete failed task set
    if (!options.keepTaskSet && primaryTaskSet) {
      await this.ecs.deleteTaskSet({
        cluster,
        service,
        taskSet: primaryTaskSet.taskSetArn,
      });
      console.log('🗑️  Deleted failed task set');
    }
  }

  async rollbackDatabase(migrationName: string): Promise<void> {
    const migrationRunner = new MigrationRunner(this.pool);

    try {
      await migrationRunner.rollback();
      console.log(`✅ Rolled back migration: ${migrationName}`);
    } catch (error) {
      console.error(`❌ Failed to rollback migration: ${migrationName}`, error);
      throw error;
    }
  }

  private async waitForStability(cluster: string, service: string): Promise<void> {
    const maxWait = 10 * 60 * 1000;
    const startTime = Date.now();

    while (Date.now() - startTime < maxWait) {
      const { services } = await this.ecs.describeServices({ cluster, services: [service] });
      const deployments = services[0].deployments;

      const primaryDeployment = deployments.find((d) => d.status === 'PRIMARY');
      if (primaryDeployment && primaryDeployment.rolloutState === 'COMPLETED') {
        return;
      }

      await new Promise((resolve) => setTimeout(resolve, 5000));
    }

    throw new Error('Rollback stabilization timed out');
  }
}

// CLI command for manual rollback
// scripts/rollback.ts
async function main() {
  const args = process.argv.slice(2);
  const environment = args[0];
  const target = args[1]; // task definition or 'previous'

  const rollbackService = new RollbackService(new ECSClient({ region: 'ap-south-1' }));
  const cluster = `travel-agency-${environment}`;
  const service = 'app';

  await rollbackService.rollbackService(cluster, service, {
    toTaskDefinition: target === 'previous' ? undefined : target,
  });

  console.log('✅ Rollback complete');
}
```

---

## Release Strategies

### Blue-Green Deployment

```
┌─────────────────────────────────────────────────────────────────┐
│                    BLUE-GREEN DEPLOYMENT                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  STEP 1: Initial State                                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Load Balancer                                           │    │
│  │      │                                                   │    │
│  │      └──────► 100% ──► BLUE (v1.0)                      │    │
│  │                  GREEN (v1.1) [idle]                    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  STEP 2: Deploy New Version to GREEN                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Load Balancer                                           │    │
│  │      │                                                   │    │
│  │      └──────► 100% ──► BLUE (v1.0)                      │    │
│  │                  GREEN (v1.2) [deploying]               │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  STEP 3: Test GREEN                                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Load Balancer                                           │    │
│  │      │                                                   │    │
│  │      └──────► 100% ──► BLUE (v1.0)                      │    │
│  │                  GREEN (v1.2) [testing]                  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  STEP 4: Switch Traffic                                         │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Load Balancer                                           │    │
│  │      │                                                   │    │
│  │      └──────► 100% ──► GREEN (v1.2)                     │    │
│  │                  BLUE (v1.0) [idle]                     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  STEP 5: Cleanup (keep BLUE for quick rollback)                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Canary Deployment

```
┌─────────────────────────────────────────────────────────────────┐
│                     CANARY DEPLOYMENT                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Traffic Distribution Over Time:                                │
│                                                                  │
│  100% │     ┌─────────────────────────────────────┐            │
│   90% │     │                                     │            │
│   80% │     │  ┌─────────┐                       │            │
│   70% │     │  │         │ 10% Canary            │            │
│   60% │────┼──┼────┐    │  ▓▓▓                     │            │
│   50% │    │  │    │    │  ▓▓▓▓▓▓                 │            │
│   40% │    │  │    │    │  ▓▓▓▓▓▓▓▓▓  50% Canary   │            │
│   30% │    │  │    └────┤  ▓▓▓▓▓▓▓▓▓▓▓▓             │            │
│   20% │    │  │         │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ 100%        │            │
│   10% │    │  │         └──┴───────────────────────►            │
│    0% │────┼──┴───────────────────────────────────            │
│       │    │    │    │    │    │    │    │                    │
│       └────┴────┴────┴────┴────┴────┴────┴──── Time (hours)    │
│           0    1    2    3    4    5    6                     │
│                                                                  │
│  If errors > threshold: Auto rollback to previous version        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Canary Implementation

```typescript
export class CanaryDeployment {
  async deployCanary(
    cluster: string,
    service: string,
    newTaskDefinition: string,
    options: {
      canaryPercentage: number;
      monitoringDuration: number; // minutes
      errorThreshold: number; // error rate percentage
    }
  ): Promise<void> {
    const ecs = new ECSClient({ region: 'ap-south-1' });

    // Step 1: Create canary task set
    console.log('Creating canary task set...');
    const canaryTaskSet = await ecs.create_task_set({
      cluster,
      service,
      taskDefinition: newTaskDefinition,
      launchType: 'FARGATE',
      networkConfiguration: {
        awsvpcConfiguration: {
          subnets: process.env.PRIVATE_SUBNETS!.split(','),
          securityGroups: [process.env.APP_SG!],
          assignPublicIp: 'DISABLED',
        },
      },
      scale: {
        value: options.canaryPercentage,
        unit: 'PERCENT',
      },
      loadBalancers: [
        {
          targetGroupArn: process.env.CANARY_TARGET_GROUP_ARN!,
          containerName: 'app',
          containerPort: 3000,
        },
      ],
    });

    console.log(`Canary task set created: ${canaryTaskSet.taskSets[0].taskSetArn}`);

    // Step 2: Monitor canary
    console.log('Monitoring canary deployment...');
    const isHealthy = await this.monitorCanary(
      cluster,
      service,
      options.monitoringDuration,
      options.errorThreshold
    );

    if (!isHealthy) {
      console.log('❌ Canary failed - rolling back');
      await this.rollbackCanary(cluster, service, canaryTaskSet.taskSets[0].taskSetArn);
      throw new Error('Canary deployment failed');
    }

    // Step 3: Gradual rollout
    console.log('✅ Canary healthy - proceeding with gradual rollout');
    await this.gradualRollout(
      cluster,
      service,
      newTaskDefinition,
      canaryTaskSet.taskSets[0].taskSetArn
    );
  }

  private async monitorCanary(
    cluster: string,
    service: string,
    durationMinutes: number,
    errorThreshold: number
  ): Promise<boolean> {
    const startTime = Date.now();
    const endTime = startTime + durationMinutes * 60 * 1000;
    const checkInterval = 60000; // Check every minute

    while (Date.now() < endTime) {
      // Check error rate
      const errorRate = await this.getErrorRate();

      if (errorRate > errorThreshold) {
        console.log(`❌ Error rate ${errorRate}% exceeds threshold ${errorThreshold}%`);
        return false;
      }

      // Check response time
      const p95Latency = await this.getP95Latency();
      if (p95Latency > 1000) {
        console.log(`⚠️  High latency detected: ${p95Latency}ms`);
      }

      console.log(`✅ Canary check passed (${Math.round((Date.now() - startTime) / 1000)}s)`);

      // Wait for next check
      await new Promise((resolve) => setTimeout(resolve, checkInterval));
    }

    return true;
  }

  private async rollbackCanary(
    cluster: string,
    service: string,
    canaryTaskSetArn: string
  ): Promise<void> {
    const ecs = new ECSClient({ region: 'ap-south-1' });

    await ecs.deleteTaskSet({
      cluster,
      service,
      taskSet: canaryTaskSetArn,
    });

    console.log('✅ Canary rolled back');
  }

  private async gradualRollout(
    cluster: string,
    service: string,
    newTaskDefinition: string,
    canaryTaskSetArn: string
  ): Promise<void> {
    const ecs = new ECSClient({ region: 'ap-south-1' });
    const rolloutSteps = [25, 50, 75, 100];

    for (const percentage of rolloutSteps) {
      console.log(`Rolling out to ${percentage}%...`);

      // Update primary task set weight
      await ecs.update_service_primary_task_set({
        cluster,
        service,
        primaryTaskSet: canaryTaskSetArn,
        scale: {
          value: percentage,
          unit: 'PERCENT',
        },
      });

      // Wait for stabilization
      await new Promise((resolve) => setTimeout(resolve, 30000));

      // Health check
      const errorRate = await this.getErrorRate();
      if (errorRate > 1) {
        throw new Error(`High error rate at ${percentage}% rollout: ${errorRate}%`);
      }

      console.log(`✅ ${percentage}% rollout complete`);
    }

    // Finalize - delete old task set
    const { services } = await ecs.describeServices({ cluster, services: [service] });
    const oldTaskSet = services[0].taskSets.find((ts) =>
      ts.taskDefinition !== newTaskDefinition && ts.status !== 'PRIMARY'
    );

    if (oldTaskSet) {
      await ecs.delete_task_set({
        cluster,
        service,
        taskSet: oldTaskSet.taskSetArn,
      });
    }

    console.log('✅ Full deployment complete');
  }

  private async getErrorRate(): Promise<number> {
    const cloudwatch = new CloudWatchClient({ region: 'ap-south-1' });

    const endTime = new Date();
    const startTime = new Date(endTime.getTime() - 60000); // Last 1 minute

    const result = await cloudwatch.getMetric_statistics({
      Namespace: 'ApplicationELB',
      MetricName: 'HTTPCode_Target_5XX',
      Dimensions: [
        { Name: 'LoadBalancer', Value: process.env.ALB_ARN! },
      ],
      StartTime: startTime,
      EndTime: endTime,
      Period: 60,
      Statistics: ['Sum'],
    });

    const datapoints = result.Datapoints || [];
    const totalErrors = datapoints.reduce((sum, dp) => sum + (dp.Sum || 0), 0);

    // Get total requests for error rate calculation
    const totalRequests = await this.getTotalRequests(startTime, endTime);

    return totalRequests > 0 ? (totalErrors / totalRequests) * 100 : 0;
  }

  private async getP95Latency(): Promise<number> {
    const cloudwatch = new CloudWatchClient({ region: 'ap-south-1' });

    const endTime = new Date();
    const startTime = new Date(endTime.getTime() - 60000);

    const result = await cloudwatch.getMetric_statistics({
      Namespace: 'ApplicationELB',
      MetricName: 'TargetResponseTime',
      Dimensions: [
        { Name: 'LoadBalancer', Value: process.env.ALB_ARN! },
      ],
      StartTime: startTime,
      EndTime: endTime,
      Period: 60,
      Statistics: ['p95'],
    });

    const datapoints = result.Datapoints || [];
    return datapoints.length > 0 ? datapoints[0].p95 || 0 : 0;
  }

  private async getTotalRequests(startTime: Date, endTime: Date): Promise<number> {
    const cloudwatch = new CloudWatchClient({ region: 'ap-south-1' });

    const result = await cloudwatch.get_metric_statistics({
      Namespace: 'ApplicationELB',
      MetricName: 'RequestCount',
      Dimensions: [
        { Name: 'LoadBalancer', Value: process.env.ALB_ARN! },
      ],
      StartTime: startTime,
      EndTime: endTime,
      Period: 60,
      Statistics: ['Sum'],
    });

    const datapoints = result.Datapoints || [];
    return datapoints.reduce((sum, dp) => sum + (dp.Sum || 0), 0);
  }
}
```

---

**Last Updated:** 2026-04-25

**Next:** DEVOPS_03 — Monitoring Deep Dive (Metrics, alerts, dashboards, observability)
