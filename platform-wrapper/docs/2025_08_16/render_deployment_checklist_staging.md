# Render Deployment Checklist - staging
Date: Sat 16 Aug 2025 16:14:35 BST
Deployer: zebra-devops

## Pre-Deployment
- [ ] Docker build tested locally
- [ ] render.yaml validated
- [ ] Environment variables documented
- [ ] Git changes committed
- [ ] Branch is up to date with remote

## Render Account Setup
- [ ] Render account created
- [ ] Team members invited
- [ ] Billing configured
- [ ] Service tier selected (Standard for production)

## Service Configuration
- [ ] GitHub repository connected
- [ ] Auto-deploy from branch: main
- [ ] Build settings configured
- [ ] Health check endpoint verified (/health)

## Database Setup
- [ ] PostgreSQL database created
- [ ] Redis instance created
- [ ] Connection strings verified
- [ ] Backup strategy configured

## Environment Variables
- [ ] AUTH0_CLIENT_SECRET set
- [ ] JWT_SECRET_KEY generated
- [ ] CORS origins configured
- [ ] Rate limiting configured

## DNS and SSL
- [ ] Custom domain configured (if applicable)
- [ ] SSL certificate active
- [ ] CORS origins updated with final domain

## Post-Deployment Validation
- [ ] Service is running (green status)
- [ ] Health check passing
- [ ] Logs reviewed for errors
- [ ] Database connectivity verified
- [ ] Redis connectivity verified
- [ ] Auth0 integration working
- [ ] CORS requests successful
- [ ] Rate limiting functional

## Monitoring Setup
- [ ] Log aggregation configured
- [ ] Alerts configured
- [ ] Performance baselines established
- [ ] Error tracking enabled

## Documentation
- [ ] Deployment notes updated
- [ ] Team notified of deployment
- [ ] Runbook updated
- [ ] Known issues documented

