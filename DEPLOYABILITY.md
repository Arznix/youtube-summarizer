# Deployability Guide

This document describes the deployment options, considerations, and best practices for the YouTube Summarizer program.

---

## Overview

The YouTube Summarizer is designed for **local-first deployment**, meaning it runs on the user's own machine without requiring external cloud services. However, it can be deployed in various environments with appropriate configurations.

---

## Deployment Models

### 1. Local Desktop Deployment (Recommended)

**Best for**: Personal use, single user

**Requirements**:
- Windows 10/11, macOS 10.15+, or Linux
- Python 3.8+
- Ollama installed locally
- Internet connection

**Deployment Steps**:
```bash
# 1. Clone repository
git clone https://github.com/Arznix/youtube-summarizer.git
cd youtube-summarizer

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure
copy .env.example .env
# Edit .env with your settings

# 5. Run
python src/agent_orchestrator.py
```

**Advantages**:
- Simple setup
- No server maintenance
- Full control over data
- No recurring costs

**Limitations**:
- Only runs when computer is on
- Single user only
- Limited by local hardware

---

### 2. Headless Server Deployment

**Best for**: Always-on operation, single user

**Requirements**:
- Linux server (Ubuntu 20.04+)
- SSH access
- Python 3.8+
- Ollama installed

**Deployment Steps**:

```bash
# 1. Connect to server
ssh user@server-ip

# 2. Install dependencies
sudo apt update
sudo apt install python3 python3-pip python3-venv git

# 3. Clone repository
git clone https://github.com/Arznix/youtube-summarizer.git
cd youtube-summarizer

# 4. Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:1.5b

# 6. Configure
cp .env.example .env
nano .env  # Edit with your settings

# 7. Run as background service
nohup python3 src/agent_orchestrator.py > logs/scheduler.log 2>&1 &
```

**Advantages**:
- Always running
- No local computer needed
- Remote access possible

**Limitations**:
- Requires server management
- Network configuration needed
- Security considerations

---

### 3. Docker Deployment

**Best for**: Containerized environments, easy replication

**Requirements**:
- Docker installed
- Docker Compose (optional)

**Dockerfile**:
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create .env from example if not exists
RUN cp .env.example .env

# Expose no ports (runs as daemon)
# Volumes for persistent data
VOLUME ["/app/data", "/app/.env"]

# Run the application
CMD ["python", "src/agent_orchestrator.py"]
```

**Docker Compose** (`docker-compose.yml`):
```yaml
version: '3.8'

services:
  youtube-summarizer:
    build: .
    container_name: youtube-summarizer
    restart: unless-stopped
    volumes:
      - ./data:/app/data
      - ./.env:/app/.env
    environment:
      - TZ=UTC
    networks:
      - app-network

  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    restart: unless-stopped
    volumes:
      - ollama_data:/root/.ollama
    ports:
      - "11434:11434"
    networks:
      - app-network

volumes:
  ollama_data:

networks:
  app-network:
    driver: bridge
```

**Deployment Steps**:
```bash
# 1. Build and start
docker-compose up -d

# 2. Pull Ollama model
docker exec -it ollama ollama pull qwen2.5:1.5b

# 3. View logs
docker-compose logs -f youtube-summarizer

# 4. Stop
docker-compose down
```

**Advantages**:
- Consistent environment
- Easy to replicate
- Isolated from host
- Simple updates

**Limitations**:
- Requires Docker knowledge
- Additional overhead
- Ollama in Docker may have GPU limitations

---

### 4. Cloud VM Deployment

**Best for**: Scalable, production-like environments

**Supported Providers**:
- AWS EC2
- Google Cloud Compute Engine
- Azure Virtual Machines
- DigitalOcean Droplets
- Linode

**Example (AWS EC2)**:

```bash
# 1. Launch EC2 instance
# - AMI: Ubuntu 22.04 LTS
# - Instance type: t3.medium (2 vCPU, 4GB RAM)
# - Security group: Allow SSH (22), Ollama (11434)

# 2. Connect
ssh -i key.pem ubuntu@ec2-ip

# 3. Install dependencies
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git

# 4. Follow headless server deployment steps

# 5. Configure firewall
sudo ufw allow 22/tcp
sudo ufw allow 11434/tcp  # Ollama (if remote access needed)
sudo ufw enable
```

**Advantages**:
- Scalable resources
- High availability
- Professional infrastructure
- Backup options

**Limitations**:
- Recurring costs
- Complex configuration
- Security management
- Network latency

---

### 5. Raspberry Pi Deployment

**Best for**: Low-cost, always-on home server

**Requirements**:
- Raspberry Pi 4 (4GB+ RAM)
- Raspberry Pi OS (64-bit)
- Internet connection

**Deployment Steps**:

```bash
# 1. Setup Raspberry Pi OS
# - Flash SD card with 64-bit OS
# - Enable SSH
# - Connect to network

# 2. Update system
sudo apt update && sudo apt upgrade -y

# 3. Install dependencies
sudo apt install -y python3 python3-pip python3-venv git

# 4. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 5. Pull model
ollama pull qwen2.5:1.5b

# 6. Clone and setup project
git clone https://github.com/Arznix/youtube-summarizer.git
cd youtube-summarizer
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 7. Configure
cp .env.example .env
nano .env

# 8. Run
python3 src/agent_orchestrator.py
```

**Advantages**:
- Low cost (~$50-100)
- Low power consumption
- Always-on capable
- Educational

**Limitations**:
- Limited performance
- SD card reliability
- Memory constraints

---

## Deployment Considerations

### 1. Resource Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| **CPU** | 2 cores | 4+ cores |
| **RAM** | 4 GB | 8+ GB |
| **Storage** | 10 GB | 50+ GB |
| **Network** | 1 Mbps | 10+ Mbps |

### 2. Ollama Considerations

**Local vs Remote Ollama**:

```env
# Local Ollama (same machine)
OLLAMA_HOST=http://localhost:11434

# Remote Ollama (different machine)
OLLAMA_HOST=http://192.168.1.100:11434
```

**GPU Acceleration**:
- Ollama supports NVIDIA GPUs
- Requires CUDA drivers
- Significantly faster processing

**Model Selection**:
```env
# Fast, low resource (1.5B parameters)
OLLAMA_MODEL=qwen2.5:1.5b

# Better quality, higher resource (7B parameters)
OLLAMA_MODEL=qwen2.5:1.5b
```

### 3. Network Configuration

**Firewall Rules**:
```bash
# Linux (ufw)
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 11434/tcp   # Ollama (if remote)

# Windows Firewall
netsh advfirewall firewall add rule name="Ollama" dir=in action=allow protocol=TCP localport=11434
```

**Port Forwarding** (for remote access):
- Forward port 11434 to Ollama server
- Use HTTPS with reverse proxy for security

### 4. Security Considerations

**Network Security**:
- Use HTTPS for all external connections
- Implement IP whitelisting
- Use VPN for remote access
- Regular security updates

**Credential Management**:
- Use environment variables
- Never commit `.env` files
- Rotate credentials regularly
- Use secrets management for production

**Web Setup Server Security**:
- Server binds to localhost only (`127.0.0.1`)
- Auth token required for all API requests
- CSRF protection for all POST requests
- Bot token masked in browser UI
- All requests logged to `web_setup.log` with timestamp, IP, and status

### 5. Monitoring and Logging

**Log Files**:
```bash
# Application logs
tail -f orchestrator.log

# System logs (systemd)
journalctl -u youtube-summarizer -f
```

**Health Checks**:
```bash
# Check if process is running
ps aux | grep agent_orchestrator

# Check Ollama status
curl http://localhost:11434/api/tags

# Check database
sqlite3 data/subscriptions_state.db "SELECT COUNT(*) FROM videos;"
```

### 6. Backup and Recovery

**What to Backup**:
```bash
# Configuration
cp .env .env.backup

# Database
cp data/subscriptions_state.db data/backup/

# Logs (optional)
tar -czf logs-$(date +%Y%m%d).tar.gz logs/
```

**Automated Backup Script**:
```bash
#!/bin/bash
BACKUP_DIR="/backup/youtube-summarizer"
DATE=$(date +%Y%m%d)

mkdir -p $BACKUP_DIR
cp .env $BACKUP_DIR/.env.$DATE
cp data/subscriptions_state.db $BACKUP_DIR/db.$DATE

# Keep only last 7 days
find $BACKUP_DIR -name "*.env.*" -mtime +7 -delete
find $BACKUP_DIR -name "db.*" -mtime +7 -delete
```

---

## Deployment Scripts

### Windows Service (NSSM)

```bash
# Install NSSM (Non-Sucking Service Manager)
# Download from https://nssm.cc/download

# Install as Windows service
nssm install YouTubeSummarizer "C:\Python39\python.exe" "C:\path\to\src\agent_orchestrator.py"
nssm set YouTubeSummarizer AppDirectory "C:\path\to\youtube-summarizer"
nssm set YouTubeSummarizer DisplayName "YouTube Summarizer"
nssm set YouTubeSummarizer Description "YouTube video summarization service"
nssm set YouTubeSummarizer Start SERVICE_AUTO_START

# Start service
nssm start YouTubeSummarizer

# View logs
nssm logs YouTubeSummarizer
```

### Linux Systemd Service

```ini
# /etc/systemd/system/youtube-summarizer.service

[Unit]
Description=YouTube Summarizer Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/youtube-summarizer
ExecStart=/home/ubuntu/youtube-summarizer/venv/bin/python src/agent_orchestrator.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable youtube-summarizer
sudo systemctl start youtube-summarizer

# Check status
sudo systemctl status youtube-summarizer

# View logs
sudo journalctl -u youtube-summarizer -f
```

### macOS LaunchAgent

```xml
<!-- ~/Library/LaunchAgents/com.youtube.summarizer.plist -->

<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.youtube.summarizer</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/username/youtube-summarizer/src/agent_orchestrator.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/username/youtube-summarizer</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/username/youtube-summarizer/logs/stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/username/youtube-summarizer/logs/stderr.log</string>
</dict>
</plist>
```

```bash
# Load the agent
launchctl load ~/Library/LaunchAgents/com.youtube.summarizer.plist

# Unload the agent
launchctl unload ~/Library/LaunchAgents/com.youtube.summarizer.plist
```

---

## Update Procedures

### Manual Update

```bash
# 1. Stop the service
sudo systemctl stop youtube-summarizer  # Linux
nssm stop YouTubeSummarizer  # Windows

# 2. Backup configuration
cp .env .env.backup

# 3. Pull updates
git pull origin master

# 4. Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# 5. Restart service
sudo systemctl start youtube-summarizer  # Linux
nssm start YouTubeSummarizer  # Windows
```

### Automated Update Script

```bash
#!/bin/bash
# update.sh

set -e

echo "Updating YouTube Summarizer..."

# Stop service
sudo systemctl stop youtube-summarizer

# Backup
cp .env .env.backup.$(date +%Y%m%d)

# Pull changes
git pull origin master

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Start service
sudo systemctl start youtube-summarizer

echo "Update complete!"
```

---

## Performance Optimization

### 1. Database Optimization

```bash
# Vacuum database periodically
sqlite3 data/subscriptions_state.db "VACUUM;"

# Add indexes for better performance
sqlite3 data/subscriptions_state.db "
CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status);
CREATE INDEX IF NOT EXISTS idx_videos_video_id ON videos(video_id);
"
```

### 2. Log Rotation

```bash
# /etc/logrotate.d/youtube-summarizer

/home/ubuntu/youtube-summarizer/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 ubuntu ubuntu
}
```

### 3. Memory Management

```python
# In config.py
MAX_CHANNELS = 50  # Reduce if memory limited
TRANSCRIPT_CACHE_SIZE = 100  # Limit cache size
```

---

## Troubleshooting Deployments

### Common Issues

| Issue | Solution |
|-------|----------|
| Service won't start | Check logs, verify Python path |
| Ollama connection refused | Ensure Ollama is running, check firewall |
| Permission denied | Check file ownership, use sudo |
| Out of memory | Reduce channels, use smaller model |
| Database locked | Stop other instances, check permissions |

### Debug Mode

```bash
# Run with verbose logging
PYTHONUNBUFFERED=1 python src/agent_orchestrator.py --once

# Check environment variables
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.environ)"
```

### Health Check Script

```bash
#!/bin/bash
# healthcheck.sh

# Check if process is running
if ! pgrep -f "agent_orchestrator" > /dev/null; then
    echo "ERROR: YouTube Summarizer not running"
    exit 1
fi

# Check Ollama
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "ERROR: Ollama not responding"
    exit 1
fi

# Check database
if ! sqlite3 data/subscriptions_state.db "SELECT 1;" > /dev/null; then
    echo "ERROR: Database not accessible"
    exit 1
fi

echo "All checks passed"
exit 0
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] System meets minimum requirements
- [ ] Python 3.8+ installed
- [ ] Ollama installed and running
- [ ] AI model downloaded
- [ ] Network connectivity verified
- [ ] Firewall rules configured
- [ ] Credentials prepared

### Deployment

- [ ] Repository cloned
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] Configuration file created
- [ ] Telegram bot configured
- [ ] YouTube channels added
- [ ] Schedule configured
- [ ] Web setup tested (`python src/setup.py --web`)
- [ ] Web setup security verified (localhost binding, auth token)

### Post-Deployment

- [ ] Test run completed (`--once`)
- [ ] Telegram notifications working
- [ ] Logs being generated
- [ ] Service auto-starts on boot
- [ ] Monitoring configured
- [ ] Backup schedule set

---

## Cost Considerations

### Free Tier (Local)

| Component | Cost |
|-----------|------|
| Python | Free |
| Ollama | Free |
| Telegram Bot | Free |
| YouTube RSS | Free |
| **Total** | **$0** |

### Cloud Deployment (Estimated)

| Provider | Instance | Monthly Cost |
|----------|----------|--------------|
| AWS EC2 | t3.medium | ~$30 |
| Google Cloud | e2-medium | ~$25 |
| Azure | B2s | ~$30 |
| DigitalOcean | 2GB Droplet | ~$12 |
| Linode | 2GB | ~$10 |

---

## Conclusion

The YouTube Summarizer is designed for **easy local deployment** but can be deployed in various environments:

- **Simplest**: Local desktop (personal use)
- **Most Reliable**: Headless Linux server (always-on)
- **Most Portable**: Docker (consistent environment)
- **Most Scalable**: Cloud VM (production)
- **Most Affordable**: Raspberry Pi (home server)

**Recommended for beginners**: Local desktop deployment
**Recommended for production**: Headless Linux server with systemd

---

*Last updated: 2026-06-21*
