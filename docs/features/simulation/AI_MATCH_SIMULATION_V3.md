# AI Match Simulation v3.0 - Enterprise Production System
**EPL Predictor | AI-Powered Match Simulation Platform**

Version: 3.0
Status: Implementation Phase
Last Updated: 2025-10-08
Target Launch: Q1 2026

---

## 📋 Executive Summary

### Vision
세계 최고 수준의 AI 기반 축구 경기 시뮬레이션 플랫폼 구축. 사용자의 전문적인 분석을 AI와 결합하여 가장 정확하고 신뢰할 수 있는 예측을 제공.

### Key Differentiators
- **User-Centric Analysis**: 사용자 평가를 65% 가중치로 최우선 반영
- **Sharp Data Integration**: 검증된 Sharp 북메이커 데이터 활용 (PRO)
- **Claude AI**: 정성적 평가 이해 및 전술적 맥락 분석
- **Enterprise-Grade**: Production-ready 보안, 성능, 확장성

### Business Model
- **BASIC**: Free (시간당 5회 제한)
- **PRO**: $19.99/월 (무제한, Sharp Vision AI, Claude 4.5)

### Target Market
- 축구 분석가 및 전문 팬
- 스포츠 베터 (참고용)
- 축구 전술 연구자
- 콘텐츠 크리에이터

---

## 🎯 Product Specifications

### Service Tiers

#### 🆓 BASIC (Free)

**Data Structure (100%)**
- User Evaluation: **65%**
  - Player ratings (22명)
  - Team tactics (18 categories)
  - Qualitative comments
- FPL API: **15%**
  - Player condition
  - Injury status
  - Availability
- Odds API (General): **20%**
  - Bet365, William Hill, Betfair, 1xBet

**Features**
- AI Model: Claude Sonnet 3.5
- Scenarios: 3 (Win/Draw/Loss)
- Rate Limit: 5/hour
- Analysis: Basic report
- Export: Web view only

**Cost per User**
- Monthly: $2.10 (avg 100 uses)

---

#### ⭐ PRO ($19.99/month)

**Data Structure (100%)**
- User Evaluation: **65%**
  - Player ratings (22명)
  - Team tactics (18 categories)
  - Qualitative comments
- Sharp Vision AI: **20%**
  - `/api/match-predictions` (existing)
  - Sharp bookmaker consensus (Pinnacle, Betfair, Smarkets)
  - Poisson expected scores
- Football-Data.org API: **15%**
  - Recent 5-match form
  - Goal statistics
  - Home/Away performance
  - Real-time injuries

**Features**
- AI Model: Claude Sonnet 4.5
- Scenarios: 5 (Dominant Win/Win/Draw/Loss/Heavy Loss)
- Rate Limit: Unlimited
- Analysis: Detailed tactical report
- Export: PDF download
- Support: Priority

**Cost per User**
- Monthly: $7.56 (avg 300 uses)
- Margin: 2.6x (164%)

---

## 🏗️ System Architecture

### Technology Stack

```yaml
Backend:
  Runtime: Python 3.11
  Framework: Flask 3.0.0
  Database: PostgreSQL 15
  Cache: Redis 7.0
  Queue: Celery 5.3
  API Docs: OpenAPI 3.0

Frontend:
  Framework: React 18
  State: Redux Toolkit
  UI: Tailwind CSS 3.x
  Animation: Framer Motion
  Build: Vite 5.0

AI/ML:
  Provider: Anthropic Claude API
  Models:
    - Sonnet 3.5 (BASIC)
    - Sonnet 4.5 (PRO)
  Cache: Redis + Custom Layer
  Optimization: Prompt Caching (90% savings)

Payment:
  Provider: Stripe
  Products: Subscription
  Features: Customer Portal, Webhooks

Infrastructure:
  Cloud: AWS
  CDN: CloudFlare
  Container: Docker
  Orchestration: Docker Compose → Kubernetes
  CI/CD: GitHub Actions

Monitoring:
  APM: Sentry
  Logs: CloudWatch
  Metrics: Custom Dashboard
  Uptime: UptimeRobot

Security:
  Auth: JWT + OAuth 2.0
  Encryption: TLS 1.3, AES-256
  Secrets: AWS Secrets Manager
  WAF: CloudFlare
```

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    CloudFlare CDN/WAF                        │
│                    (Static Assets, DDoS Protection)          │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS
         ┌───────────────┴────────────────┐
         │                                │
    ┌────▼─────┐                   ┌─────▼──────┐
    │  React   │                   │   Flask    │
    │ Frontend │◄─────────────────►│    API     │
    │  (Vite)  │   REST + WS      │  Gateway   │
    └──────────┘                   └─────┬──────┘
                                         │
                         ┌───────────────┼───────────────┐
                         │               │               │
                  ┌──────▼──────┐ ┌─────▼─────┐ ┌──────▼──────┐
                  │   Auth      │ │   Core    │ │ Simulation  │
                  │  Service    │ │  Service  │ │   Service   │
                  │             │ │           │ │  (Celery)   │
                  │ - JWT       │ │ - User    │ │             │
                  │ - OAuth     │ │ - Rating  │ │ - Claude    │
                  │ - Session   │ │ - Team    │ │ - Queue     │
                  └──────┬──────┘ └─────┬─────┘ └──────┬──────┘
                         │               │               │
                         └───────────────┼───────────────┘
                                         │
                         ┌───────────────┼───────────────┐
                         │               │               │
                  ┌──────▼──────┐ ┌─────▼─────┐ ┌──────▼──────┐
                  │ PostgreSQL  │ │   Redis   │ │   Stripe    │
                  │             │ │           │ │             │
                  │ - Users     │ │ - Cache   │ │ - Payment   │
                  │ - Subs      │ │ - Queue   │ │ - Webhook   │
                  │ - Ratings   │ │ - Limit   │ └─────────────┘
                  │ - Logs      │ └───────────┘
                  └─────────────┘       │
                                        │
                         ┌──────────────┼──────────────┐
                         │              │              │
                  ┌──────▼──────┐ ┌────▼─────┐ ┌─────▼──────┐
                  │   Claude    │ │ External │ │ Monitoring │
                  │     API     │ │   APIs   │ │            │
                  │             │ │          │ │ - Sentry   │
                  │ - Sonnet 3.5│ │ - FPL    │ │ - Grafana  │
                  │ - Sonnet 4.5│ │ - F-Data │ │ - Alerts   │
                  └─────────────┘ └──────────┘ └────────────┘
```

---

## 💾 Database Schema

### PostgreSQL Tables

```sql
-- Users Table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    avatar_url TEXT,
    tier VARCHAR(20) DEFAULT 'BASIC' CHECK (tier IN ('BASIC', 'PRO')),
    stripe_customer_id VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    verification_token VARCHAR(255),
    reset_token VARCHAR(255),
    reset_token_expires TIMESTAMP,
    preferences JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_tier ON users(tier);
CREATE INDEX idx_users_stripe ON users(stripe_customer_id);

-- Subscriptions Table
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    stripe_subscription_id VARCHAR(255) UNIQUE,
    tier VARCHAR(20) NOT NULL CHECK (tier IN ('BASIC', 'PRO')),
    status VARCHAR(50) NOT NULL CHECK (status IN ('active', 'canceled', 'past_due', 'trialing', 'incomplete')),
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    canceled_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_subs_user_id ON subscriptions(user_id);
CREATE INDEX idx_subs_status ON subscriptions(status);
CREATE INDEX idx_subs_stripe ON subscriptions(stripe_subscription_id);

-- Usage Tracking Table
CREATE TABLE usage_tracking (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    endpoint VARCHAR(100) NOT NULL,
    method VARCHAR(10) NOT NULL,
    tier VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    response_time_ms INTEGER,
    status_code INTEGER,
    tokens_used INTEGER,
    cost_usd DECIMAL(10, 6),
    ip_address INET,
    user_agent TEXT
);

CREATE INDEX idx_usage_user_id ON usage_tracking(user_id);
CREATE INDEX idx_usage_timestamp ON usage_tracking(timestamp DESC);
CREATE INDEX idx_usage_endpoint ON usage_tracking(endpoint);

-- Simulation Results Cache Table
CREATE TABLE simulation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    match_id VARCHAR(100) NOT NULL,
    tier VARCHAR(20) NOT NULL,
    user_evaluation_hash VARCHAR(64) NOT NULL,
    scenarios JSONB NOT NULL,
    confidence JSONB,
    analysis JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    hit_count INTEGER DEFAULT 1,
    tokens_used INTEGER,
    cost_usd DECIMAL(10, 6)
);

CREATE INDEX idx_sim_user_id ON simulation_results(user_id);
CREATE INDEX idx_sim_match ON simulation_results(match_id);
CREATE INDEX idx_sim_hash ON simulation_results(user_evaluation_hash);
CREATE INDEX idx_sim_expires ON simulation_results(expires_at);

-- Rate Limits Table
CREATE TABLE rate_limits (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    endpoint VARCHAR(100) NOT NULL,
    window_start TIMESTAMP NOT NULL,
    count INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, endpoint, window_start)
);

CREATE INDEX idx_rate_user_window ON rate_limits(user_id, window_start);
CREATE INDEX idx_rate_endpoint ON rate_limits(endpoint);

-- Audit Logs Table
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(255),
    changes JSONB,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_action ON audit_logs(action);

-- Player Ratings (Existing - Migration)
-- Team Ratings (Existing - Migration)
-- Matches (New)
CREATE TABLE matches (
    id VARCHAR(100) PRIMARY KEY,
    home_team VARCHAR(100) NOT NULL,
    away_team VARCHAR(100) NOT NULL,
    gameweek INTEGER,
    kickoff_time TIMESTAMP,
    status VARCHAR(20),
    home_score INTEGER,
    away_score INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_matches_gameweek ON matches(gameweek);
CREATE INDEX idx_matches_kickoff ON matches(kickoff_time);
```

---

## 🔐 API Specification

### Authentication Endpoints

#### POST /api/v1/auth/register
```json
Request:
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "display_name": "John Doe"
}

Response 201:
{
  "user_id": "uuid",
  "message": "Registration successful. Please verify your email."
}
```

#### POST /api/v1/auth/login
```json
Request:
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}

Response 200:
{
  "access_token": "jwt_token",
  "refresh_token": "refresh_token",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "tier": "BASIC",
    "display_name": "John Doe"
  }
}
```

### Simulation Endpoints

#### POST /api/v1/simulation/run
```json
Request:
Headers:
  Authorization: Bearer {access_token}

Body:
{
  "match_id": "liv_mci_gw15",
  "user_evaluation": {
    "player_ratings": [
      {
        "name": "Mohamed Salah",
        "overall": 92,
        "form": 8.5,
        "position": "RW"
      }
    ],
    "team_tactics": {
      "attacking": 85,
      "defending": 78,
      "possession": 82,
      "pressing": 88
    },
    "comments": "Liverpool's high press will be key..."
  }
}

Response 200 (BASIC):
{
  "simulation_id": "uuid",
  "tier": "BASIC",
  "scenarios": [
    {
      "outcome": "Win",
      "probability": 45.2,
      "expected_score": "2-1",
      "reasoning": "Strong home advantage and Salah's form"
    },
    {
      "outcome": "Draw",
      "probability": 29.8,
      "expected_score": "1-1",
      "reasoning": "Both teams have solid defenses"
    },
    {
      "outcome": "Loss",
      "probability": 25.0,
      "expected_score": "1-2",
      "reasoning": "City's midfield control"
    }
  ],
  "confidence": {
    "level": "medium",
    "score": 58.3
  },
  "created_at": "2025-10-08T12:00:00Z",
  "tokens_used": 5200
}

Response 200 (PRO):
{
  "simulation_id": "uuid",
  "tier": "PRO",
  "scenarios": [
    {
      "outcome": "Dominant Win",
      "probability": 22.5,
      "expected_score_range": "3-0 to 4-1",
      "tactical_analysis": "Liverpool's gegenpressing overwhelms City's build-up...",
      "key_variables": [
        "Salah vs Walker matchup",
        "Midfield control in transition"
      ],
      "confidence": 72.1
    },
    {
      "outcome": "Win",
      "probability": 28.3,
      "expected_score_range": "2-1 to 2-0",
      "tactical_analysis": "Balanced match with Liverpool edging...",
      "key_variables": [...],
      "confidence": 65.4
    },
    {
      "outcome": "Draw",
      "probability": 26.2,
      "expected_score_range": "1-1 to 2-2",
      "tactical_analysis": "Tactical stalemate likely...",
      "key_variables": [...],
      "confidence": 61.8
    },
    {
      "outcome": "Loss",
      "probability": 18.1,
      "expected_score_range": "1-2 to 0-2",
      "tactical_analysis": "City's possession dominance...",
      "key_variables": [...],
      "confidence": 58.2
    },
    {
      "outcome": "Heavy Loss",
      "probability": 4.9,
      "expected_score_range": "0-3 to 1-4",
      "tactical_analysis": "Complete tactical breakdown...",
      "key_variables": [...],
      "confidence": 42.3
    }
  ],
  "overall_confidence": {
    "level": "high",
    "score": 68.7
  },
  "sharp_vision_data": {
    "probabilities": {
      "home": 0.43,
      "draw": 0.28,
      "away": 0.29
    },
    "expected_score": {
      "home": 1.8,
      "away": 1.4
    }
  },
  "tactical_summary": "This is a high-intensity clash...",
  "created_at": "2025-10-08T12:00:00Z",
  "tokens_used": 8400,
  "export_url": "/api/v1/simulation/{id}/export"
}

Response 429 (Rate Limit):
{
  "error": "Rate limit exceeded",
  "message": "BASIC tier allows 5 simulations per hour",
  "reset_at": "2025-10-08T13:00:00Z",
  "upgrade_url": "/pricing"
}
```

#### GET /api/v1/simulation/history
```json
Response 200:
{
  "simulations": [
    {
      "id": "uuid",
      "match_id": "liv_mci_gw15",
      "created_at": "2025-10-08T12:00:00Z",
      "tier": "PRO"
    }
  ],
  "total": 42,
  "page": 1,
  "per_page": 20
}
```

---

## 💰 Cost Structure & Pricing

### Monthly Costs

**Fixed Costs**
```
The Odds API:        $49
AWS EC2/RDS:         $50
CloudFlare:          $20
Stripe:              $0 (pay-per-transaction)
Monitoring/Tools:    $20
──────────────────────
Total Fixed:        $139/month
```

**Variable Costs (per user)**
```
BASIC:  $2.10/user  (100 simulations/month avg)
PRO:    $7.56/user  (300 simulations/month avg)
```

### Revenue Model

**Pricing**
```
BASIC: $0/month
PRO:   $19.99/month
```

**Break-even Analysis**
```
PRO subscribers needed: 11 users
Monthly revenue @ 50 PRO: $1,000
Monthly cost @ 50 PRO: $517
Monthly profit @ 50 PRO: $483 (48% margin)
```

**12-Month Projection (Conservative)**
```
Month 1-3:   20 PRO   →  $400/mo   →  $1,200
Month 4-6:   50 PRO   →  $1,000/mo →  $4,200 (cumulative)
Month 7-9:   100 PRO  →  $2,000/mo →  $10,200
Month 10-12: 200 PRO  →  $4,000/mo →  $22,200

Year 1 Revenue: $22,200
Year 1 Costs:   $7,500
Year 1 Profit:  $14,700
```

---

## 📅 Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
**Database & Core Infrastructure**

- [x] Project documentation (v3.0)
- [ ] PostgreSQL schema setup
- [ ] Redis configuration
- [ ] Database migrations system
- [ ] Environment configuration
- [ ] Logging infrastructure
- [ ] Error handling framework

**Deliverables:**
- ✅ Database schema
- ✅ Migration scripts
- ✅ Config management
- ✅ Logging system

---

### Phase 2: Authentication & User Management (Week 3-4)
**Enterprise-grade Auth System**

- [ ] User registration/login
- [ ] JWT token management
- [ ] Password hashing (bcrypt)
- [ ] Email verification
- [ ] Password reset
- [ ] OAuth 2.0 (Google)
- [ ] Session management (Redis)
- [ ] Rate limiting middleware
- [ ] Audit logging

**Deliverables:**
- ✅ Auth API endpoints
- ✅ JWT handler
- ✅ Rate limiter
- ✅ Email service
- ✅ OAuth integration

---

### Phase 3: Payment & Subscription (Week 5-6)
**Stripe Integration**

- [ ] Stripe customer creation
- [ ] Checkout session
- [ ] Customer portal
- [ ] Webhook handlers
- [ ] Subscription management
- [ ] Invoice generation
- [ ] Payment failure recovery
- [ ] Subscription status sync

**Deliverables:**
- ✅ Stripe API integration
- ✅ Payment endpoints
- ✅ Webhook processing
- ✅ Subscription logic

---

### Phase 4: AI Simulation Engine (Week 7-9)
**Claude API & Processing**

- [ ] Claude API client
- [ ] Prompt engineering (BASIC/PRO)
- [ ] Response parsing
- [ ] Caching layer (Redis)
- [ ] Cost tracking
- [ ] Celery task queue
- [ ] Async processing
- [ ] Sharp Vision AI integration
- [ ] Football-Data API integration
- [ ] FPL API integration
- [ ] Result validation
- [ ] Error handling & retry logic

**Deliverables:**
- ✅ AI simulation service
- ✅ Data pipeline
- ✅ Async task system
- ✅ Cache optimization

---

### Phase 5: Frontend Development (Week 10-12)
**React Application**

- [ ] Project setup (Vite + React 18)
- [ ] Redux store configuration
- [ ] Auth UI (Login/Register)
- [ ] Protected routes
- [ ] MyVision tab restructure
- [ ] MatchSimulator component
- [ ] Simulation results UI
- [ ] Tier comparison UI
- [ ] Payment/Subscription UI
- [ ] User dashboard
- [ ] Settings page
- [ ] Responsive design
- [ ] Error boundaries
- [ ] Loading states

**Deliverables:**
- ✅ Full React application
- ✅ Complete UI/UX
- ✅ Mobile responsive

---

### Phase 6: Integration & Testing (Week 13-14)
**Quality Assurance**

- [ ] Unit tests (Backend)
- [ ] Integration tests
- [ ] E2E tests (Cypress)
- [ ] Load testing (Locust)
- [ ] Security testing
- [ ] API documentation
- [ ] User documentation

**Deliverables:**
- ✅ Test coverage >80%
- ✅ Performance benchmarks
- ✅ Documentation

---

### Phase 7: Deployment & DevOps (Week 15-16)
**Production Launch**

- [ ] Docker containers
- [ ] Docker Compose
- [ ] AWS setup (EC2, RDS, S3)
- [ ] CloudFlare CDN
- [ ] SSL certificates
- [ ] Environment variables
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Monitoring (Sentry, CloudWatch)
- [ ] Backup strategy
- [ ] Disaster recovery

**Deliverables:**
- ✅ Production deployment
- ✅ CI/CD automation
- ✅ Monitoring dashboard

---

### Phase 8: Beta Launch & Optimization (Week 17-20)
**Closed Beta**

- [ ] Beta user recruitment (50-100 users)
- [ ] Feedback collection
- [ ] Performance optimization
- [ ] Bug fixes
- [ ] A/B testing
- [ ] Analytics integration
- [ ] Customer support setup

**Deliverables:**
- ✅ Beta program
- ✅ User feedback
- ✅ Optimized system

---

## 🚀 Immediate Next Steps

### Week 1-2: Foundation Setup

**Day 1-2: Database Setup**
1. Create PostgreSQL database
2. Run schema migrations
3. Seed initial data
4. Setup Redis
5. Test connections

**Day 3-4: Core Infrastructure**
1. Config management system
2. Logging infrastructure
3. Error handling framework
4. Database repositories
5. Unit test setup

**Day 5-7: API Foundation**
1. Flask app structure
2. Blueprint organization
3. Middleware setup
4. CORS configuration
5. API versioning

**Day 8-10: Development Environment**
1. Docker Compose setup
2. Environment variables
3. Development scripts
4. Testing framework
5. Documentation

---

## 📊 Success Metrics

### Technical KPIs
- API Response Time: <200ms (p95)
- Uptime: >99.9%
- Error Rate: <0.1%
- Test Coverage: >80%
- Security Score: A+

### Business KPIs
- Free → PRO Conversion: 5-10%
- Monthly Churn Rate: <5%
- Customer LTV: >$200
- CAC: <$50
- LTV/CAC Ratio: >4:1

### User Experience KPIs
- Simulation Accuracy: >55%
- User Satisfaction: >4.5/5
- Average Simulations/User: 150/month
- Support Response Time: <24h

---

## 📝 Change Log

### v3.0 (Current)
- Complete enterprise architecture design
- 2-tier pricing model (BASIC + PRO)
- Claude Sonnet 4.5 integration
- Sharp Vision AI data reuse
- Comprehensive implementation roadmap

### v2.0 (Previous)
- Initial PRO tier design
- Basic simulation concept
- Cost analysis

### v1.0 (Initial)
- Prototype concept
- MVP planning

---

## 👥 Team & Resources

### Required Skills
- Backend: Python, Flask, PostgreSQL, Redis
- Frontend: React, Redux, Tailwind
- DevOps: Docker, AWS, CI/CD
- AI: Prompt Engineering, Claude API
- Payment: Stripe Integration

### Estimated Timeline
- Development: 16 weeks
- Beta Testing: 4 weeks
- Launch Preparation: 2 weeks
- **Total: 22 weeks (~5.5 months)**

---

## 📞 Contact & Support

**Project Lead**: [Your Name]
**Email**: support@eplpredictor.com
**Repository**: Private (GitHub)
**Documentation**: /docs
**Status Dashboard**: /status

---

**Document Status**: ✅ Approved for Implementation
**Next Review**: After Phase 1 Completion
**Version Control**: Git tracked in /docs/AI_MATCH_SIMULATION_V3.md
