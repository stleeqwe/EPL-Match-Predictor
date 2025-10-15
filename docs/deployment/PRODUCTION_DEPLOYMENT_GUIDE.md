# Production Deployment Guide
## Enterprise-Grade Football Prediction System

---

## 🚀 Quick Start (Production Deployment)

### Prerequisites

- **Server**: Ubuntu 22.04 LTS or newer (2 vCPU, 8GB RAM minimum)
- **Docker**: 24.0+ with Docker Compose V2
- **Domain**: Registered domain with DNS configured
- **SSL**: Let's Encrypt or commercial certificate
- **Ports**: 80, 443, 5432, 6379 open (internal only for DB/Redis)

---

## 📋 Pre-Deployment Checklist

### 1. System Requirements Check

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sudo sh
sudo systemctl enable --now docker

# Install Docker Compose
sudo apt install docker-compose-plugin

# Verify
docker --version  # Should be 24.0+
docker compose version  # Should be v2.20+
```

### 2. Clone Repository

```bash
cd /opt
git clone https://github.com/yourorg/soccer-predictor.git
cd soccer-predictor
```

### 3. Configure Environment

```bash
# Copy template
cp .env.production.template .env.production

# Generate secrets
openssl rand -base64 32  # SECRET_KEY
openssl rand -base64 24  # POSTGRES_PASSWORD
openssl rand -base64 24  # REDIS_PASSWORD

# Edit configuration
nano .env.production
```

**Required Changes:**
```bash
SECRET_KEY=<generated-secret>
POSTGRES_PASSWORD=<strong-password>
REDIS_PASSWORD=<strong-password>
GRAFANA_PASSWORD=<admin-password>
FLOWER_PASSWORD=<monitor-password>
PGADMIN_PASSWORD=<pgadmin-password>

# Update domain
CORS_ORIGINS=https://yourdomain.com
GRAFANA_URL=https://grafana.yourdomain.com
```

### 4. SSL Certificate Setup

#### Option A: Let's Encrypt (Free)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Generate certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Certificates will be at:
# /etc/letsencrypt/live/yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/yourdomain.com/privkey.pem

# Copy to project
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./nginx/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./nginx/ssl/
sudo chown $(whoami):$(whoami) ./nginx/ssl/*
```

#### Option B: Commercial Certificate

```bash
# Place your certificates in:
./nginx/ssl/fullchain.pem
./nginx/ssl/privkey.pem
```

---

## 🏗️ Initial Deployment

### Step 1: Build Images

```bash
# Build all services
docker compose -f docker-compose.production.yml build

# Verify images
docker images | grep football
```

### Step 2: Initialize Database

```bash
# Start database only
docker compose -f docker-compose.production.yml up -d postgres redis

# Wait for health check
docker compose -f docker-compose.production.yml ps

# Run migrations
docker compose -f docker-compose.production.yml run --rm api alembic upgrade head

# Verify
docker compose -f docker-compose.production.yml exec postgres \
  psql -U predictor -d football_predictor -c "\dt"
```

### Step 3: Collect Historical Data

```bash
# Run data collection
docker compose -f docker-compose.production.yml run --rm api \
  python -m data_collection.production_data_pipeline \
  --seasons 2023-2024 2024-2025 \
  --output /app/data/epl_historical.csv

# Import to database
docker compose -f docker-compose.production.yml run --rm api \
  python -m scripts.import_historical_data \
  --file /app/data/epl_historical.csv
```

### Step 4: Train Initial Models

```bash
# Train Bayesian model
docker compose -f docker-compose.production.yml run --rm api \
  python -m models.train_bayesian_model \
  --samples 5000 \
  --burnin 2000 \
  --output /app/model_cache/bayesian_v1.0.pkl

# Train XGBoost ensemble
docker compose -f docker-compose.production.yml run --rm api \
  python -m models.train_xgboost \
  --output /app/model_cache/xgboost_v1.0.pkl

# Verify models
docker compose -f docker-compose.production.yml exec api ls -lh /app/model_cache/
```

### Step 5: Start All Services

```bash
# Start everything
docker compose -f docker-compose.production.yml up -d

# Check status
docker compose -f docker-compose.production.yml ps

# View logs
docker compose -f docker-compose.production.yml logs -f api
```

### Step 6: Verify Deployment

```bash
# Health checks
curl https://yourdomain.com/health
curl https://yourdomain.com/api/v1/health

# Test prediction
curl -X POST https://yourdomain.com/api/v1/predict/bayesian \
  -H "Content-Type: application/json" \
  -d '{
    "home_team": "Manchester City",
    "away_team": "Liverpool"
  }'

# Access monitoring
# Prometheus: http://your-server:9090
# Grafana: http://your-server:3001
# Flower: http://your-server:5555 (user: admin)
```

---

## 📊 Post-Deployment Configuration

### 1. Configure Grafana Dashboards

```bash
# Login to Grafana
open http://your-server:3001

# Credentials from .env.production
# User: GRAFANA_USER
# Password: GRAFANA_PASSWORD

# Import dashboards:
# 1. Go to Dashboards → Import
# 2. Upload JSON from ./monitoring/grafana/dashboards/
```

### 2. Set Up Alerts

#### Prometheus Alertmanager

```yaml
# monitoring/alertmanager.yml
global:
  slack_api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'

route:
  receiver: 'slack-notifications'
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h

receivers:
  - name: 'slack-notifications'
    slack_configs:
      - channel: '#football-predictor-alerts'
        title: '{{ .Status | toUpper }}: {{ .CommonLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
```

#### Critical Alerts

- API down > 2 minutes
- Database connections > 80%
- Model accuracy < 50%
- Data freshness > 12 hours
- Error rate > 1%

### 3. Enable Automatic Backups

```bash
# Database backups (daily at 3AM)
crontab -e

# Add:
0 3 * * * docker exec football_postgres pg_dump -U predictor football_predictor | \
  gzip > /backups/football_$(date +\%Y\%m\%d).sql.gz

# Retain 30 days
0 4 * * * find /backups -name "football_*.sql.gz" -mtime +30 -delete

# Model backups (weekly)
0 4 * * 0 tar -czf /backups/models_$(date +\%Y\%m\%d).tar.gz \
  /opt/soccer-predictor/model_cache/
```

### 4. Configure Log Rotation

```bash
# /etc/logrotate.d/football-predictor
/opt/soccer-predictor/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 644 appuser appuser
    sharedscripts
    postrotate
        docker compose -f /opt/soccer-predictor/docker-compose.production.yml \
          kill -SIGUSR1 api
    endscript
}
```

---

## 🔄 Continuous Operations

### Daily Data Updates

```bash
# Automated via Celery Beat
# Schedule: 2:00 AM UTC daily

# Manual trigger:
docker compose -f docker-compose.production.yml exec scheduler \
  celery -A tasks.celery call tasks.update_match_results
```

### Weekly Model Retraining

```bash
# Automated schedule: Sunday 3:00 AM UTC

# Manual retrain:
docker compose -f docker-compose.production.yml run --rm api \
  python -m models.retrain_all \
  --evaluate \
  --deploy-if-better
```

### Monitoring Checklist (Daily)

- [ ] Check Grafana dashboard for anomalies
- [ ] Review error logs: `docker compose logs --tail=100 api`
- [ ] Verify data freshness: `curl /api/v1/data/status`
- [ ] Check prediction accuracy: Grafana → Model Performance panel
- [ ] Review Celery task queue: Flower dashboard

---

## 🐛 Troubleshooting

### Issue: API Not Responding

```bash
# Check service status
docker compose ps

# View logs
docker compose logs api

# Restart API
docker compose restart api

# If persistent, check resources
docker stats

# Check database connection
docker compose exec api python -c "from database import check_connection; check_connection()"
```

### Issue: Model Predictions Slow (>5 seconds)

```bash
# Check model cache
docker compose exec api ls -lh /app/model_cache/

# Warm up cache
curl -X POST https://yourdomain.com/api/v1/models/warmup

# If still slow, check Redis
docker compose exec redis redis-cli --raw incr ping

# Increase workers
# Edit .env.production: MAX_WORKERS=8
docker compose up -d --scale api=2
```

### Issue: Data Collection Failing

```bash
# Check scraper logs
docker compose logs worker | grep "data_collection"

# Test manually
docker compose exec worker python -m data_collection.production_data_pipeline \
  --seasons 2024-2025 \
  --no-cache

# Common causes:
# - Rate limiting (increase FBREF_RATE_LIMIT)
# - Website structure changed (update selectors)
# - Network issues (check DNS)
```

### Issue: High Memory Usage

```bash
# Check per-service memory
docker stats --no-stream

# If Bayesian model using too much:
# Reduce BAYESIAN_SAMPLES in .env.production
# Restart: docker compose restart api worker

# If PostgreSQL:
# Tune postgresql.conf
docker compose exec postgres nano /var/lib/postgresql/data/postgresql.conf
# Set: shared_buffers = 2GB
# Set: effective_cache_size = 6GB
```

---

## 🔐 Security Hardening

### 1. Firewall Configuration

```bash
# UFW (Ubuntu)
sudo ufw enable
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 80/tcp  # HTTP
sudo ufw allow 443/tcp # HTTPS
sudo ufw deny 5432/tcp # Block external DB access
sudo ufw deny 6379/tcp # Block external Redis

# Verify
sudo ufw status
```

### 2. SSL/TLS Configuration

**Nginx SSL Settings:**
```nginx
# nginx/nginx.conf
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
ssl_prefer_server_ciphers off;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
ssl_stapling on;
ssl_stapling_verify on;

# HSTS
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

### 3. Database Security

```sql
-- Revoke public permissions
REVOKE ALL ON DATABASE football_predictor FROM PUBLIC;

-- Read-only user for analytics
CREATE ROLE analytics_user WITH LOGIN PASSWORD 'strong_password';
GRANT CONNECT ON DATABASE football_predictor TO analytics_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics_user;

-- API user (restricted)
CREATE ROLE api_user WITH LOGIN PASSWORD 'api_password';
GRANT CONNECT ON DATABASE football_predictor TO api_user;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO api_user;
```

### 4. Rate Limiting

```python
# Already configured in API
# See backend/api/middleware/rate_limit.py

# Adjust limits in .env.production:
API_RATE_LIMIT=100/minute  # Increase for production traffic
```

---

## 📈 Scaling Guide

### Horizontal Scaling (Multiple API Instances)

```bash
# Scale API to 4 instances
docker compose up -d --scale api=4

# Load balancer (Nginx) will distribute traffic
# Ensure Redis is used for session storage
```

### Database Scaling

```sql
-- Enable connection pooling
-- Already configured via SQLAlchemy:
-- pool_size=20, max_overflow=40

-- For high load, consider:
-- 1. Read replicas (pg_basebackup)
-- 2. Citus extension for sharding
-- 3. TimescaleDB continuous aggregates
```

### Vertical Scaling (Resource Limits)

```yaml
# docker-compose.production.yml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

---

## 💵 Cost Optimization

### Cloud Provider Estimates

**AWS (us-east-1):**
```
EC2 t3.large (2 vCPU, 8GB): $60/month
RDS PostgreSQL db.t3.medium: $80/month
ElastiCache Redis cache.t3.small: $30/month
ALB (Application Load Balancer): $20/month
Data Transfer (100GB): $9/month
CloudWatch: $10/month
Total: ~$209/month
```

**DigitalOcean (Recommended for startups):**
```
Droplet 8GB (4 vCPU): $48/month
Managed PostgreSQL 4GB: $60/month
Managed Redis 1GB: $15/month
Load Balancer: $12/month
Backups: $10/month
Total: ~$145/month
```

**Cost Reduction Tips:**
- Use spot instances for workers (AWS)
- Implement aggressive caching (reduce DB queries)
- Compress API responses (gzip)
- Use CDN for static assets
- Archive old data to S3/Glacier

---

## 📞 Support & Maintenance

### Regular Maintenance Schedule

**Daily:**
- Review error logs
- Check monitoring dashboards
- Verify data updates

**Weekly:**
- Model retraining
- Database VACUUM
- Review security alerts

**Monthly:**
- Update dependencies
- Security patches
- Performance review
- Cost analysis

**Quarterly:**
- Model performance audit
- Disaster recovery drill
- Capacity planning
- User feedback review

### Contact Information

```
On-Call Engineer: oncall@yourcompany.com
PagerDuty: https://yourcompany.pagerduty.com
Slack: #football-predictor-ops
Documentation: https://docs.yourcompany.com/football-predictor
```

---

## ✅ Production Readiness Checklist

### Infrastructure
- [x] Docker Compose configured
- [x] PostgreSQL + TimescaleDB setup
- [x] Redis caching layer
- [x] Nginx reverse proxy
- [x] SSL/TLS certificates

### Application
- [x] Environment variables secured
- [x] Database migrations ready
- [x] Model training pipeline
- [x] API documentation (Swagger)
- [x] Error handling & logging

### Monitoring
- [x] Prometheus metrics collection
- [x] Grafana dashboards
- [x] Alert rules configured
- [x] Log aggregation

### Security
- [x] Firewall configured
- [x] SSL/TLS enabled
- [x] Secrets management
- [x] Rate limiting
- [x] Input validation

### Operations
- [x] Backup strategy
- [x] Disaster recovery plan
- [x] Scaling procedures
- [x] Rollback procedures
- [x] Monitoring runbook

### Performance
- [x] Load testing completed
- [x] Caching strategy
- [x] Database indexing
- [x] Query optimization
- [x] CDN integration

---

**🎉 System Ready for Production Deployment!**

**Expected Performance:**
- Availability: 99.9%
- API Latency (P95): <500ms
- Prediction Accuracy: >53%
- Daily Predictions: 10,000+
- Concurrent Users: 1,000+

**Next Steps:**
1. Review this guide with DevOps team
2. Schedule deployment window
3. Execute deployment
4. Monitor for 48 hours
5. Gradual traffic ramp-up

---

**Version:** 1.0.0
**Last Updated:** 2025-10-02
**Maintained By:** Engineering Team
