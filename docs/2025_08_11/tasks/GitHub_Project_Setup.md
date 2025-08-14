# GitHub Project Setup: Zebra Edge

## Project Configuration

**Repository:** MarketEdge  
**Project Name:** Zebra Edge  
**Project Type:** Table view with automation  
**Development Cycle:** 3-week MVP Sprint

## Labels to Create

### Priority Labels
- `P0-Critical` (red) - Must have for MVP success
- `P1-High` (orange) - Important for user experience
- `P2-Medium` (yellow) - Nice to have features
- `P3-Low` (green) - Future consideration

### Sprint Labels
- `Week-1-Foundation` (blue) - Platform Foundation Sprint
- `Week-2-Odeon` (purple) - Odeon Pilot Implementation Sprint
- `Week-3-Production` (teal) - Visualization & Production Sprint

### Type Labels
- `Epic` (dark blue) - Major feature areas
- `Story` (light blue) - User stories
- `Task` (gray) - Technical tasks
- `Bug` (red) - Bug fixes

### Component Labels
- `Frontend` (green) - React/TypeScript frontend work
- `Backend` (orange) - API and server-side logic
- `Data` (purple) - Data integration and processing
- `Auth` (yellow) - Authentication and authorization
- `Deployment` (brown) - Production deployment tasks

## Milestones to Create

### Week 1 Complete: Platform Foundation Ready
**Due Date:** End of Week 1  
**Description:** Platform foundation with auth, user management, and client organizations  
**Success Criteria:**
- Client organizations with industry associations
- Super user management interface
- Enhanced authentication flow

### Week 2 Complete: Odeon Pilot Functional  
**Due Date:** End of Week 2  
**Description:** Functional Odeon cinema pilot with competitor pricing dashboard  
**Success Criteria:**
- Cinema market dashboard operational
- Competitor pricing data integration
- Market intelligence alerts system

### Week 3 Complete: Production Ready MVP
**Due Date:** End of Week 3  
**Description:** Complete MVP with visualizations and production deployment  
**Success Criteria:**
- Interactive data visualizations
- Stable Supabase integration  
- Production deployment complete

## Project Views to Configure

### 1. Sprint Board View
**Columns:**
- Backlog
- Week 1 - In Progress  
- Week 1 - Done
- Week 2 - In Progress
- Week 2 - Done  
- Week 3 - In Progress
- Week 3 - Done

### 2. Priority Matrix View
**Filters:**
- P0-Critical items (highest priority)
- P1-High items
- P2-Medium items
- P3-Low items

### 3. Component View
**Groups by Component:**
- Frontend issues
- Backend issues  
- Data integration issues
- Auth issues
- Deployment issues

### 4. Epic Tracking View
**Shows progress for:**
- Epic 1: Platform Foundation & User Management
- Epic 2: Odeon Cinema Pilot Dashboard
- Epic 3: Data Visualization & Production

## Automation Rules

### Issue Assignment
- Auto-assign issues with `Week-1-Foundation` to Sprint 1 milestone
- Auto-assign issues with `Week-2-Odeon` to Sprint 2 milestone  
- Auto-assign issues with `Week-3-Production` to Sprint 3 milestone

### Progress Tracking
- Move issues to "In Progress" when assigned to team member
- Move issues to "Done" when closed
- Update epic progress based on story completion

### Notification Rules
- Notify team on P0-Critical issue creation
- Notify project manager on milestone approaching
- Alert on blocked issues older than 2 days