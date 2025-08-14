# Hierarchical Organization Management API Documentation

## Overview

The Hierarchical Organization Management system extends MarketEdge's multi-tenant platform to support complex organizational structures with enterprise hierarchies, industry-specific configurations, and fine-grained permission management.

### Key Features

- **Hierarchical Organization Structure**: Organization → Location → Department → User permission inheritance
- **Enhanced Permission Model**: Five-tier role system with granular permissions
- **Industry Templates**: Pre-configured settings for Cinema, Hotel, Gym, B2B, and Retail industries
- **Rapid Client Onboarding**: <24 hour setup vs. 3-day baseline
- **Row-Level Security**: Database-level tenant isolation and access control
- **Backward Compatibility**: Seamless integration with existing user/org system

## Authentication & Authorization

All endpoints require Bearer token authentication. Permissions are enforced based on user roles and hierarchy assignments.

### Enhanced User Roles

| Role | Level | Permissions |
|------|--------|-------------|
| `super_admin` | Platform | Full cross-tenant access |
| `org_admin` | Organization | Full organization access |
| `location_manager` | Location | Location and department management |
| `department_lead` | Department | Department-specific management |
| `user` | Individual | Basic read/write access |
| `viewer` | Individual | Read-only access |

## API Endpoints

### Organization Management

#### Create Organization with Hierarchy

```http
POST /api/v1/v2/organizations
```

Creates a new organization with hierarchical structure and industry template.

**Request Body:**
```json
{
  "name": "Cinema Chain Corp",
  "industry_template_code": "CINEMA",
  "admin_user_email": "admin@cinemachain.com",
  "admin_user_first_name": "John",
  "admin_user_last_name": "Admin",
  "locations": [
    {
      "name": "Downtown Theater",
      "description": "Prime location theater",
      "settings": {
        "capacity": 500,
        "screens": 12,
        "premium_formats": ["IMAX", "Dolby"]
      }
    }
  ],
  "customizations": {
    "data_refresh_interval": 300,
    "features.dynamic_pricing": true
  }
}
```

**Response:**
```json
{
  "organization_id": "123e4567-e89b-12d3-a456-426614174000",
  "root_node_id": "123e4567-e89b-12d3-a456-426614174001",
  "admin_user_id": "123e4567-e89b-12d3-a456-426614174002",
  "locations_created": 1,
  "template_applied": true,
  "message": "Organization created successfully"
}
```

#### Get Organization Structure

```http
GET /api/v1/v2/organizations/{organization_id}/structure
```

Returns complete hierarchical structure of an organization.

**Response:**
```json
{
  "organization": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "Cinema Chain Corp",
    "level": "organization",
    "hierarchy_path": "cinema-chain-corp",
    "depth": 0,
    "children_count": 2,
    "user_count": 5
  },
  "locations": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174001",
      "name": "Downtown Theater",
      "level": "location",
      "hierarchy_path": "cinema-chain-corp/downtown-theater",
      "depth": 1,
      "children_count": 3,
      "user_count": 8
    }
  ],
  "departments": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174002",
      "name": "Operations",
      "level": "department",
      "hierarchy_path": "cinema-chain-corp/downtown-theater/operations",
      "depth": 2,
      "children_count": 0,
      "user_count": 3
    }
  ],
  "total_users": 16,
  "template_info": {
    "template_name": "Cinema Industry Standard",
    "industry_code": "CINEMA"
  }
}
```

### Hierarchy Node Management

#### Create Hierarchy Node

```http
POST /api/v1/v2/hierarchy-nodes
```

Creates a new hierarchy node (location, department, etc.).

**Request Body:**
```json
{
  "name": "New Location",
  "description": "Additional theater location",
  "parent_id": "123e4567-e89b-12d3-a456-426614174000",
  "level": "location",
  "settings": {
    "capacity": 300,
    "screens": 8
  }
}
```

#### Update Hierarchy Node

```http
PUT /api/v1/v2/hierarchy-nodes/{node_id}
```

**Request Body:**
```json
{
  "name": "Updated Location Name",
  "description": "Updated description",
  "is_active": true,
  "settings": {
    "capacity": 350,
    "screens": 10
  }
}
```

#### Delete Hierarchy Node

```http
DELETE /api/v1/v2/hierarchy-nodes/{node_id}?force=false
```

Deletes a hierarchy node. Use `force=true` to recursively delete children.

### User Assignment

#### Assign User to Node

```http
POST /api/v1/v2/hierarchy-nodes/{node_id}/assign-user
```

Assigns a user to a hierarchy node with specific role.

**Request Body:**
```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174003",
  "role": "location_manager",
  "is_primary": true
}
```

### Permission Management

#### Get User Permissions

```http
GET /api/v1/v2/users/{user_id}/permissions?context_node_id={node_id}
```

Returns resolved permissions for a user in specific context.

**Response:**
```json
{
  "permissions": [
    "read",
    "write", 
    "manage_users",
    "view_reports"
  ],
  "detailed_permissions": {
    "read": {
      "granted": true,
      "source": "role_assignment",
      "priority": 3
    },
    "manage_users": {
      "granted": true,
      "source": "user_override",
      "priority": 5,
      "reason": "Special project access"
    }
  },
  "metadata": {
    "resolution_path": [
      {
        "node_id": "123e4567-e89b-12d3-a456-426614174001",
        "node_name": "Downtown Theater",
        "node_level": "location",
        "user_role": "location_manager"
      }
    ],
    "overrides_applied": [
      {
        "permission": "manage_users", 
        "granted": true,
        "reason": "Special project access"
      }
    ],
    "inheritance_chain": []
  }
}
```

#### Get User Accessible Nodes

```http
GET /api/v1/v2/users/{user_id}/accessible-nodes?minimum_role=location_manager
```

Returns all hierarchy nodes accessible to a user.

**Response:**
```json
{
  "accessible_nodes": [
    {
      "node_id": "123e4567-e89b-12d3-a456-426614174001",
      "name": "Downtown Theater",
      "level": "location",
      "hierarchy_path": "cinema-chain-corp/downtown-theater",
      "user_role": "location_manager",
      "is_primary": true
    }
  ]
}
```

## Industry Templates

### List Templates

```http
GET /api/v1/v2/industry-templates?active_only=true&industry_code=CINEMA
```

**Response:**
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174004",
    "name": "Cinema Industry Standard",
    "industry_code": "CINEMA",
    "display_name": "Cinema & Entertainment",
    "default_settings": {
      "industry_type": "cinema",
      "subscription_plan": "professional",
      "features": {
        "dynamic_pricing": true,
        "competitor_tracking": true,
        "capacity_monitoring": true
      }
    },
    "default_permissions": {
      "org_admin": ["read", "write", "delete", "admin", "manage_users"],
      "location_manager": ["read", "write", "manage_users", "view_reports"],
      "user": ["read", "view_reports"]
    },
    "customizable_fields": [
      "data_refresh_interval",
      "features.dynamic_pricing", 
      "rate_limit_per_hour"
    ],
    "organizations_count": 15,
    "version": "1.0.0"
  }
]
```

### Create Template

```http
POST /api/v1/v2/industry-templates
```

**Request Body:**
```json
{
  "name": "Custom Cinema Template",
  "industry_code": "CINEMA_PREMIUM",
  "display_name": "Premium Cinema Experience",
  "description": "Enhanced template for premium cinema chains",
  "default_settings": {
    "industry_type": "cinema",
    "subscription_plan": "enterprise",
    "features": {
      "dynamic_pricing": true,
      "vip_services": true,
      "advanced_analytics": true
    }
  },
  "default_permissions": {
    "org_admin": ["read", "write", "delete", "admin", "manage_users", "manage_settings", "view_reports", "export_data"],
    "location_manager": ["read", "write", "manage_users", "view_reports", "export_data"]
  },
  "default_features": {
    "pricing_optimization": true,
    "competitor_analysis": true,
    "premium_support": true
  },
  "customizable_fields": ["features.vip_services", "subscription_plan"]
}
```

### Apply Template

```http
POST /api/v1/v2/industry-templates/apply
```

**Request Body:**
```json
{
  "template_id": "123e4567-e89b-12d3-a456-426614174004",
  "organization_id": "123e4567-e89b-12d3-a456-426614174000",
  "customizations": {
    "data_refresh_interval": 600,
    "features.dynamic_pricing": false
  },
  "override_existing": false
}
```

### Initialize Default Templates

```http
POST /api/v1/v2/industry-templates/initialize-defaults
```

Creates default industry templates (Cinema, Hotel, etc.).

## Industry-Specific Configurations

### Cinema Industry Template

**Features:**
- Dynamic pricing optimization
- Competitor tracking and analysis
- Capacity monitoring and forecasting
- Seasonal pricing adjustments
- Real-time occupancy data

**Default Settings:**
```json
{
  "industry_type": "cinema",
  "subscription_plan": "professional",
  "rate_limit_per_hour": 2000,
  "burst_limit": 200,
  "features": {
    "dynamic_pricing": true,
    "competitor_tracking": true,
    "capacity_monitoring": true,
    "seasonal_adjustments": true,
    "real_time_updates": true
  },
  "dashboard_widgets": [
    "revenue_chart",
    "competitor_comparison", 
    "capacity_utilization"
  ],
  "data_refresh_interval": 300
}
```

### Hotel Industry Template

**Features:**
- Room rate optimization
- Occupancy forecasting
- Competitor benchmarking
- Revenue management tools
- Demand prediction analytics

**Default Settings:**
```json
{
  "industry_type": "hotel",
  "subscription_plan": "enterprise", 
  "rate_limit_per_hour": 3000,
  "burst_limit": 300,
  "features": {
    "room_rate_optimization": true,
    "occupancy_forecasting": true,
    "competitor_benchmarking": true,
    "seasonal_pricing": true,
    "real_time_availability": true
  },
  "dashboard_widgets": [
    "adr_chart",
    "occupancy_trends",
    "revenue_per_room"
  ],
  "data_refresh_interval": 600
}
```

## Permission Resolution Logic

### Resolution Order (Priority High to Low)

1. **User-specific permission overrides** - Individual user grants/revokes
2. **Role-based permissions at current level** - Direct role assignments
3. **Inherited permissions from parent levels** - Cascading permissions
4. **Industry template defaults** - Fallback permissions

### Example Resolution

For a user assigned as `location_manager` at "Downtown Theater":

1. Check for individual overrides at location level
2. Get `location_manager` role permissions at location
3. Inherit applicable permissions from organization level
4. Apply industry template defaults for missing permissions

## Error Handling

### Common HTTP Status Codes

- `200 OK` - Successful operation
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource already exists
- `500 Internal Server Error` - Server error

### Error Response Format

```json
{
  "detail": "Error message",
  "error_code": "HIERARCHY_NODE_NOT_FOUND",
  "context": {
    "node_id": "123e4567-e89b-12d3-a456-426614174000",
    "operation": "assign_user"
  }
}
```

## Rate Limiting

API endpoints are subject to rate limiting based on organization subscription plan:

- **Basic**: 1000 requests/hour, 100 burst
- **Professional**: 2000 requests/hour, 200 burst  
- **Enterprise**: 5000 requests/hour, 500 burst

## Database Schema

### Key Tables

- `organization_hierarchy` - Hierarchical organization structure
- `user_hierarchy_assignments` - User-to-node role assignments
- `hierarchy_role_assignments` - Role-based permissions per node
- `hierarchy_permission_overrides` - User-specific permission overrides
- `industry_templates` - Industry configuration templates
- `organization_template_applications` - Applied templates tracking

### Row Level Security

All hierarchical tables implement RLS policies ensuring:
- Tenant isolation (users only see their organization's data)
- Super admin cross-tenant access when explicitly allowed
- Automatic filtering based on `current_tenant_id` session variable

## Migration & Backward Compatibility

### Legacy Role Mapping

| Legacy Role | Enhanced Role | Notes |
|-------------|---------------|--------|
| `admin` | `org_admin` | Full backward compatibility |
| `analyst` | `user` | Maintains existing access levels |
| `viewer` | `viewer` | Unchanged permissions |

### Migration Process

1. **Phase 1**: Add hierarchical tables alongside existing schema
2. **Phase 2**: Migrate existing organizations to hierarchy structure
3. **Phase 3**: Create default role assignments for existing users
4. **Phase 4**: Enable enhanced permission checks with fallback

## Performance Considerations

### Optimization Strategies

- **Indexed Queries**: All permission lookups use indexed columns
- **Caching**: Permission resolution results cached for 5 minutes
- **Batch Operations**: Bulk user assignments optimized for large organizations
- **Lazy Loading**: Hierarchy traversal only loads required levels

### Performance Benchmarks

- Permission resolution: <50ms for 95th percentile
- Organization creation: <2 seconds end-to-end
- User assignment: <100ms per assignment
- Template application: <5 seconds including configurations

## Security Features

### Multi-Layer Security

1. **API Level**: Bearer token authentication + role-based authorization
2. **Service Level**: Permission resolution engine with audit logging
3. **Database Level**: Row Level Security policies with tenant isolation
4. **Application Level**: Input validation and sanitization

### Audit Logging

All hierarchy changes are logged with:
- User performing action
- Timestamp and operation type
- Before/after states
- Reason/context when provided

## Integration Examples

### Create Cinema Organization (Complete Workflow)

```bash
# 1. Create organization with cinema template
curl -X POST "https://api.marketedge.com/api/v1/v2/organizations" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Regal Cinemas",
    "industry_template_code": "CINEMA",
    "admin_user_email": "admin@regal.com",
    "admin_user_first_name": "Admin",
    "admin_user_last_name": "User",
    "locations": [
      {
        "name": "Times Square",
        "description": "Flagship location"
      }
    ]
  }'

# 2. Add additional location  
curl -X POST "https://api.marketedge.com/api/v1/v2/hierarchy-nodes" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Brooklyn Heights",
    "parent_id": "ROOT_NODE_ID",
    "level": "location",
    "description": "Community theater"
  }'

# 3. Assign location manager
curl -X POST "https://api.marketedge.com/api/v1/v2/hierarchy-nodes/LOCATION_NODE_ID/assign-user" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "USER_ID",
    "role": "location_manager",
    "is_primary": true
  }'
```

## Support & Resources

- **API Reference**: Full OpenAPI/Swagger documentation at `/docs`
- **SDKs**: Available for Python, JavaScript, and Java
- **Webhooks**: Real-time notifications for hierarchy changes
- **Support**: Priority support for Enterprise customers