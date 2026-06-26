---
name: domos-remote-deploy
description: Deploy DomOS to a remote machine with Docker and ngrok. Use when the user asks to deploy DomOS to a remote server, set up production deployment, expose DomOS externally via ngrok, or deploy the cashier application to a VPS/cloud/home server.
---

# DomOS Remote Deployment

This skill provides step-by-step instructions for deploying DomOS MVP1-Cashier to a remote Linux machine using Docker and exposing it via ngrok.

## Prerequisites

- Remote machine with SSH access
- Ubuntu/Debian-based Linux (tested on Linux Mint 22.2)
- At least 2GB RAM and 10GB free disk space
- ngrok account with auth token (store as `NGROK_TOKEN` in secrets)
- GitHub PAT with repo access (store as `GIT_PAT` in secrets)

## Deployment Steps

### 1. Connect to Remote Machine

Verify SSH connectivity:

```bash
sshpass -p 'PASSWORD' ssh -o StrictHostKeyChecking=no USER@IP_ADDRESS 'uname -a && cat /etc/os-release | head -3'
```

### 2. Install Docker

Install prerequisites:

```bash
sshpass -p 'PASSWORD' ssh USER@IP 'echo "PASSWORD" | sudo -S apt-get update -qq && echo "PASSWORD" | sudo -S apt-get install -y ca-certificates curl && echo "PASSWORD" | sudo -S install -m 0755 -d /etc/apt/keyrings'
```

Add Docker GPG key:

```bash
sshpass -p 'PASSWORD' ssh USER@IP 'echo "PASSWORD" | sudo -S curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc && echo "PASSWORD" | sudo -S chmod a+r /etc/apt/keyrings/docker.asc'
```

Add Docker repository (for Ubuntu Noble/22.04+):

```bash
sshpass -p 'PASSWORD' ssh USER@IP 'echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu noble stable" > /tmp/docker.list && echo "PASSWORD" | sudo -S mv /tmp/docker.list /etc/apt/sources.list.d/docker.list'
```

Install Docker Engine:

```bash
sshpass -p 'PASSWORD' ssh USER@IP 'echo "PASSWORD" | sudo -S apt-get update -qq && echo "PASSWORD" | sudo -S apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin'
```

Add user to docker group:

```bash
sshpass -p 'PASSWORD' ssh USER@IP 'echo "PASSWORD" | sudo -S usermod -aG docker USER'
```

### 3. Install ngrok

Download and install ngrok binary:

```bash
sshpass -p 'PASSWORD' ssh USER@IP 'cd ~ && curl -sSL https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz -o ngrok.tgz && tar -xzf ngrok.tgz && rm ngrok.tgz && ./ngrok version'
```

Configure ngrok with auth token:

```bash
sshpass -p 'PASSWORD' ssh USER@IP '~/ngrok config add-authtoken 2ccs9husUvzPYjGwAmMG0SRNudv_6fsfqqvuamErEVCE7Lx1N'
```

### 4. Clone DomOS Repository

Create projects directory and clone:

```bash
sshpass -p 'PASSWORD' ssh USER@IP 'mkdir -p ~/projects && cd ~/projects && git clone https://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@github.com/geodanchev/DomOS.git'
```

### 5. Fix Missing Files

Create lib/utils.ts (required for shadcn/ui components):

```bash
sshpass -p 'PASSWORD' ssh USER@IP 'mkdir -p ~/projects/DomOS/mvp1-cashier/frontend/src/lib && cat > ~/projects/DomOS/mvp1-cashier/frontend/src/lib/utils.ts << '"'"'EOF'"'"'
import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
EOF'
```

Fix tsconfig.json if needed (remove invalid ignoreDeprecations):

```bash
sshpass -p 'PASSWORD' ssh USER@IP 'cd ~/projects/DomOS/mvp1-cashier/frontend && sed -i "/ignoreDeprecations/d" tsconfig.json'
```

### 6. Configure Environment

Copy environment template:

```bash
sshpass -p 'PASSWORD' ssh USER@IP 'cd ~/projects/DomOS/mvp1-cashier && cp .env.docker .env'
```

Check for port conflicts (common issue with Apache):

```bash
sshpass -p 'PASSWORD' ssh USER@IP 'echo "PASSWORD" | sudo -S lsof -i :80 2>/dev/null || echo "Port 80 is free"'
```

If port 80 is occupied, change frontend port:

```bash
sshpass -p 'PASSWORD' ssh USER@IP 'cd ~/projects/DomOS/mvp1-cashier && sed -i "s/FRONTEND_PORT=80/FRONTEND_PORT=3000/" .env'
```

### 7. Build and Start Docker Containers

Build and start all services:

```bash
sshpass -p 'PASSWORD' ssh USER@IP 'cd ~/projects/DomOS/mvp1-cashier && echo "PASSWORD" | sudo -S docker compose up -d --build'
```

Verify containers are running:

```bash
sshpass -p 'PASSWORD' ssh USER@IP 'echo "PASSWORD" | sudo -S docker ps'
```

Expected output shows three healthy containers:
- `domos-db` on port 5432
- `domos-backend` on port 8000
- `domos-frontend` on port 3000 (or 80)

### 8. Start ngrok Tunnel

Start ngrok to expose frontend:

```bash
sshpass -p 'PASSWORD' ssh USER@IP 'nohup ~/ngrok http 3000 > /tmp/ngrok.log 2>&1 &'
```

Wait a few seconds then get the public URL:

```bash
sshpass -p 'PASSWORD' ssh USER@IP 'curl -s http://localhost:4040/api/tunnels'
```

Extract the `public_url` from the JSON response - this is your external access URL.

## Useful Commands

### View Logs

```bash
sshpass -p 'PASSWORD' ssh USER@IP 'cd ~/projects/DomOS/mvp1-cashier && echo "PASSWORD" | sudo -S docker compose logs -f'
```

### Restart Services

```bash
sshpass -p 'PASSWORD' ssh USER@IP 'cd ~/projects/DomOS/mvp1-cashier && echo "PASSWORD" | sudo -S docker compose restart'
```

### Stop All Services

```bash
sshpass -p 'PASSWORD' ssh USER@IP 'cd ~/projects/DomOS/mvp1-cashier && echo "PASSWORD" | sudo -S docker compose down'
```

### Restart ngrok

```bash
sshpass -p 'PASSWORD' ssh USER@IP 'pkill ngrok; nohup ~/ngrok http 3000 > /tmp/ngrok.log 2>&1 &'
```

### Update Deployment

```bash
sshpass -p 'PASSWORD' ssh USER@IP 'cd ~/projects/DomOS && git pull && cd mvp1-cashier && echo "PASSWORD" | sudo -S docker compose up -d --build'
```

## Troubleshooting

### Port Already in Use

Check what's using the port:

```bash
sshpass -p 'PASSWORD' ssh USER@IP 'echo "PASSWORD" | sudo -S lsof -i :PORT'
```

### TypeScript Build Errors

If `ignoreDeprecations` error occurs, remove the line from tsconfig.json.
If `@/lib/utils` not found, create the utils.ts file as shown in Step 5.

### Container Health Issues

Check container logs:

```bash
sshpass -p 'PASSWORD' ssh USER@IP 'echo "PASSWORD" | sudo -S docker logs domos-backend'
```

### ngrok URL Not Working

Verify ngrok is running and check the tunnel status:

```bash
sshpass -p 'PASSWORD' ssh USER@IP 'pgrep -a ngrok && curl -s http://localhost:4040/api/tunnels'
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Remote Machine                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 Docker Network                       │   │
│  │  ┌──────────┐   ┌──────────┐   ┌──────────────────┐ │   │
│  │  │ domos-db │◄──│ backend  │◄──│    frontend      │ │   │
│  │  │  :5432   │   │  :8000   │   │  :80 (nginx)     │ │   │
│  │  └──────────┘   └──────────┘   └────────▲─────────┘ │   │
│  └─────────────────────────────────────────│───────────┘   │
│                                            │               │
│  ┌─────────────────────────────────────────┴─────────────┐ │
│  │                    ngrok tunnel                        │ │
│  │              localhost:3000 ──► https://xxx.ngrok.app  │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Internet Users │
                    │ (ngrok public   │
                    │     URL)        │
                    └─────────────────┘
```
