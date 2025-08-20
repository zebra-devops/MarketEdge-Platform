
# Add this to your API endpoints (temporary)
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.organization import Organization
import uuid
from datetime import datetime

router = APIRouter()

TEMP_ADMIN_SECRET = "TEMP_SECRET_12345_REMOVE_AFTER_USE"

@router.post("/admin/create-super-admin")
async def create_super_admin(
    secret: str,
    db: Session = Depends(get_db)
):
    """Temporary endpoint to create Matt Lindop super admin user"""
    
    if secret != TEMP_ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == "matt.lindop@zebra.associates").first()
    if existing_user:
        return {"message": "User already exists", "user_id": str(existing_user.id)}
    
    # Create organization if it doesn't exist
    zebra_org = db.query(Organization).filter(Organization.name == "Zebra Associates").first()
    if not zebra_org:
        zebra_org = Organization(
            id=uuid.uuid4(),
            name="Zebra Associates",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(zebra_org)
        db.flush()
    
    # Create user
    matt_user = User(
        id=uuid.uuid4(),
        email="matt.lindop@zebra.associates",
        auth0_id="auth0|placeholder-will-be-updated-on-first-login",
        name="Matt Lindop",
        role="SUPER_ADMIN",
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(matt_user)
    db.commit()
    
    return {
        "message": "Super admin user created successfully",
        "user_id": str(matt_user.id),
        "email": matt_user.email,
        "role": matt_user.role
    }
