# B2B Email Environment Configuration Specification

**Document Date:** August 19, 2025  
**Technical Owner:** DevOps/Platform Team  
**Business Owner:** Product Owner  
**Security Review:** Required  
**Status:** Ready for Implementation  

## Overview

Technical specification for production B2B outbound email environment configuration supporting enterprise client onboarding capabilities. This document defines the exact environment variables, security requirements, and deployment procedures needed for US-010 implementation.

---

## Required Environment Variables

### **Production Environment (.env.production)**

```bash
# =============================================================================
# B2B OUTBOUND EMAIL CONFIGURATION
# =============================================================================

# SMTP Server Configuration
SMTP_SERVER=smtp.sendgrid.net                    # Production SMTP server
SMTP_PORT=587                                     # TLS port (recommended)
SMTP_USER=apikey                                  # SendGrid uses 'apikey' as username
SMTP_PASSWORD=SG.xxx_your_sendgrid_api_key_xxx   # SendGrid API key (32+ chars)

# Email Domain Configuration  
EMAIL_SENDER_ADDRESS=noreply@marketedge.com      # Verified sender address
EMAIL_SENDER_NAME=Market Edge Platform           # Display name for sender
EMAIL_REPLY_TO=support@marketedge.com            # Reply-to address

# Frontend Integration
FRONTEND_URL=https://app.marketedge.com          # Production frontend domain
INVITATION_BASE_URL=https://app.marketedge.com/accept-invitation  # Invitation landing page

# Email Template Configuration
EMAIL_TEMPLATE_VERSION=v1.0                      # Template version for A/B testing
EMAIL_BRAND_LOGO_URL=https://app.marketedge.com/assets/logo.png  # Brand logo URL

# Security and Compliance
EMAIL_ENCRYPTION_ENABLED=true                    # Force TLS encryption
EMAIL_RATE_LIMIT_PER_MINUTE=100                 # Rate limiting (adjust based on SMTP plan)
EMAIL_BOUNCE_TRACKING_ENABLED=true              # Enable bounce tracking
EMAIL_UNSUBSCRIBE_URL=https://app.marketedge.com/unsubscribe  # Compliance requirement

# Monitoring and Alerting
EMAIL_DELIVERY_MONITORING=true                   # Enable delivery monitoring
EMAIL_FAILURE_ALERT_THRESHOLD=5                 # Alert after 5% failure rate
EMAIL_DAILY_VOLUME_LIMIT=10000                  # Daily email volume limit

# Development/Debug (set to false in production)
EMAIL_DEBUG_MODE=false                          # Disable debug logging in production
EMAIL_TEST_MODE=false                           # Disable test mode in production
```

### **Staging Environment (.env.staging)**

```bash
# =============================================================================
# B2B OUTBOUND EMAIL CONFIGURATION - STAGING
# =============================================================================

# SMTP Server Configuration (same provider, different credentials)
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=SG.xxx_staging_sendgrid_api_key_xxx  # Separate staging API key

# Email Domain Configuration
EMAIL_SENDER_ADDRESS=noreply@staging.marketedge.com
EMAIL_SENDER_NAME=Market Edge Platform (Staging)
EMAIL_REPLY_TO=staging-support@marketedge.com

# Frontend Integration
FRONTEND_URL=https://staging.marketedge.com
INVITATION_BASE_URL=https://staging.marketedge.com/accept-invitation

# Email Template Configuration
EMAIL_TEMPLATE_VERSION=v1.0-staging
EMAIL_BRAND_LOGO_URL=https://staging.marketedge.com/assets/logo.png

# Security and Compliance
EMAIL_ENCRYPTION_ENABLED=true
EMAIL_RATE_LIMIT_PER_MINUTE=50                  # Lower rate limit for staging
EMAIL_BOUNCE_TRACKING_ENABLED=true
EMAIL_UNSUBSCRIBE_URL=https://staging.marketedge.com/unsubscribe

# Monitoring and Alerting
EMAIL_DELIVERY_MONITORING=true
EMAIL_FAILURE_ALERT_THRESHOLD=10               # Higher threshold for staging
EMAIL_DAILY_VOLUME_LIMIT=1000                  # Lower volume limit for staging

# Development/Debug
EMAIL_DEBUG_MODE=true                          # Enable debug logging in staging
EMAIL_TEST_MODE=false                          # Real emails in staging
```

### **Development Environment (.env.development)**

```bash
# =============================================================================
# B2B OUTBOUND EMAIL CONFIGURATION - DEVELOPMENT
# =============================================================================

# SMTP Server Configuration (development/testing)
SMTP_SERVER=smtp.mailtrap.io                    # Use Mailtrap for dev testing
SMTP_PORT=2525
SMTP_USER=your_mailtrap_username
SMTP_PASSWORD=your_mailtrap_password

# Email Domain Configuration
EMAIL_SENDER_ADDRESS=dev@localhost
EMAIL_SENDER_NAME=Market Edge Platform (Dev)
EMAIL_REPLY_TO=dev@localhost

# Frontend Integration
FRONTEND_URL=http://localhost:3000
INVITATION_BASE_URL=http://localhost:3000/accept-invitation

# Email Template Configuration
EMAIL_TEMPLATE_VERSION=v1.0-dev
EMAIL_BRAND_LOGO_URL=http://localhost:3000/assets/logo.png

# Security and Compliance
EMAIL_ENCRYPTION_ENABLED=false                  # TLS not required for dev
EMAIL_RATE_LIMIT_PER_MINUTE=10                 # Low rate limit for dev
EMAIL_BOUNCE_TRACKING_ENABLED=false            # Disable bounce tracking
EMAIL_UNSUBSCRIBE_URL=http://localhost:3000/unsubscribe

# Monitoring and Alerting
EMAIL_DELIVERY_MONITORING=false                # Disable monitoring in dev
EMAIL_FAILURE_ALERT_THRESHOLD=50              # High threshold for dev
EMAIL_DAILY_VOLUME_LIMIT=100                  # Low volume limit for dev

# Development/Debug
EMAIL_DEBUG_MODE=true                          # Enable debug logging
EMAIL_TEST_MODE=true                           # Use test mode in development
```

---

## SMTP Provider Recommendations

### **Primary Recommendation: SendGrid**

**Why SendGrid:**
- 99.9% uptime SLA
- Excellent deliverability rates (>95%)
- Comprehensive API and SMTP support
- Built-in bounce/spam handling
- Enterprise-grade security
- Detailed analytics and monitoring

**Setup Steps:**
1. Create SendGrid account and verify identity
2. Configure domain authentication (SPF, DKIM, DMARC)
3. Generate API key with Mail Send permissions
4. Set up IP warming (for high-volume sending)
5. Configure webhook endpoints for delivery tracking

**Pricing:** Free tier (100 emails/day), paid plans from $14.95/month

### **Alternative: AWS SES**

**Why AWS SES:**
- Cost-effective for high volume ($0.10 per 1,000 emails)
- Native AWS integration
- Excellent for existing AWS infrastructure
- High deliverability when properly configured

**Setup Considerations:**
- Requires AWS account and IAM configuration
- More complex setup than SendGrid
- Manual reputation management required
- Limited support compared to dedicated email providers

---

## Security Requirements

### **Credential Management**

#### **Production Security**
```bash
# Use AWS Secrets Manager or similar
aws secretsmanager create-secret \
    --name "marketedge/email/smtp-credentials" \
    --description "SMTP credentials for production email" \
    --secret-string '{
        "SMTP_SERVER": "smtp.sendgrid.net",
        "SMTP_PORT": "587", 
        "SMTP_USER": "apikey",
        "SMTP_PASSWORD": "SG.actual_api_key_here"
    }'
```

#### **Environment Variable Security**
- **Never commit credentials to version control**
- **Use secret management services in production**
- **Rotate SMTP credentials every 90 days**
- **Implement credential access logging**
- **Use different credentials per environment**

### **Email Security Compliance**

#### **Domain Authentication (Required)**
```dns
# SPF Record
marketedge.com TXT "v=spf1 include:sendgrid.net ~all"

# DKIM Record (provided by SendGrid)
s1._domainkey.marketedge.com CNAME s1.domainkey.u12345.wl123.sendgrid.net

# DMARC Record
_dmarc.marketedge.com TXT "v=DMARC1; p=quarantine; rua=mailto:dmarc@marketedge.com"
```

#### **Encryption Requirements**
- **TLS 1.2+ required for all SMTP connections**
- **Email content encryption for sensitive data**
- **Secure token generation for invitation links**
- **HTTPS required for all email links and images**

---

## Deployment Procedures

### **Environment Setup Checklist**

#### **Pre-Deployment**
- [ ] SMTP provider account created and verified
- [ ] Domain authentication records configured
- [ ] Environment variables template created
- [ ] Security review completed
- [ ] Staging environment tested

#### **Production Deployment**
- [ ] Secret management service configured
- [ ] Environment variables deployed securely
- [ ] SMTP connectivity tested
- [ ] Email template rendering validated
- [ ] Delivery monitoring configured
- [ ] Alert thresholds set

#### **Post-Deployment Validation**
- [ ] Test email delivery to multiple providers (Gmail, Outlook, Yahoo)
- [ ] Performance testing under load
- [ ] Monitoring dashboard functional
- [ ] Backup SMTP provider configured (if applicable)
- [ ] Documentation updated

### **Validation Scripts**

#### **Environment Validation Script**
```bash
#!/bin/bash
# validate_email_config.sh

echo "🔍 Validating Email Environment Configuration..."

# Check required environment variables
required_vars=(
    "SMTP_SERVER"
    "SMTP_PORT" 
    "SMTP_USER"
    "SMTP_PASSWORD"
    "EMAIL_SENDER_ADDRESS"
    "FRONTEND_URL"
)

for var in "${required_vars[@]}"; do
    if [[ -z "${!var}" ]]; then
        echo "❌ Missing required environment variable: $var"
        exit 1
    else
        echo "✅ $var is set"
    fi
done

# Test SMTP connectivity
echo "🔗 Testing SMTP connectivity..."
python3 -c "
import smtplib
import os
try:
    server = smtplib.SMTP(os.getenv('SMTP_SERVER'), int(os.getenv('SMTP_PORT')))
    server.starttls()
    server.login(os.getenv('SMTP_USER'), os.getenv('SMTP_PASSWORD'))
    server.quit()
    print('✅ SMTP connection successful')
except Exception as e:
    print(f'❌ SMTP connection failed: {e}')
    exit(1)
"

echo "🎉 Email configuration validation complete!"
```

#### **Test Email Script**
```python
#!/usr/bin/env python3
# test_email_delivery.py

import os
import sys
import asyncio
from app.services.auth import send_invitation_email

async def test_email_delivery():
    """Test email delivery with current configuration"""
    
    test_recipients = [
        "test@gmail.com",
        "test@outlook.com", 
        "test@yahoo.com"
    ]
    
    for email in test_recipients:
        try:
            await send_invitation_email(
                email=email,
                first_name="Test User",
                organization_name="Test Organization",
                invitation_token="test-token-123"
            )
            print(f"✅ Test email sent to {email}")
        except Exception as e:
            print(f"❌ Failed to send test email to {email}: {e}")
            return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_email_delivery())
    sys.exit(0 if success else 1)
```

---

## Monitoring and Alerting

### **Key Metrics to Monitor**

1. **Email Delivery Success Rate**
   - Target: >95% successful delivery
   - Alert: <90% over 15-minute window

2. **Email Delivery Time**
   - Target: <30 seconds average
   - Alert: >60 seconds average over 5 minutes

3. **SMTP Connection Health**
   - Target: 100% connection success
   - Alert: Any connection failures

4. **Daily Email Volume**
   - Target: Within SMTP provider limits
   - Alert: Approaching 80% of daily limit

### **Alerting Configuration**

#### **Critical Alerts (PagerDuty)**
- SMTP service completely unavailable
- >10% email delivery failure rate
- Security incidents (authentication failures)

#### **Warning Alerts (Slack)**
- >5% email delivery failure rate
- Slow email delivery (>60s average)
- Approaching rate limits

#### **Monitoring Dashboard KPIs**
- Real-time delivery success rate
- Email volume over time
- Provider-specific delivery rates
- Invitation click-through rates

---

## Cost Estimation

### **SendGrid Pricing (Recommended)**
- **Essentials Plan:** $14.95/month (50,000 emails)
- **Pro Plan:** $89.95/month (1,500,000 emails)
- **Premier Plan:** Custom pricing (high volume)

### **Infrastructure Costs**
- **Monitoring Tools:** $20-50/month
- **Domain/DNS Management:** $10-20/month
- **Secret Management:** $5-15/month (AWS Secrets Manager)

### **Total Monthly Cost Estimate**
- **Small Scale:** $50-100/month (up to 50K emails)
- **Enterprise Scale:** $150-300/month (up to 1M emails)

---

## Implementation Timeline

### **Phase 1: Setup and Configuration (2-3 days)**
- Day 1: SMTP provider setup and domain authentication
- Day 2: Environment variable configuration and secret management
- Day 3: Initial testing and validation

### **Phase 2: Testing and Validation (1-2 days)**  
- Day 4: Comprehensive delivery testing across email providers
- Day 5: Load testing and performance validation

### **Phase 3: Production Deployment (1 day)**
- Day 6: Production deployment and monitoring setup

**Total Duration:** 4-6 days within Phase 1 timeline

---

## Success Criteria

### **Technical Success**
- ✅ >95% email delivery success rate
- ✅ <30 second average delivery time
- ✅ 100% SMTP uptime during business hours
- ✅ Zero security incidents during deployment

### **Business Success**  
- ✅ Client invitation emails delivered reliably
- ✅ Sub-24 hour onboarding timeline maintained
- ✅ >90% invitation acceptance rate
- ✅ <2% email-related support tickets

---

## Conclusion

This specification provides comprehensive environment configuration requirements for B2B outbound email infrastructure supporting enterprise client onboarding. Implementation of these specifications will enable reliable email delivery for the £925K+ revenue opportunity while maintaining security and compliance standards.

**Next Steps:**
1. Security team review and approval
2. SMTP provider selection and account setup  
3. Environment variable deployment using secure methods
4. Comprehensive testing and validation
5. Production deployment with monitoring