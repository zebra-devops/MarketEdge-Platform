from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks, Response
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import json
import logging

logger = logging.getLogger(__name__)

from ....core.database import get_db
from ....models.user import User, UserRole
from ....models.user_import import ImportBatch, ImportError, ImportStatus
from ....models.user_application_access import UserApplicationAccess, UserInvitation, ApplicationType, InvitationStatus
from ....models.organisation import Organisation
from ....auth.dependencies import get_current_user, require_admin, require_super_admin
from ....services.csv_import_service import CSVImportService, CSVValidationResult, CSVUserRow
from ....services.auth import send_invitation_email
from ....services.authorization_service import AuthorizationService
from ....middleware.upload_rate_limiter import check_csv_import_rate_limit
import secrets
from datetime import timedelta

router = APIRouter()


class ImportPreviewResponse(BaseModel):
    """Response for CSV import preview"""
    is_valid: bool
    total_rows: int
    valid_rows: int
    error_count: int
    duplicate_count: int
    warning_count: int
    errors: List[Dict[str, Any]]
    duplicates: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    preview_data: List[Dict[str, Any]]  # First 10 valid rows for preview


class ImportBatchResponse(BaseModel):
    """Response for import batch operations"""
    id: str
    filename: str
    status: str
    total_rows: int
    processed_rows: int
    successful_rows: int
    failed_rows: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class ImportExecuteRequest(BaseModel):
    """Request to execute CSV import"""
    send_invitations: bool = True
    skip_duplicates: bool = True
    default_role: UserRole = UserRole.viewer


@router.post("/organizations/{org_id}/users/import/template")
async def download_csv_template(
    org_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download CSV template for user import"""
    # Verify access using authorization service
    if not AuthorizationService.check_import_access(current_user, org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this organization"
        )
    
    csv_service = CSVImportService(db)
    template_content = csv_service.get_csv_template()
    
    return Response(
        content=template_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=user_import_template.csv"}
    )


@router.post("/organizations/{org_id}/users/import/preview", response_model=ImportPreviewResponse)
async def preview_csv_import(
    org_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Preview CSV import - validate and show preview without importing"""
    # Verify access using authorization service
    if not AuthorizationService.check_import_access(current_user, org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this organization"
        )
    
    # Verify organization exists
    org = db.query(Organisation).filter(Organisation.id == org_id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    csv_service = CSVImportService(db)
    validation_result = await csv_service.validate_csv_file(file)
    
    # Create preview data (first 10 valid rows)
    preview_data = []
    for row in validation_result.valid_rows[:10]:
        preview_data.append({
            'email': row.email,
            'first_name': row.first_name,
            'last_name': row.last_name,
            'role': row.role.value,
            'department': row.department,
            'location': row.location,
            'phone': row.phone,
            'applications': {
                'market_edge': row.market_edge_access,
                'causal_edge': row.causal_edge_access,
                'value_edge': row.value_edge_access
            }
        })
    
    return ImportPreviewResponse(
        is_valid=validation_result.is_valid,
        total_rows=validation_result.total_rows,
        valid_rows=len(validation_result.valid_rows),
        error_count=len(validation_result.errors),
        duplicate_count=len(validation_result.duplicates),
        warning_count=len(validation_result.warnings),
        errors=validation_result.errors,
        duplicates=validation_result.duplicates,
        warnings=validation_result.warnings,
        preview_data=preview_data
    )


@router.post("/organizations/{org_id}/users/import", response_model=ImportBatchResponse)
async def execute_csv_import(
    org_id: str,
    import_request: ImportExecuteRequest,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    rate_limit_metadata: dict = Depends(check_csv_import_rate_limit)
):
    """Execute CSV import with background processing"""
    # Verify access using authorization service
    if not AuthorizationService.check_import_access(current_user, org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this organization"
        )
    
    # Verify organization exists
    org = db.query(Organisation).filter(Organisation.id == org_id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    csv_service = CSVImportService(db)
    
    # Validate CSV first
    validation_result = await csv_service.validate_csv_file(file)
    
    if not validation_result.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "CSV validation failed",
                "errors": validation_result.errors,
                "duplicates": validation_result.duplicates
            }
        )
    
    # Create import batch
    import_batch = await csv_service.create_import_batch(
        filename=file.filename,
        total_rows=len(validation_result.valid_rows),
        organisation_id=org_id,
        uploaded_by=str(current_user.id)
    )
    
    # Start background processing
    background_tasks.add_task(
        process_csv_import,
        import_batch.id,
        validation_result.valid_rows,
        org_id,
        current_user.id,
        import_request.send_invitations,
        import_request.skip_duplicates
    )
    
    response = ImportBatchResponse(
        id=str(import_batch.id),
        filename=import_batch.filename,
        status=import_batch.status.value,
        total_rows=import_batch.total_rows,
        processed_rows=import_batch.processed_rows,
        successful_rows=import_batch.successful_rows,
        failed_rows=import_batch.failed_rows,
        created_at=import_batch.created_at
    )
    
    # Log the import for monitoring
    logger.info(f"CSV import initiated by user {current_user.id} for org {org_id}. "
                f"Batch ID: {import_batch.id}, Total rows: {len(validation_result.valid_rows)}")
    
    return response


@router.get("/organizations/{org_id}/users/import/{batch_id}", response_model=ImportBatchResponse)
async def get_import_batch_status(
    org_id: str,
    batch_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get import batch status and progress"""
    # Verify access using authorization service
    if not AuthorizationService.check_organization_access(current_user, org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this organization"
        )
    
    import_batch = db.query(ImportBatch).filter(
        ImportBatch.id == batch_id,
        ImportBatch.organisation_id == org_id
    ).first()
    
    if not import_batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Import batch not found"
        )
    
    return ImportBatchResponse(
        id=str(import_batch.id),
        filename=import_batch.filename,
        status=import_batch.status.value,
        total_rows=import_batch.total_rows,
        processed_rows=import_batch.processed_rows,
        successful_rows=import_batch.successful_rows,
        failed_rows=import_batch.failed_rows,
        created_at=import_batch.created_at,
        started_at=import_batch.started_at,
        completed_at=import_batch.completed_at,
        error_message=import_batch.error_message
    )


@router.get("/organizations/{org_id}/users/import/{batch_id}/errors")
async def get_import_batch_errors(
    org_id: str,
    batch_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed error information for import batch"""
    # Verify access
    if current_user.role not in [UserRole.admin] and str(current_user.organisation_id) != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this organization"
        )
    
    import_batch = db.query(ImportBatch).filter(
        ImportBatch.id == batch_id,
        ImportBatch.organisation_id == org_id
    ).first()
    
    if not import_batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Import batch not found"
        )
    
    errors = db.query(ImportError).filter(ImportError.import_batch_id == batch_id).all()
    
    return {
        "batch_id": batch_id,
        "total_errors": len(errors),
        "errors": [
            {
                "row_number": error.row_number,
                "field_name": error.field_name,
                "error_message": error.error_message,
                "row_data": json.loads(error.row_data) if error.row_data else None
            }
            for error in errors
        ]
    }


@router.get("/organizations/{org_id}/users/import", response_model=List[ImportBatchResponse])
async def get_import_history(
    org_id: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get import history for organization"""
    # Verify access
    if current_user.role not in [UserRole.admin] and str(current_user.organisation_id) != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this organization"
        )
    
    import_batches = db.query(ImportBatch).filter(
        ImportBatch.organisation_id == org_id
    ).order_by(ImportBatch.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        ImportBatchResponse(
            id=str(batch.id),
            filename=batch.filename,
            status=batch.status.value,
            total_rows=batch.total_rows,
            processed_rows=batch.processed_rows,
            successful_rows=batch.successful_rows,
            failed_rows=batch.failed_rows,
            created_at=batch.created_at,
            started_at=batch.started_at,
            completed_at=batch.completed_at,
            error_message=batch.error_message
        )
        for batch in import_batches
    ]


# Background task function
async def process_csv_import(
    import_batch_id: str,
    valid_rows: List[CSVUserRow],
    organisation_id: str,
    current_user_id: str,
    send_invitations: bool,
    skip_duplicates: bool
):
    """Background task to process CSV import"""
    from ....core.database import SessionLocal
    
    logger.info(f"Starting background import processing for batch {import_batch_id}")
    
    db = SessionLocal()
    try:
        csv_service = CSVImportService(db)
        import_batch = db.query(ImportBatch).filter(ImportBatch.id == import_batch_id).first()
        
        if not import_batch:
            logger.error(f"Import batch {import_batch_id} not found")
            return
        
        # Update status to processing
        await csv_service.update_import_progress(
            import_batch, 0, 0, 0, ImportStatus.PROCESSING
        )
        
        successful_count = 0
        failed_count = 0
        
        for i, user_row in enumerate(valid_rows):
            try:
                # Check for existing user (in case of concurrent imports)
                existing_user = db.query(User).filter(User.email == user_row.email).first()
                if existing_user:
                    if skip_duplicates:
                        continue
                    else:
                        await csv_service.log_import_error(
                            import_batch_id,
                            i + 2,  # Row number (accounting for header)
                            "email",
                            f"User with email {user_row.email} already exists",
                            user_row.dict()
                        )
                        failed_count += 1
                        continue
                
                # Create new user
                new_user = User(
                    email=user_row.email,
                    first_name=user_row.first_name,
                    last_name=user_row.last_name,
                    role=user_row.role,
                    organisation_id=organisation_id
                )
                
                db.add(new_user)
                db.flush()  # Get the user ID
                
                # Set up application access
                if user_row.market_edge_access:
                    db.add(UserApplicationAccess(
                        user_id=new_user.id,
                        application=ApplicationType.MARKET_EDGE,
                        has_access=True,
                        granted_by=current_user_id
                    ))
                
                if user_row.causal_edge_access:
                    db.add(UserApplicationAccess(
                        user_id=new_user.id,
                        application=ApplicationType.CAUSAL_EDGE,
                        has_access=True,
                        granted_by=current_user_id
                    ))
                
                if user_row.value_edge_access:
                    db.add(UserApplicationAccess(
                        user_id=new_user.id,
                        application=ApplicationType.VALUE_EDGE,
                        has_access=True,
                        granted_by=current_user_id
                    ))
                
                # Send invitation if requested
                if send_invitations and user_row.send_invitation:
                    invitation_token = secrets.token_urlsafe(32)
                    expires_at = datetime.utcnow() + timedelta(days=7)
                    
                    invitation = UserInvitation(
                        user_id=new_user.id,
                        invitation_token=invitation_token,
                        status=InvitationStatus.PENDING,
                        invited_by=current_user_id,
                        expires_at=expires_at
                    )
                    db.add(invitation)
                    
                    # Note: Email sending would happen here
                    # For now, we'll just create the invitation record
                
                db.commit()
                successful_count += 1
                
                # Update progress every 10 users
                if (i + 1) % 10 == 0:
                    await csv_service.update_import_progress(
                        import_batch, i + 1, successful_count, failed_count
                    )
                
            except Exception as e:
                db.rollback()
                await csv_service.log_import_error(
                    import_batch_id,
                    i + 2,  # Row number
                    "general",
                    str(e),
                    user_row.dict()
                )
                failed_count += 1
        
        # Final status update - set correct status based on results
        if failed_count == 0 and successful_count > 0:
            final_status = ImportStatus.COMPLETED
        elif successful_count == 0:
            final_status = ImportStatus.FAILED
        else:
            # Partial success - some users imported, some failed
            final_status = ImportStatus.COMPLETED
            import_batch.error_message = f"Partial import: {successful_count} succeeded, {failed_count} failed"
            
        await csv_service.update_import_progress(
            import_batch, len(valid_rows), successful_count, failed_count, final_status
        )
        
    except Exception as e:
        # Log the error for debugging
        logger.error(f"Import batch {import_batch_id} failed with error: {str(e)}", exc_info=True)
        
        # Update batch with error status
        if import_batch:
            import_batch.status = ImportStatus.FAILED
            import_batch.error_message = f"Import failed: {str(e)}"
            import_batch.completed_at = datetime.utcnow()
            db.commit()
            
            # Log failure details
            logger.error(f"Import batch {import_batch_id} marked as failed. "
                        f"Processed: {import_batch.processed_rows}, "
                        f"Successful: {import_batch.successful_rows}, "
                        f"Failed: {import_batch.failed_rows}")
    
    finally:
        db.close()
        logger.info(f"Import batch {import_batch_id} processing completed")