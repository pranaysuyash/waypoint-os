# SECURITY_04: Infrastructure Security Deep Dive

> Network security, container security, secrets management, and infrastructure hardening

---

## Table of Contents

1. [Overview](#overview)
2. [Network Security](#network-security)
3. [Container Security](#container-security)
4. [Kubernetes Security](#kubernetes-security)
5. [Secrets Management](#secrets-management)
6. [IAM & Least Privilege](#iam--least-privilege)
7. [Security Monitoring](#security-monitoring)
8. [Intrusion Detection](#intrusion-detection)
9. [Vulnerability Management](#vulnerability-management)
10. [Incident Response](#incident-response)
11. [API Specification](#api-specification)
12. [Testing Scenarios](#testing-scenarios)
13. [Metrics & Monitoring](#metrics--monitoring)

---

## Overview

Infrastructure security provides the foundation for all application-level security controls. This document covers network segmentation, container hardening, secrets management, and incident response capabilities.

### Security Domains

| Domain | Key Controls | Risk Level |
|--------|-------------|------------|
| **Network** | VPC, security groups, NACLs, WAF | Critical |
| **Container** | Image scanning, runtime protection, least privilege | High |
| **Kubernetes** | RBAC, pod security, network policies | High |
| **Secrets** | Encryption, rotation, audit logging | Critical |
| **Monitoring** | Logging, alerting, forensics | Medium |

### Defense in Depth

```
┌─────────────────────────────────────────────────────────────┐
│                     Edge Security Layer                      │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │   WAF   │  │   DDoS  │  │   CDN   │  │  Firewall│        │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘        │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Network Security Layer                    │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │   VPC   │  │Subnets  │  │Security │  │   NACL  │        │
│  │ Peering │  │  (AZs)  │  │ Groups  │  │         │        │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘        │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   Compute Security Layer                    │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │  Image  │  │Runtime  │  │    K8s  │  │  Host   │        │
│  │ Scanning│  │Protection│ │  RBAC   │  │ Hardening│       │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘        │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   Application Security Layer                 │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │  AuthN  │  │  AuthZ  │  │Input    │  │Encryption│       │
│  │         │  │         │  │Validation│  │          │       │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘        │
└─────────────────────────────────────────────────────────────┘
```

---

## Network Security

### VPC Architecture

```typescript
// infrastructure/network/vpc-config.ts

interface VPCConfig {
  cidr: string;
  availabilityZones: string[];
  subnets: {
    public: SubnetConfig[];
    private: SubnetConfig[];
    isolated: SubnetConfig[];
    database: SubnetConfig[];
  };
  flowLogs: {
    enabled: boolean;
    retentionDays: number;
    destination: 's3' | 'cloudwatch';
  };
}

interface SubnetConfig {
  cidr: string;
  availabilityZone: string;
  type: 'public' | 'private' | 'isolated' | 'database';
  mapPublicIp?: boolean;
  tags?: Record<string, string>;
}

export const productionVPC: VPCConfig = {
  cidr: '10.0.0.0/16',
  availabilityZones: ['us-east-1a', 'us-east-1b', 'us-east-1c'],
  subnets: {
    // Public subnets for load balancers only
    public: [
      {
        cidr: '10.0.0.0/24',
        availabilityZone: 'us-east-1a',
        type: 'public',
        mapPublicIp: true,
        tags: { Layer: 'public', Tier: 'web' }
      },
      {
        cidr: '10.0.1.0/24',
        availabilityZone: 'us-east-1b',
        type: 'public',
        mapPublicIp: true,
        tags: { Layer: 'public', Tier: 'web' }
      },
      {
        cidr: '10.0.2.0/24',
        availabilityZone: 'us-east-1c',
        type: 'public',
        mapPublicIp: true,
        tags: { Layer: 'public', Tier: 'web' }
      }
    ],
    // Private subnets for application servers
    private: [
      {
        cidr: '10.0.10.0/24',
        availabilityZone: 'us-east-1a',
        type: 'private',
        mapPublicIp: false,
        tags: { Layer: 'private', Tier: 'application' }
      },
      {
        cidr: '10.0.11.0/24',
        availabilityZone: 'us-east-1b',
        type: 'private',
        mapPublicIp: false,
        tags: { Layer: 'private', Tier: 'application' }
      },
      {
        cidr: '10.0.12.0/24',
        availabilityZone: 'us-east-1c',
        type: 'private',
        mapPublicIp: false,
        tags: { Layer: 'private', Tier: 'application' }
      }
    ],
    // Isolated subnets for backend services (no internet gateway)
    isolated: [
      {
        cidr: '10.0.20.0/24',
        availabilityZone: 'us-east-1a',
        type: 'isolated',
        mapPublicIp: false,
        tags: { Layer: 'isolated', Tier: 'backend' }
      },
      {
        cidr: '10.0.21.0/24',
        availabilityZone: 'us-east-1b',
        type: 'isolated',
        mapPublicIp: false,
        tags: { Layer: 'isolated', Tier: 'backend' }
      }
    ],
    // Database subnets (no internet access, isolated)
    database: [
      {
        cidr: '10.0.30.0/24',
        availabilityZone: 'us-east-1a',
        type: 'database',
        mapPublicIp: false,
        tags: { Layer: 'database', Tier: 'data' }
      },
      {
        cidr: '10.0.31.0/24',
        availabilityZone: 'us-east-1b',
        type: 'database',
        mapPublicIp: false,
        tags: { Layer: 'database', Tier: 'data' }
      },
      {
        cidr: '10.0.32.0/24',
        availabilityZone: 'us-east-1c',
        type: 'database',
        mapPublicIp: false,
        tags: { Layer: 'database', Tier: 'data' }
      }
    ]
  },
  flowLogs: {
    enabled: true,
    retentionDays: 90,
    destination: 's3'
  }
};
```

### Security Groups & NACLs

```typescript
// infrastructure/network/security-groups.ts

interface SecurityGroupRule {
  protocol: 'tcp' | 'udp' | 'icmp' | '-1';
  fromPort: number;
  toPort: number;
  cidr?: string;
  sourceSecurityGroup?: string;
  description: string;
}

interface SecurityGroupConfig {
  name: string;
  description: string;
  ingress: SecurityGroupRule[];
  egress: SecurityGroupRule[];
  tags: Record<string, string>;
}

export const securityGroups: SecurityGroupConfig[] = [
  {
    name: 'alb-security-group',
    description: 'Security group for Application Load Balancer',
    ingress: [
      {
        protocol: 'tcp',
        fromPort: 443,
        toPort: 443,
        cidr: '0.0.0.0/0',
        description: 'HTTPS from anywhere'
      },
      {
        protocol: 'tcp',
        fromPort: 80,
        toPort: 80,
        cidr: '0.0.0.0/0',
        description: 'HTTP for redirect to HTTPS'
      }
    ],
    egress: [
      {
        protocol: '-1',
        fromPort: 0,
        toPort: 0,
        cidr: '0.0.0.0/0',
        description: 'Allow all outbound'
      }
    ],
    tags: { Tier: 'web', Component: 'alb' }
  },
  {
    name: 'application-security-group',
    description: 'Security group for application containers',
    ingress: [
      {
        protocol: 'tcp',
        fromPort: 3000,
        toPort: 3000,
        sourceSecurityGroup: 'alb-security-group',
        description: 'HTTPS from ALB'
      },
      {
        protocol: 'tcp',
        fromPort: 22,
        toPort: 22,
        cidr: '10.0.0.0/16', // VPN only
        description: 'SSH from VPN'
      }
    ],
    egress: [
      {
        protocol: 'tcp',
        fromPort: 443,
        toPort: 443,
        cidr: '0.0.0.0/0',
        description: 'HTTPS to external APIs'
      },
      {
        protocol: 'tcp',
        fromPort: 5432,
        toPort: 5432,
        sourceSecurityGroup: 'database-security-group',
        description: 'PostgreSQL to database'
      },
      {
        protocol: 'tcp',
        fromPort: 6379,
        toPort: 6379,
        sourceSecurityGroup: 'redis-security-group',
        description: 'Redis connection'
      }
    ],
    tags: { Tier: 'application', Component: 'containers' }
  },
  {
    name: 'database-security-group',
    description: 'Security group for RDS PostgreSQL',
    ingress: [
      {
        protocol: 'tcp',
        fromPort: 5432,
        toPort: 5432,
        sourceSecurityGroup: 'application-security-group',
        description: 'PostgreSQL from application'
      },
      {
        protocol: 'tcp',
        fromPort: 5432,
        toPort: 5432,
        cidr: '10.0.100.0/28', // Bastion host
        description: 'PostgreSQL from bastion'
      }
    ],
    egress: [],
    tags: { Tier: 'database', Component: 'rds' }
  },
  {
    name: 'redis-security-group',
    description: 'Security group for ElastiCache Redis',
    ingress: [
      {
        protocol: 'tcp',
        fromPort: 6379,
        toPort: 6379,
        sourceSecurityGroup: 'application-security-group',
        description: 'Redis from application'
      }
    ],
    egress: [],
    tags: { Tier: 'cache', Component: 'redis' }
  }
];

// Network ACLs (stateless, apply to subnets)
interface NACLRule {
  ruleNumber: number;
  protocol: 'tcp' | 'udp' | 'icmp' | '-1';
  ruleAction: 'allow' | 'deny';
  cidr: string;
  fromPort?: number;
  toPort?: number;
  description: string;
}

export const publicSubnetNACL: NACLRule[] = [
  // Inbound rules
  { ruleNumber: 100, protocol: 'tcp', ruleAction: 'allow', cidr: '0.0.0.0/0', fromPort: 443, toPort: 443, description: 'HTTPS' },
  { ruleNumber: 110, protocol: 'tcp', ruleAction: 'allow', cidr: '0.0.0.0/0', fromPort: 80, toPort: 80, description: 'HTTP' },
  { ruleNumber: 120, protocol: 'tcp', ruleAction: 'allow', cidr: '0.0.0.0/0', fromPort: 1024, toPort: 65535, description: 'Ephemeral ports' },
  { ruleNumber: 200, protocol: '-1', ruleAction: 'deny', cidr: '0.0.0.0/0', description: 'Deny all' },
  // Outbound rules
  { ruleNumber: 100, protocol: '-1', ruleAction: 'allow', cidr: '0.0.0.0/0', description: 'Allow all outbound' }
];
```

### Web Application Firewall (WAF)

```typescript
// infrastructure/network/waf-config.ts

interface WAFRule {
  name: string;
  priority: number;
  action: 'allow' | 'block' | 'count' | 'captcha';
  conditions: WAFCondition[];
}

interface WAFCondition {
  type: 'ip_match' | 'string_match' | 'size_constraint' | 'xss_match' | 'sql_injection' | 'rate_based';
  field?: string;
  value?: string;
  threshold?: number;
}

export const wafRules: WAFRule[] = [
  {
    name: 'block-known-malicious-ips',
    priority: 1,
    action: 'block',
    conditions: [
      {
        type: 'ip_match',
        value: 'threat-intelligence-feed'
      }
    ]
  },
  {
    name: 'rate-limit-api-endpoints',
    priority: 2,
    action: 'block',
    conditions: [
      {
        type: 'rate_based',
        field: '/api/*',
        threshold: 2000 // requests per 5 minutes
      }
    ]
  },
  {
    name: 'block-sql-injection',
    priority: 3,
    action: 'block',
    conditions: [
      {
        type: 'sql_injection',
        field: 'QUERY_STRING'
      },
      {
        type: 'sql_injection',
        field: 'body'
      }
    ]
  },
  {
    name: 'block-xss-attacks',
    priority: 4,
    action: 'block',
    conditions: [
      {
        type: 'xss_match',
        field: 'QUERY_STRING'
      },
      {
        type: 'xss_match',
        field: 'body'
      }
    ]
  },
  {
    name: 'limit-request-size',
    priority: 5,
    action: 'block',
    conditions: [
      {
        type: 'size_constraint',
        field: 'body',
        value: '10485760' // 10MB
      }
    ]
  },
  {
    name: 'block-common-attack-patterns',
    priority: 6,
    action: 'block',
    conditions: [
      {
        type: 'string_match',
        field: 'URI',
        value: '\\.\\.|/etc/passwd|/proc/self|cmd\\.exe'
      }
    ]
  },
  {
    name: 'captcha-suspicious-requests',
    priority: 7,
    action: 'captcha',
    conditions: [
      {
        type: 'string_match',
        field: 'USER_AGENT',
        value: 'bot|crawler|spider|scraper'
      }
    ]
  }
];
```

---

## Container Security

### Image Hardening

```typescript
// infrastructure/container/dockerfile-security.ts

// Secure base image guidelines
interface ContainerSecurityConfig {
  baseImage: {
    registry: 'dockerhub' | 'ecr' | 'ghcr';
    image: string;
    tag: string;
    digest?: string; // Pin to digest for immutability
  };
  user: string; // Non-root user
  capabilities: {
    drop: string[]; // Capabilities to drop
    add: string[]; // Capabilities to add (should be empty)
  };
  securityOptions: string[];
  readOnlyRootFilesystem: boolean;
  allowPrivilegeEscalation: false;
}

export const secureContainerConfig: ContainerSecurityConfig = {
  baseImage: {
    registry: 'ecr',
    image: 'node-alpine',
    tag: '20.11.0',
    digest: 'sha256:abc123...' // Pin to specific digest
  },
  user: 'nodeuser', // Non-root user
  capabilities: {
    drop: ['ALL'], // Drop all capabilities
    add: [] // Add none
  },
  securityOptions: [
    'no-new-privileges',
    'seccomp=default.json',
    'apparmor=docker-default'
  ],
  readOnlyRootFilesystem: true,
  allowPrivilegeEscalation: false
};

// Dockerfile security best practices
export const secureDockerfile = `
# Use specific version and digest
FROM node:20.11.0-alpine3.19@sha256:abc123...

# Build as non-root user
RUN addgroup -g 1001 -S nodeuser && \\
    adduser -S -u 1001 -G nodeuser nodeuser

# Install only necessary packages and cleanup
RUN apk add --no-cache \\
    dumb-init \\
    && rm -rf /var/cache/apk/*

# Set security options
ENV NODE_ENV=production \\
    SECURITY_OPTS="--no-warnings"

# Create non-root directories with proper permissions
RUN mkdir -p /app /app/logs /app/tmp && \\
    chown -R nodeuser:nodeuser /app

# Copy as non-root user
COPY --chown=nodeuser:nodeuser package*.json ./
COPY --chown=nodeuser:nodeuser . .

# Switch to non-root user early
USER nodeuser
WORKDIR /app

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
    CMD node healthcheck.js || exit 1

# Use dumb-init to handle signals properly
ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "server.js"]

# Remove all capabilities
# Drop all capabilities, add none
# Read-only root filesystem
# No privilege escalation
`;
```

### Image Scanning

```typescript
// infrastructure/container/image-scanning.ts

interface VulnerabilitySeverity {
  critical: number;
  high: number;
  medium: number;
  low: number;
  negligible: number;
}

interface Vulnerability {
  id: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'NEGLIGIBLE';
  cvss: number;
  package: string;
  installedVersion: string;
  fixedVersion: string;
  description: string;
  link: string;
}

interface ImageScanResult {
  image: string;
  digest: string;
  timestamp: Date;
  vulnerabilities: Vulnerability[];
  summary: VulnerabilitySeverity;
  passed: boolean;
  policy: {
    failOnSeverity: string[];
    ignoreCVEs: string[];
  };
}

export class ImageScanner {
  private readonly policy = {
    failOnSeverity: ['CRITICAL', 'HIGH'],
    ignoreCVEs: [
      'CVE-2021-1234', // False positive or accepted risk
      'CVE-2022-5678'  // Not exploitable in our context
    ]
  };

  async scanImage(imageUri: string): Promise<ImageScanResult> {
    // Integrate with scanning service (Trivy, ECR Scan, Aqua, etc.)
    const result = await this.performScan(imageUri);
    return this.evaluateResult(result);
  }

  private async performScan(imageUri: string): Promise<ImageScanResult> {
    // Implementation depends on scanning service
    // Example using Trivy:
    // const trivy = spawn('trivy', ['image', '--format', 'json', imageUri]);
    // const output = await trivy;
    // return JSON.parse(output);

    // Mock implementation
    return {
      image: imageUri,
      digest: 'sha256:abc123...',
      timestamp: new Date(),
      vulnerabilities: [],
      summary: {
        critical: 0,
        high: 0,
        medium: 2,
        low: 5,
        negligible: 10
      },
      passed: true,
      policy: this.policy
    };
  }

  private evaluateResult(result: ImageScanResult): ImageScanResult {
    const failableVulns = result.vulnerabilities.filter(
      v =>
        this.policy.failOnSeverity.includes(v.severity) &&
        !this.policy.ignoreCVEs.includes(v.id)
    );

    result.passed = failableVulns.length === 0;
    return result;
  }

  async enforcePolicy(imageUri: string): Promise<boolean> {
    const result = await this.scanImage(imageUri);

    if (!result.passed) {
      const failable = result.vulnerabilities
        .filter(v => !result.passed && this.policy.failOnSeverity.includes(v.severity))
        .map(v => `${v.id}: ${v.package} (${v.severity})`)
        .join('\n');

      throw new Error(
        `Image security scan failed. Found vulnerabilities:\n${failable}`
      );
    }

    return true;
  }
}

// CI/CD integration
export async function scanBeforeDeploy(imageUri: string): Promise<void> {
  const scanner = new ImageScanner();
  await scanner.enforcePolicy(imageUri);
  console.log(`✅ Image ${imageUri} passed security scan`);
}
```

### Runtime Security

```typescript
// infrastructure/container/runtime-security.ts

interface RuntimeSecurityPolicy {
  container: {
    allowedCapabilities: string[];
    droppedCapabilities: string[];
    allowPrivilegeEscalation: boolean;
    readOnlyRootFilesystem: boolean;
    runAsNonRoot: boolean;
    runAsUser: number;
    seccompProfile: string;
  };
  network: {
    allowedEgress: string[];
    allowedIngress: string[];
    denyAllEgress: boolean;
  };
  filesystem: {
    readOnlyPaths: string[];
    readWritePaths: string[];
  };
}

export const runtimePolicy: RuntimeSecurityPolicy = {
  container: {
    allowedCapabilities: [],
    droppedCapabilities: ['ALL'],
    allowPrivilegeEscalation: false,
    readOnlyRootFilesystem: true,
    runAsNonRoot: true,
    runAsUser: 1001,
    seccompProfile: 'runtime/default'
  },
  network: {
    allowedEgress: [
      'api.example.com:443',
      'cdn.example.com:443',
      '*.amazonaws.com:443'
    ],
    allowedIngress: [],
    denyAllEgress: false
  },
  filesystem: {
    readOnlyPaths: [
      '/',
      '/app',
      '/node_modules'
    ],
    readWritePaths: [
      '/app/tmp',
      '/app/logs'
    ]
  }
};

// Falco rules for runtime security monitoring
export const falcoRules = `
- rule: Detect webshell
  desc: Detect possible webshell file creation
  condition: >
    spawn and proc.name in (node, nginx) and
    file.name in (shell.php, jsp.jsp, aspx.aspx, cmd.aspx)
  output: >
    Possible webshell created (user=%user.name command=%proc.cmdline file=%file.name)
  priority: CRITICAL

- rule: Detect crypto miner
  desc: Detect cryptocurrency mining processes
  condition: >
    spawned_process and
    proc.name in (xmrig, minergate, cpuminer)
  output: >
    Crypto miner detected (user=%user.name command=%proc.cmdline)
  priority: CRITICAL

- rule: Detect reverse shell
  desc: Detect possible reverse shell connection
  condition: >
    spawn and proc.name in (bash, sh, nc, ncat) and
    fd.type in (ipv4, ipv6) and fd.net != 0
  output: >
    Possible reverse shell (user=%user.name command=%proc.cmdline)
  priority: CRITICAL

- rule: Detect container escape
  desc: Detect attempts to escape container
  condition: >
    spawn and proc.name in (mount, insmod, modprobe) and
    container.id != host
  output: >
    Container escape attempt (user=%user.name command=%proc.cmdline)
  priority: CRITICAL

- rule: Detect sensitive file access
  desc: Detect access to sensitive files
  condition: >
    open_read and
    file.path in (/etc/shadow, /etc/passwd, /root/.ssh, /app/.env)
  output: >
    Sensitive file accessed (user=%user.name file=%file.name)
  priority: WARNING
`;
```

---

## Kubernetes Security

### Pod Security Standards

```typescript
// infrastructure/kubernetes/pod-security.ts

interface PodSecurityPolicy {
  name: string;
  version: string;
  controls: {
    privileged: boolean;
    hostNetwork: boolean;
    hostPID: boolean;
    hostIPC: boolean;
    volumeTypes: string[];
    allowedHostPaths: string[];
    allowedCapabilities: string[];
    allowedFlexVolumes: string[];
    allowedUnsafeSysctls: string[];
    forbiddenSysctls: string[];
  };
}

export const baselinePolicy: PodSecurityPolicy = {
  name: 'baseline',
  version: 'v1.29',
  controls: {
    privileged: false,
    hostNetwork: false,
    hostPID: false,
    hostIPC: false,
    volumeTypes: ['configMap', 'downwardAPI', 'emptyDir', 'persistentVolumeClaim', 'projected', 'secret'],
    allowedHostPaths: [],
    allowedCapabilities: ['NET_BIND_SERVICE'],
    allowedFlexVolumes: [],
    allowedUnsafeSysctls: [],
    forbiddenSysctls: ['kernel.*', 'net.*', 'fs.*']
  }
};

export const restrictedPolicy: PodSecurityPolicy = {
  name: 'restricted',
  version: 'v1.29',
  controls: {
    privileged: false,
    hostNetwork: false,
    hostPID: false,
    hostIPC: false,
    volumeTypes: ['configMap', 'downwardAPI', 'emptyDir', 'persistentVolumeClaim', 'projected', 'secret'],
    allowedHostPaths: [],
    allowedCapabilities: [],
    allowedFlexVolumes: [],
    allowedUnsafeSysctls: [],
    forbiddenSysctls: ['kernel.*', 'net.*', 'fs.*']
  }
};

// Pod Security Admission configuration
export const podSecurityAdmission = {
  // Apply restricted policy to all namespaces by default
  defaults: {
    enforce: 'restricted',
    audit: 'restricted',
    warn: 'restricted'
  },
  // Exemptions for system namespaces
  exemptions: {
    namespaces: ['kube-system', 'monitoring', 'logging'],
    runtimeClasses: [],
    usernames: []
  }
};
```

### Network Policies

```typescript
// infrastructure/kubernetes/network-policy.ts

interface NetworkPolicyRule {
  from?: string[];
  to?: string[];
  ports?: { protocol: string; port: number }[];
}

export const defaultDenyPolicy = {
  apiVersion: 'networking.k8s.io/v1',
  kind: 'NetworkPolicy',
  metadata: {
    name: 'default-deny-all',
    namespace: 'default'
  },
  spec: {
    podSelector: {},
    policyTypes: ['Ingress', 'Egress']
  }
};

export const applicationNetworkPolicy = {
  apiVersion: 'networking.k8s.io/v1',
  kind: 'NetworkPolicy',
  metadata: {
    name: 'application-network-policy',
    namespace: 'production'
  },
  spec: {
    podSelector: {
      matchLabels: {
        app: 'travel-agency-api'
      }
    },
    policyTypes: ['Ingress', 'Egress'],
    ingress: [
      {
        from: [
          {
            namespaceSelector: {
              matchLabels: {
                name: 'ingress-nginx'
              }
            }
          }
        ],
        ports: [
          {
            protocol: 'TCP',
            port: 3000
          }
        ]
      }
    ],
    egress: [
      {
        to: [
          {
            namespaceSelector: {
              matchLabels: {
                name: 'kube-system'
              }
            },
            podSelector: {
              matchLabels: {
                k8s-app: 'kube-dns'
              }
            }
          }
        ],
        ports: [
          {
            protocol: 'UDP',
            port: 53
          }
        ]
      },
      {
        to: [
          {
            podSelector: {
              matchLabels: {
                app: 'postgres'
              }
            }
          }
        ],
        ports: [
          {
            protocol: 'TCP',
            port: 5432
          }
        ]
      },
      {
        to: [],
          ports: [
            {
              protocol: 'TCP',
              port: 443
            }
          ]
        }
      }
    ]
  }
};
```

### RBAC Configuration

```typescript
// infrastructure/kubernetes/rbac.ts

interface RoleRule {
  apiGroups: string[];
  resources: string[];
  verbs: string[];
  resourceNames?: string[];
}

export const applicationRole: RoleRule[] = [
  {
    apiGroups: [''],
    resources: ['configmaps', 'secrets'],
    verbs: ['get', 'list'],
    resourceNames: ['app-config', 'app-secrets']
  },
  {
    apiGroups: [''],
    resources: ['pods'],
    verbs: ['get', 'list']
  },
  {
    apiGroups: [''],
    resources: ['pods/log'],
    verbs: ['get']
  }
];

export const readOnlyRole: RoleRule[] = [
  {
    apiGroups: [''],
    resources: ['configmaps', 'endpoints', 'persistentvolumeclaims', 'pods', 'replicationcontrollers', 'replicasets', 'services', 'nodes'],
    verbs: ['get', 'list', 'watch']
  },
  {
    apiGroups: ['apps'],
    resources: ['daemonsets', 'deployments', 'replicasets', 'statefulsets'],
    verbs: ['get', 'list', 'watch']
  }
];

export const adminRole: RoleRule[] = [
  {
    apiGroups: ['*'],
    resources: ['*'],
    verbs: ['*']
  }
];

// ServiceAccount for application pods
export const applicationServiceAccount = {
  apiVersion: 'v1',
  kind: 'ServiceAccount',
  metadata: {
    name: 'travel-agency-api',
    namespace: 'production',
    annotations: {
      'eks.amazonaws.com/role-arn': 'arn:aws:iam::ACCOUNT_ID:role/travel-agency-api-role'
    }
  }
};
```

---

## Secrets Management

### Vault Integration

```typescript
// infrastructure/secrets/vault.ts

import Vault from 'node-vault';

interface VaultConfig {
  endpoint: string;
  namespace?: string;
  auth: {
    type: 'token' | 'kubernetes' | 'aws' | 'gcp';
    role: string;
  };
  mount: string;
}

export class SecretsManager {
  private client: Vault.client;
  private cache: Map<string, { value: any; expires: number }>;

  constructor(config: VaultConfig) {
    this.client = Vault({
      endpoint: config.endpoint,
      namespace: config.namespace
    });

    this.cache = new Map();
    this.authenticate(config.auth);
  }

  private async authenticate(auth: VaultConfig['auth']): Promise<void> {
    switch (auth.type) {
      case 'kubernetes':
        const jwt = await this.getKubernetesJWT();
        const result = await this.client.auth({
          type: 'kubernetes',
          role: auth.role,
          jwt
        });
        this.client.token = result.auth.client_token;
        break;

      case 'aws':
        const awsAuth = await this.client.auth({
          type: 'aws',
          role: auth.role
        });
        this.client.token = awsAuth.auth.client_token;
        break;

      case 'token':
        this.client.token = process.env.VAULT_TOKEN!;
        break;
    }
  }

  private async getKubernetesJWT(): Promise<string> {
    const fs = await import('fs/promises');
    return await fs.readFile('/var/run/secrets/kubernetes.io/serviceaccount/token', 'utf-8');
  }

  async getSecret(path: string, cacheTTL = 300): Promise<any> {
    const cached = this.cache.get(path);
    if (cached && cached.expires > Date.now()) {
      return cached.value;
    }

    const result = await this.client.read(`${this.client.mount}/data/${path}`);
    const secret = result.data.data;

    this.cache.set(path, {
      value: secret,
      expires: Date.now() + cacheTTL * 1000
    });

    return secret;
  }

  async getDatabaseCredentials(): Promise<{
    username: string;
    password: string;
    host: string;
    port: number;
    database: string;
  }> {
    return this.getSecret('database/production');
  }

  async getAPIKey(service: string): Promise<string> {
    const secret = await this.getSecret(`api-keys/${service}`);
    return secret.key;
  }

  async rotateSecret(path: string): Promise<void> {
    // Implement secret rotation logic
    const newSecret = this.generateSecret();
    await this.client.write(`${this.client.mount}/data/${path}`, {
      data: { value: newSecret }
    });

    // Invalidate cache
    this.cache.delete(path);

    // Trigger application reload
    await this.notifyRotation(path);
  }

  private generateSecret(): string {
    // Cryptographically secure random secret generation
    const crypto = require('crypto');
    return crypto.randomBytes(32).toString('base64');
  }

  private async notifyRotation(path: string): Promise<void> {
    // Publish to message bus for service reload
    // await messageBus.publish('secret.rotation', { path });
  }
}
```

### AWS Secrets Manager

```typescript
// infrastructure/secrets/aws-secrets.ts

import {
  SecretsManagerClient,
  GetSecretValueCommand,
  RotateSecretCommand,
  DescribeSecretCommand
} from '@aws-sdk/client-secrets-manager';

export class AWSSecretsManager {
  private client: SecretsManagerClient;
  private cache: Map<string, { value: any; version: string; expires: number }>;

  constructor() {
    this.client = new SecretsManagerClient({
      region: process.env.AWS_REGION
    });
    this.cache = new Map();
  }

  async getSecret(secretId: string, versionStage = 'AWSCURRENT'): Promise<any> {
    const cached = this.cache.get(secretId);
    if (cached && cached.expires > Date.now()) {
      return cached.value;
    }

    const command = new GetSecretValueCommand({
      SecretId: secretId,
      VersionStage: versionStage
    });

    const response = await this.client.send(command);

    let secret: any;
    if (response.SecretString) {
      secret = JSON.parse(response.SecretString);
    } else if (response.SecretBinary) {
      secret = Buffer.from(response.SecretBinary).toString('utf-8');
    }

    this.cache.set(secretId, {
      value: secret,
      version: response.VersionId!,
      expires: Date.now() + 300000 // 5 minute cache
    });

    return secret;
  }

  async getDatabaseCredentials(secretId: string): Promise<{
    username: string;
    password: string;
    host: string;
    port: number;
    dbname: string;
  }> {
    return this.getSecret(secretId);
  }

  async rotateSecret(secretId: string): Promise<void> {
    const command = new RotateSecretCommand({
      SecretId: secretId
    });

    await this.client.send(command);

    // Invalidate cache
    this.cache.delete(secretId);
  }

  async checkRotationNeeded(secretId: string): Promise<boolean> {
    const command = new DescribeSecretCommand({
      SecretId: secretId
    });

    const response = await this.client.send(command);

    if (!response.RotationEnabled) {
      return false;
    }

    const lastRotated = response.LastChangedDate?.getTime() || 0;
    const rotationDays = 90;
    const rotationInterval = rotationDays * 24 * 60 * 60 * 1000;

    return Date.now() - lastRotated > rotationInterval;
  }
}
```

### Secret Rotation

```typescript
// infrastructure/secrets/rotation.ts

interface RotationConfig {
  secretId: string;
  rotationIntervalDays: number;
  rotationLambdaARN: string;
}

export class SecretRotator {
  private configs: Map<string, RotationConfig>;

  constructor() {
    this.configs = new Map();
  }

  registerSecret(config: RotationConfig): void {
    this.configs.set(config.secretId, config);
  }

  async rotateSecret(secretId: string): Promise<void> {
    const config = this.configs.get(secretId);
    if (!config) {
      throw new Error(`No rotation config for secret: ${secretId}`);
    }

    // 1. Generate new secret value
    const newValue = await this.generateNewValue(secretId);

    // 2. Update secret in target system
    await this.updateTargetSystem(secretId, newValue);

    // 3. Test new secret
    await this.testNewSecret(secretId, newValue);

    // 4. Update secret manager
    await this.updateSecretManager(secretId, newValue);

    // 5. Notify applications
    await this.notifyApplications(secretId);

    // 6. Revoke old secret after grace period
    setTimeout(() => this.revokeOldSecret(secretId), 3600000); // 1 hour
  }

  private async generateNewValue(secretId: string): Promise<string> {
    const crypto = require('crypto');
    return crypto.randomBytes(32).toString('base64');
  }

  private async updateTargetSystem(secretId: string, newValue: string): Promise<void> {
    // Implementation depends on target system
    // Example: Update database password, API key, etc.
  }

  private async testNewSecret(secretId: string, newValue: string): Promise<void> {
    // Verify new secret works
  }

  private async updateSecretManager(secretId: string, newValue: string): Promise<void> {
    // Update secret in Vault/AWS Secrets Manager
  }

  private async notifyApplications(secretId: string): Promise<void> {
    // Notify applications to reload credentials
  }

  private async revokeOldSecret(secretId: string): Promise<void> {
    // Revoke old secret version
  }
}
```

---

## IAM & Least Privilege

### IAM Policies

```typescript
// infrastructure/iam/policies.ts

interface IAMPolicyStatement {
  Effect: 'Allow' | 'Deny';
  Action: string | string[];
  Resource: string | string[];
  Condition?: Record<string, any>;
}

interface IAMPolicy {
  Version: string;
  Statement: IAMPolicyStatement[];
}

export const applicationBasePolicy: IAMPolicy = {
  Version: '2012-10-17',
  Statement: [
    {
      Effect: 'Allow',
      Action: [
        'secretsmanager:GetSecretValue',
        'secretsmanager:DescribeSecret'
      ],
      Resource: [
        'arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:travel-agency/*'
      ]
    },
    {
      Effect: 'Allow',
      Action: [
        'kms:Decrypt'
      ],
      Resource: [
        'arn:aws:kms:us-east-1:ACCOUNT_ID:key/KEY_ID'
      ]
    },
    {
      Effect: 'Allow',
      Action: [
        'ssm:GetParameter',
        'ssm:GetParameters'
      ],
      Resource: [
        'arn:aws:ssm:us-east-1:ACCOUNT_ID:parameter/travel-agency/*'
      ]
    }
  ]
};

export const databaseAccessPolicy: IAMPolicy = {
  Version: '2012-10-17',
  Statement: [
    {
      Effect: 'Allow',
      Action: [
        'rds-db:connect'
      ],
      Resource: [
        'arn:aws:rds-db:us-east-1:ACCOUNT_ID:dbuser:DB_ID/app_user'
      ]
    }
  ]
};

export const s3AccessPolicy: IAMPolicy = {
  Version: '2012-10-17',
  Statement: [
    {
      Effect: 'Allow',
      Action: [
        's3:GetObject',
        's3:PutObject',
        's3:DeleteObject'
      ],
      Resource: [
        'arn:aws:s3:::travel-agency-documents/*',
        'arn:aws:s3:::travel-agency-uploads/*'
      ]
    },
    {
      Effect: 'Allow',
      Action: [
        's3:ListBucket'
      ],
      Resource: [
        'arn:aws:s3:::travel-agency-documents',
        'arn:aws:s3:::travel-agency-uploads'
      ]
    }
  ]
};

export const sqsAccessPolicy: IAMPolicy = {
  Version: '2012-10-17',
  Statement: [
    {
      Effect: 'Allow',
      Action: [
        'sqs:SendMessage',
        'sqs:ReceiveMessage',
        'sqs:DeleteMessage',
        'sqs:GetQueueAttributes'
      ],
      Resource: [
        'arn:aws:sqs:us-east-1:ACCOUNT_ID:trip-processing-queue',
        'arn:aws:sqs:us-east-1:ACCOUNT_ID:email-sending-queue'
      ]
    }
  ]
};
```

### Role Assumption

```typescript
// infrastructure/iam/role-assumption.ts

interface AssumeRoleConfig {
  roleArn: string;
  sessionName: string;
  durationSeconds: number;
  policy?: string;
}

export class IAMRoleManager {
  private sts: any;

  constructor() {
    const { STSClient } = require('@aws-sdk/client-sts');
    this.sts = new STSClient({ region: process.env.AWS_REGION });
  }

  async assumeRole(config: AssumeRoleConfig): Promise<{
    accessKeyId: string;
    secretAccessKey: string;
    sessionToken: string;
    expiration: Date;
  }> {
    const { AssumeRoleCommand } = require('@aws-sdk/client-sts');

    const command = new AssumeRoleCommand({
      RoleArn: config.roleArn,
      RoleSessionName: config.sessionName,
      DurationSeconds: config.durationSeconds,
      Policy: config.policy
    });

    const response = await this.sts.send(command);

    return {
      accessKeyId: response.Credentials.AccessKeyId,
      secretAccessKey: response.Credentials.SecretAccessKey,
      sessionToken: response.Credentials.SessionToken,
      expiration: response.Credentials.Expiration
    };
  }

  async assumeReadOnlyRole(accountId: string): Promise<any> {
    return this.assumeRole({
      roleArn: `arn:aws:iam::${accountId}:role/ReadOnly`,
      sessionName: 'travel-agency-api',
      durationSeconds: 900, // 15 minutes
      policy: JSON.stringify({
        Version: '2012-10-17',
        Statement: [
          {
            Effect: 'Allow',
            Action: ['s3:GetObject', 's3:ListBucket'],
            Resource: '*'
          }
        ]
      })
    });
  }
}
```

---

## Security Monitoring

### CloudTrail Logging

```typescript
// infrastructure/monitoring/cloudtrail.ts

interface CloudTrailConfig {
  trailName: string;
  s3Bucket: string;
  includeGlobalServices: boolean;
  isMultiRegion: boolean;
  enableLogFileValidation: boolean;
  kmsKeyId: string;
  cloudWatchLogsLogGroup: string;
  cloudWatchLogsRoleArn: string;
}

export const productionTrail: CloudTrailConfig = {
  trailName: 'travel-agency-production',
  s3Bucket: 'travel-agency-cloudtrail-logs',
  includeGlobalServices: true,
  isMultiRegion: true,
  enableLogFileValidation: true,
  kmsKeyId: 'arn:aws:kms:us-east-1:ACCOUNT_ID:key/KEY_ID',
  cloudWatchLogsLogGroup: '/aws/cloudtrail/production',
  cloudWatchLogsRoleArn: 'arn:aws:iam::ACCOUNT_ID:role/CloudTrailLogsRole'
};

// Critical events to monitor
export const criticalEvents = [
  // IAM events
  'CreateUser',
  'DeleteUser',
  'AttachUserPolicy',
  'DetachUserPolicy',
  'CreateAccessKey',
  'DeleteAccessKey',
  'CreateRole',
  'DeleteRole',
  'AttachRolePolicy',
  'DetachRolePolicy',

  // S3 events
  'DeleteBucket',
  'PutBucketPolicy',
  'DeleteBucketPolicy',
  'PutBucketAcl',
  'PutObjectAcl',

  // EC2 events
  'RunInstances',
  'TerminateInstances',
  'CreateSecurityGroup',
  'DeleteSecurityGroup',
  'AuthorizeSecurityGroupIngress',
  'RevokeSecurityGroupIngress',

  // RDS events
  'CreateDBInstance',
  'DeleteDBInstance',
  'ModifyDBInstance',
  'RestoreDBInstanceFromDBSnapshot',

  // Secrets Manager
  'CreateSecret',
  'DeleteSecret',
  'RotateSecret',
  'PutSecretValue'
];
```

### CloudWatch Alarms

```typescript
// infrastructure/monitoring/cloudwatch-alarms.ts

interface CloudWatchAlarm {
  alarmName: string;
  metricName: string;
  namespace: string;
  statistic: 'Average' | 'Sum' | 'Minimum' | 'Maximum' | 'SampleCount';
  period: number;
  evaluationPeriods: number;
  threshold: number;
  comparisonOperator: 'GreaterThanThreshold' | 'LessThanThreshold' | 'GreaterThanOrEqualToThreshold';
  treatMissingData: 'breaching' | 'notBreaching' | 'ignore' | 'missing';
}

export const securityAlarms: CloudWatchAlarm[] = [
  {
    alarmName: 'Security-FailedAuthenticationAttempts',
    metricName: 'FailedAuthenticationAttempts',
    namespace: 'TravelAgency/Security',
    statistic: 'Sum',
    period: 300,
    evaluationPeriods: 1,
    threshold: 100,
    comparisonOperator: 'GreaterThanThreshold',
    treatMissingData: 'notBreaching'
  },
  {
    alarmName: 'Security-SuspiciousAPIActivity',
    metricName: 'SuspiciousAPIRequests',
    namespace: 'TravelAgency/Security',
    statistic: 'Sum',
    period: 300,
    evaluationPeriods: 1,
    threshold: 50,
    comparisonOperator: 'GreaterThanThreshold',
    treatMissingData: 'notBreaching'
  },
  {
    alarmName: 'Security-UnusualDataEgress',
    metricName: 'DataEgressBytes',
    namespace: 'AWS/EC2',
    statistic: 'Sum',
    period: 300,
    evaluationPeriods: 3,
    threshold: 10737418240, // 10GB
    comparisonOperator: 'GreaterThanThreshold',
    treatMissingData: 'notBreaching'
  },
  {
    alarmName: 'Security-VulnerabilityScanFailed',
    metricName: 'VulnerabilityScanStatus',
    namespace: 'TravelAgency/Security',
    statistic: 'Minimum',
    period: 86400, // Daily
    evaluationPeriods: 1,
    threshold: 1,
    comparisonOperator: 'LessThanThreshold',
    treatMissingData: 'breaching'
  },
  {
    alarmName: 'Security-UnauthorizedAccessAttempt',
    metricName: 'AccessDeniedCount',
    namespace: 'AWS/CloudTrail',
    statistic: 'Sum',
    period: 300,
    evaluationPeriods: 1,
    threshold: 10,
    comparisonOperator: 'GreaterThanThreshold',
    treatMissingData: 'notBreaching'
  }
];
```

### Security Metrics

```typescript
// infrastructure/monitoring/metrics.ts

interface SecurityMetric {
  name: string;
  type: 'counter' | 'gauge' | 'histogram';
  description: string;
  labels: string[];
}

export const securityMetrics: SecurityMetric[] = [
  {
    name: 'authentication_attempts_total',
    type: 'counter',
    description: 'Total number of authentication attempts',
    labels: ['method', 'status']
  },
  {
    name: 'authorization_failures_total',
    type: 'counter',
    description: 'Total number of authorization failures',
    labels: ['resource', 'action']
  },
  {
    name: 'security_events_total',
    type: 'counter',
    description: 'Total number of security events',
    labels: ['severity', 'type']
  },
  {
    name: 'vulnerability_scan_duration_seconds',
    type: 'histogram',
    description: 'Duration of vulnerability scans',
    labels: ['image']
  },
  {
    name: 'secret_rotation_age_seconds',
    type: 'gauge',
    description: 'Age of current secret version',
    labels: ['secret_id']
  },
  {
    name: 'tls_handshake_duration_seconds',
    type: 'histogram',
    description: 'Duration of TLS handshakes',
    labels: ['version', 'cipher']
  },
  {
    name: 'rate_limit_violations_total',
    type: 'counter',
    description: 'Total number of rate limit violations',
    labels: ['user_id', 'endpoint']
  }
];
```

---

## Intrusion Detection

### Anomaly Detection

```typescript
// infrastructure/detection/anomaly.ts

interface AnomalyDetectorConfig {
  baselineWindow: number; // minutes
  threshold: number; // standard deviations
  minSampleSize: number;
}

export class AnomalyDetector {
  private config: AnomalyDetectorConfig;
  private baselines: Map<string, number[]> = new Map();

  constructor(config: AnomalyDetectorConfig) {
    this.config = config;
  }

  async evaluate(metric: string, value: number): Promise<{
    isAnomaly: boolean;
    score: number;
    threshold: number;
  }> {
    const baseline = this.baselines.get(metric) || [];

    if (baseline.length < this.config.minSampleSize) {
      this.updateBaseline(metric, value);
      return { isAnomaly: false, score: 0, threshold: 0 };
    }

    const mean = this.calculateMean(baseline);
    const stdDev = this.calculateStdDev(baseline, mean);
    const zScore = Math.abs((value - mean) / stdDev);

    const isAnomaly = zScore > this.config.threshold;

    if (isAnomaly) {
      await this.alertAnomaly(metric, value, mean, stdDev, zScore);
    }

    this.updateBaseline(metric, value);

    return {
      isAnomaly,
      score: zScore,
      threshold: this.config.threshold
    };
  }

  private calculateMean(values: number[]): number {
    return values.reduce((a, b) => a + b, 0) / values.length;
  }

  private calculateStdDev(values: number[], mean: number): number {
    const squaredDiffs = values.map(v => Math.pow(v - mean, 2));
    return Math.sqrt(this.calculateMean(squaredDiffs));
  }

  private updateBaseline(metric: string, value: number): void {
    const baseline = this.baselines.get(metric) || [];
    baseline.push(value);

    // Keep only the baseline window size
    if (baseline.length > this.config.baselineWindow) {
      baseline.shift();
    }

    this.baselines.set(metric, baseline);
  }

  private async alertAnomaly(
    metric: string,
    value: number,
    mean: number,
    stdDev: number,
    zScore: number
  ): Promise<void> {
    // Send alert to security team
    console.error(`Anomaly detected: ${metric}`, {
      value,
      mean,
      stdDev,
      zScore
    });
  }
}
```

### Signature Detection

```typescript
// infrastructure/detection/signature.ts

interface Signature {
  id: string;
  name: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  category: string;
  pattern: RegExp | ((event: any) => boolean);
  description: string;
  mitigation?: string;
}

export const securitySignatures: Signature[] = [
  {
    id: 'SIG-001',
    name: 'SQL Injection Attempt',
    severity: 'critical',
    category: 'injection',
    pattern: /('|(\-\-)|(\;)|(\b(or|and)\b.*=.*)|(exec(\s|\+)+(s|x)p\w+)/i,
    description: 'Detects common SQL injection patterns',
    mitigation: 'Block IP and sanitize input'
  },
  {
    id: 'SIG-002',
    name: 'XSS Attempt',
    severity: 'high',
    category: 'xss',
    pattern: /<script|javascript:|onerror\s*=|onload\s*=/i,
    description: 'Detects cross-site scripting attempts',
    mitigation: 'Encode output and validate input'
  },
  {
    id: 'SIG-003',
    name: 'Path Traversal',
    severity: 'high',
    category: 'file',
    pattern: /\.\.[\/\\]/,
    description: 'Detects directory traversal attempts',
    mitigation: 'Validate file paths and use chroot'
  },
  {
    id: 'SIG-004',
    name: 'Command Injection',
    severity: 'critical',
    category: 'injection',
    pattern: /[;&|`$()]/,
    description: 'Detects command injection attempts',
    mitigation: 'Use parameterized queries'
  },
  {
    id: 'SIG-005',
    name: 'SSRF Attempt',
    severity: 'high',
    category: 'ssrf',
    pattern: /http(s)?:\/\/(localhost|127\.0\.0\.1|0\.0\.0\.0|169\.254|::1)/i,
    description: 'Detects server-side request forgery attempts',
    mitigation: 'Validate and whitelist URLs'
  }
];

export class SignatureEngine {
  private signatures: Signature[];

  constructor(signatures: Signature[]) {
    this.signatures = signatures;
  }

  evaluate(event: any): {
    matched: Signature[];
    highestSeverity: 'low' | 'medium' | 'high' | 'critical' | null;
  } {
    const matched: Signature[] = [];

    for (const signature of this.signatures) {
      if (this.matchSignature(signature, event)) {
        matched.push(signature);
      }
    }

    const severityOrder = ['critical', 'high', 'medium', 'low'];
    let highestSeverity: any = null;

    for (const severity of severityOrder) {
      if (matched.some(m => m.severity === severity)) {
        highestSeverity = severity;
        break;
      }
    }

    return { matched, highestSeverity };
  }

  private matchSignature(signature: Signature, event: any): boolean {
    if (signature.pattern instanceof RegExp) {
      const payload = JSON.stringify(event);
      return signature.pattern.test(payload);
    } else if (typeof signature.pattern === 'function') {
      return signature.pattern(event);
    }
    return false;
  }
}
```

---

## Vulnerability Management

### Vulnerability Scanning

```typescript
// infrastructure/vulnerability/scanner.ts

interface VulnerabilityScanConfig {
  targets: string[];
  scanTypes: ('network' | 'container' | 'code' | 'dependency')[];
  schedule: string; // cron expression
  severityThreshold: 'low' | 'medium' | 'high' | 'critical';
}

export class VulnerabilityScanner {
  async scanContainers(images: string[]): Promise<VulnerabilityReport> {
    const results = await Promise.all(
      images.map(img => this.scanImage(img))
    );

    return this.aggregateResults(results);
  }

  async scanNetwork(cidr: string): Promise<NetworkVulnerabilityReport> {
    // Network vulnerability scanning
    return {
      scanTime: new Date(),
      targets: [],
      vulnerabilities: [],
      summary: {
        critical: 0,
        high: 0,
        medium: 0,
        low: 0
      }
    };
  }

  async scanDependencies(path: string): Promise<DependencyVulnerabilityReport> {
    // Dependency scanning with OSV, Snyk, or similar
    return {
      scanTime: new Date(),
      path,
      dependencies: [],
      vulnerabilities: [],
      summary: {
        total: 0,
        fixable: 0,
        critical: 0,
        high: 0,
        medium: 0,
        low: 0
      }
    };
  }

  private async scanImage(image: string): Promise<ImageVulnerabilityReport> {
    // Container image scanning with Trivy
    return {
      image,
      scanTime: new Date(),
      vulnerabilities: [],
      summary: {
        critical: 0,
        high: 0,
        medium: 0,
        low: 0
      }
    };
  }

  private aggregateResults(results: ImageVulnerabilityReport[]): VulnerabilityReport {
    return {
      scanTime: new Date(),
      targets: results.map(r => r.image),
      vulnerabilities: results.flatMap(r => r.vulnerabilities),
      summary: results.reduce(
        (acc, r) => ({
          critical: acc.critical + r.summary.critical,
          high: acc.high + r.summary.high,
          medium: acc.medium + r.summary.medium,
          low: acc.low + r.summary.low
        }),
        { critical: 0, high: 0, medium: 0, low: 0 }
      )
    };
  }
}

interface VulnerabilityReport {
  scanTime: Date;
  targets: string[];
  vulnerabilities: any[];
  summary: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
}

interface ImageVulnerabilityReport extends VulnerabilityReport {
  image: string;
}

interface NetworkVulnerabilityReport extends VulnerabilityReport {
  targets: string[];
}

interface DependencyVulnerabilityReport {
  scanTime: Date;
  path: string;
  dependencies: any[];
  vulnerabilities: any[];
  summary: {
    total: number;
    fixable: number;
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
}
```

---

## Incident Response

### Incident Response Playbook

```typescript
// infrastructure/incidents/playbook.ts

interface Incident {
  id: string;
  severity: 'P1' | 'P2' | 'P3' | 'P4';
  type: string;
  status: 'detected' | 'investigating' | 'mitigating' | 'resolved';
  detectedAt: Date;
  assignedTo?: string;
  timeline: IncidentEvent[];
  metadata: Record<string, any>;
}

interface IncidentEvent {
  timestamp: Date;
  phase: 'detection' | 'containment' | 'eradication' | 'recovery' | 'lessons-learned';
  action: string;
  actor: string;
  details: string;
}

export class IncidentResponder {
  async handleIncident(incident: Incident): Promise<void> {
    switch (incident.severity) {
      case 'P1':
        await this.handleP1(incident);
        break;
      case 'P2':
        await this.handleP2(incident);
        break;
      case 'P3':
        await this.handleP3(incident);
        break;
      default:
        await this.handleP4(incident);
    }
  }

  private async handleP1(incident: Incident): Promise<void> {
    // P1: Critical - Immediate response required
    await this.executePlaybook(incident, [
      { phase: 'containment', action: 'isolate_affected_systems' },
      { phase: 'containment', action: 'preserve_evidence' },
      { phase: 'containment', action: 'notify_executives' },
      { phase: 'eradication', action: 'identify_root_cause' },
      { phase: 'eradication', action: 'remove_threat' },
      { phase: 'recovery', action: 'restore_services' },
      { phase: 'recovery', action: 'monitor_for_recurrence' },
      { phase: 'lessons-learned', action: 'document_incident' }
    ]);
  }

  private async handleP2(incident: Incident): Promise<void> {
    // P2: High - Response within 1 hour
    await this.executePlaybook(incident, [
      { phase: 'containment', action: 'limit_impact' },
      { phase: 'containment', action: 'preserve_evidence' },
      { phase: 'eradication', action: 'identify_root_cause' },
      { phase: 'eradication', action: 'remove_threat' },
      { phase: 'recovery', action: 'restore_services' },
      { phase: 'lessons-learned', action: 'document_incident' }
    ]);
  }

  private async handleP3(incident: Incident): Promise<void> {
    // P3: Medium - Response within 4 hours
    await this.executePlaybook(incident, [
      { phase: 'containment', action: 'assess_impact' },
      { phase: 'eradication', action: 'identify_root_cause' },
      { phase: 'eradication', action: 'remove_threat' },
      { phase: 'recovery', action: 'restore_services' }
    ]);
  }

  private async handleP4(incident: Incident): Promise<void> {
    // P4: Low - Response within 24 hours
    await this.executePlaybook(incident, [
      { phase: 'eradication', action: 'investigate' },
      { phase: 'recovery', action: 'apply_fix' }
    ]);
  }

  private async executePlaybook(
    incident: Incident,
    actions: { phase: string; action: string }[]
  ): Promise<void> {
    for (const step of actions) {
      await this.executeStep(incident, step.phase, step.action);
    }
  }

  private async executeStep(
    incident: Incident,
    phase: string,
    action: string
  ): Promise<void> {
    // Execute the incident response step
    console.log(`[${phase}] ${action}: ${incident.id}`);

    // Add to timeline
    incident.timeline.push({
      timestamp: new Date(),
      phase: phase as any,
      action,
      actor: 'system',
      details: `Executed ${action} for incident ${incident.id}`
    });
  }
}
```

### Communication Templates

```typescript
// infrastructure/incidents/communication.ts

interface CommunicationTemplate {
  severity: string;
  channels: ('slack' | 'email' | 'sms' | 'pagerduty')[];
  template: string;
  recipients: string[];
}

export const incidentTemplates: Record<string, CommunicationTemplate> = {
  'P1-data-breach': {
    severity: 'P1',
    channels: ['slack', 'email', 'sms', 'pagerduty'],
    template: `
🚨 CRITICAL INCIDENT: Data Breach Detected

Incident ID: {{incidentId}}
Detected: {{detectedAt}}
Severity: P1 - Critical

Description:
{{description}}

Immediate Actions Required:
1. Preserve evidence
2. Isolate affected systems
3. Notify legal/compliance
4. Initiate customer communication plan

Incident Commander: {{commander}}
Status Page: {{statusPage}}
    `,
    recipients: ['security-team', 'executives', 'legal', 'pr']
  },

  'P2-service-disruption': {
    severity: 'P2',
    channels: ['slack', 'email', 'pagerduty'],
    template: `
⚠️ HIGH SEVERITY: Service Disruption

Incident ID: {{incidentId}}
Detected: {{detectedAt}}
Severity: P2 - High

Description:
{{description}}

Affected Services:
{{affectedServices}}

Current Status: {{status}}
Estimated Resolution: {{eta}}

Next Update: {{nextUpdate}}
    `,
    recipients: ['engineering', 'support']
  },

  'P3-security-event': {
    severity: 'P3',
    channels: ['slack', 'email'],
    template: `
🔒 Security Event Detected

Incident ID: {{incidentId}}
Detected: {{detectedAt}}
Severity: P3 - Medium

Description:
{{description}}

Actions Taken:
{{actions}}

No immediate customer impact expected.
    `,
    recipients: ['security-team', 'engineering-lead']
  }
};
```

---

## API Specification

### Infrastructure Security API

```typescript
// api/infrastructure-security/routes.ts

import { z } from 'zod';

// Schemas
const ScanRequestSchema = z.object({
  type: z.enum(['container', 'network', 'dependency']),
  target: z.string()
});

const ScanResultSchema = z.object({
  scanId: z.string(),
  status: z.enum(['pending', 'running', 'completed', 'failed']),
  startedAt: z.date(),
  completedAt: z.date().optional(),
  vulnerabilities: z.array(z.object({
    id: z.string(),
    severity: z.enum(['critical', 'high', 'medium', 'low']),
    description: z.string(),
    affected: z.string(),
    fix: z.string().optional()
  })),
  summary: z.object({
    critical: z.number(),
    high: z.number(),
    medium: z.number(),
    low: z.number()
  })
});

const IncidentRequestSchema = z.object({
  severity: z.enum(['P1', 'P2', 'P3', 'P4']),
  type: z.string(),
  description: z.string(),
  metadata: z.record(z.any()).optional()
});

const IncidentResponseSchema = z.object({
  id: z.string(),
  severity: z.enum(['P1', 'P2', 'P3', 'P4']),
  type: z.string(),
  status: z.enum(['detected', 'investigating', 'mitigating', 'resolved']),
  detectedAt: z.date(),
  assignedTo: z.string().optional(),
  timeline: z.array(z.object({
    timestamp: z.date(),
    phase: z.string(),
    action: z.string(),
    actor: z.string(),
    details: z.string()
  }))
});

const SecurityMetricsSchema = z.object({
  timestamp: z.date(),
  authenticationAttempts: z.number(),
  authorizationFailures: z.number(),
  securityEvents: z.number(),
  vulnerabilityScanDuration: z.number(),
  secretAge: z.number(),
  tlsHandshakeDuration: z.number(),
  rateLimitViolations: z.number()
});

// Routes
export const infrastructureSecurityRoutes = {
  // Vulnerability Scanning
  'POST /api/security/scan': {
    summary: 'Initiate security scan',
    request: ScanRequestSchema,
    response: z.object({ scanId: z.string() })
  },

  'GET /api/security/scan/:scanId': {
    summary: 'Get scan results',
    response: ScanResultSchema
  },

  'GET /api/security/vulnerabilities': {
    summary: 'List all vulnerabilities',
    query: z.object({
      severity: z.enum(['critical', 'high', 'medium', 'low']).optional(),
      status: z.enum(['open', 'fixed', 'ignored']).optional(),
      limit: z.number().default(50)
    }),
    response: z.array(z.object({
      id: z.string(),
      severity: z.enum(['critical', 'high', 'medium', 'low']),
      status: z.enum(['open', 'fixed', 'ignored']),
      description: z.string(),
      affected: z.string(),
      detectedAt: z.date()
    }))
  },

  // Incident Management
  'POST /api/security/incidents': {
    summary: 'Create new incident',
    request: IncidentRequestSchema,
    response: IncidentResponseSchema
  },

  'GET /api/security/incidents/:incidentId': {
    summary: 'Get incident details',
    response: IncidentResponseSchema
  },

  'PUT /api/security/incidents/:incidentId': {
    summary: 'Update incident',
    request: z.object({
      status: z.enum(['investigating', 'mitigating', 'resolved']).optional(),
      assignedTo: z.string().optional(),
      notes: z.string().optional()
    }),
    response: IncidentResponseSchema
  },

  // Security Metrics
  'GET /api/security/metrics': {
    summary: 'Get security metrics',
    query: z.object({
      from: z.string().datetime(),
      to: z.string().datetime(),
      granularity: z.enum(['minute', 'hour', 'day']).default('hour')
    }),
    response: z.array(SecurityMetricsSchema)
  },

  // Secrets Management
  'POST /api/security/secrets/rotate': {
    summary: 'Rotate secret',
    request: z.object({
      secretId: z.string(),
      force: z.boolean().default(false)
    }),
    response: z.object({
      secretId: z.string(),
      rotationId: z.string(),
      status: z.enum(['pending', 'in-progress', 'completed', 'failed'])
    })
  },

  'GET /api/security/secrets/rotation-status': {
    summary: 'Get secret rotation status',
    query: z.object({
      secretId: z.string()
    }),
    response: z.object({
      secretId: z.string(),
      lastRotated: z.date(),
      nextRotation: z.date(),
      status: z.enum(['current', 'pending', 'overdue'])
    })
  }
};
```

---

## Testing Scenarios

### Infrastructure Security Tests

```typescript
// tests/infrastructure-security/scenarios.ts

interface TestScenario {
  name: string;
  description: string;
  setup: () => Promise<void>;
  execute: () => Promise<void>;
  verify: () => Promise<void>;
  cleanup: () => Promise<void>;
}

export const infrastructureSecurityTests: TestScenario[] = [
  {
    name: 'Network Segmentation',
    description: 'Verify proper network segmentation',
    setup: async () => {
      // Deploy test resources in different subnets
    },
    execute: async () => {
      // Attempt to connect from public to private subnet (should fail)
      // Attempt to connect from private to database subnet (should work)
    },
    verify: async () => {
      // Verify security group rules are enforced
    },
    cleanup: async () => {
      // Remove test resources
    }
  },

  {
    name: 'Container Image Scanning',
    description: 'Verify container images are scanned before deployment',
    setup: async () => {
      // Build a test container image
    },
    execute: async () => {
      // Attempt to deploy image with vulnerabilities (should fail)
      // Deploy clean image (should succeed)
    },
    verify: async () => {
      // Verify scan results are stored
    },
    cleanup: async () => {
      // Remove test images
    }
  },

  {
    name: 'Secret Rotation',
    description: 'Verify secret rotation works correctly',
    setup: async () => {
      // Create a test secret
    },
    execute: async () => {
      // Trigger secret rotation
      // Verify applications can still authenticate
    },
    verify: async () => {
      // Verify new secret version is active
      // Verify old secret is revoked
    },
    cleanup: async () => {
      // Delete test secret
    }
  },

  {
    name: 'IAM Least Privilege',
    description: 'Verify IAM roles follow least privilege',
    setup: async () => {
      // Create test IAM role
    },
    execute: async () => {
      // Attempt to access allowed resources (should succeed)
      // Attempt to access denied resources (should fail)
    },
    verify: async () => {
      // Verify CloudTrail logs show correct denials
    },
    cleanup: async () => {
      // Delete test role
    }
  },

  {
    name: 'WAF Rules',
    description: 'Verify WAF blocks malicious traffic',
    setup: async () => {
      // Configure test endpoints
    },
    execute: async () => {
      // Send SQL injection attempts (should be blocked)
      // Send XSS attempts (should be blocked)
      // Send rate-limited requests (should be throttled)
    },
    verify: async () => {
      // Verify WAF logs show blocked requests
    },
    cleanup: async () => {
      // Remove test endpoints
    }
  },

  {
    name: 'Incident Response',
    description: 'Verify incident response playbook',
    setup: async () => {
      // Configure test monitoring
    },
    execute: async () => {
      // Trigger security alert
      // Verify incident is created
      // Verify notifications are sent
    },
    verify: async () => {
      // Verify incident timeline is updated
    },
    cleanup: async () => {
      // Close test incident
    }
  },

  {
    name: 'Encryption at Rest',
    description: 'Verify all data is encrypted at rest',
    setup: async () => {
      // Create test resources
    },
    execute: async () => {
      // Verify EBS volumes are encrypted
      // Verify S3 buckets have encryption enabled
      // Verify RDS instances are encrypted
    },
    verify: async () => {
      // Verify KMS keys are used
    },
    cleanup: async () => {
      // Remove test resources
    }
  },

  {
    name: 'TLS Configuration',
    description: 'Verify proper TLS configuration',
    setup: async () => {
      // Configure test endpoints
    },
    execute: async () => {
      // Scan with testssl.sh or similar
      // Verify TLS 1.2/1.3 only
      // Verify strong cipher suites
      // Verify certificate validity
    },
    verify: async () => {
      // Verify no weak configurations
    },
    cleanup: async () => {
      // Remove test endpoints
    }
  }
];
```

---

## Metrics & Monitoring

### Infrastructure Security KPIs

| Metric | Description | Target | Alert Threshold |
|--------|-------------|--------|-----------------|
| **Vulnerability Scan Coverage** | % of images scanned before deploy | 100% | < 100% |
| **Critical Vulnerability MTTR** | Mean time to remediate critical vulns | < 24 hours | > 48 hours |
| **Secret Age** | Days since last secret rotation | < 90 days | > 85 days |
| **Incident Response Time** | Time to acknowledge P1 incidents | < 15 min | > 30 min |
| **Failed Authentication Rate** | % of failed auth attempts | < 1% | > 5% |
| **Security Baseline Drift** | % of resources compliant with baseline | 100% | < 95% |
| **TLS Compliance** | % of endpoints with valid TLS | 100% | < 100% |
| **Encryption Coverage** | % of storage encrypted | 100% | < 100% |

### Dashboard Queries

```promql
# Vulnerability scan success rate
rate(vulnerability_scan_success_total[5m]) / rate(vulnerability_scan_total[5m])

# Secret rotation status
secret_rotation_age_seconds / (90 * 24 * 3600)

# Failed authentication rate
rate(authentication_failures_total[5m]) / rate(authentication_attempts_total[5m])

# WAF blocked requests
rate(waf_blocked_requests_total[5m])

# Incident response time
time() - incident_detected_timestamp{severity="P1"}

# TLS handshake failures
rate(tls_handshake_failures_total[5m]) / rate(tls_handshake_total[5m])
```

---

**Document Version:** 1.0

**Last Updated:** 2026-04-26

**Related Documents:**
- [SECURITY_01_APPLICATION_SECURITY.md](./SECURITY_01_APPLICATION_SECURITY.md)
- [SECURITY_02_API_SECURITY.md](./SECURITY_02_API_SECURITY.md)
- [SECURITY_03_DATA_SECURITY.md](./SECURITY_03_DATA_SECURITY.md)
- [SECURITY_HARDENING_MASTER_INDEX.md](./SECURITY_HARDENING_MASTER_INDEX.md)
