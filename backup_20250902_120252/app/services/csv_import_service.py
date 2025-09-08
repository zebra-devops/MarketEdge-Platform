import csv
import io
import re
import logging
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, ValidationError
import json

logger = logging.getLogger(__name__)

from ..models.user import User, UserRole
from ..models.user_import import ImportBatch, ImportError, ImportStatus
from ..models.user_application_access import ApplicationType
from ..models.organisation import Organisation


class CSVUserRow(BaseModel):
    """Validation model for CSV user rows"""
    email: EmailStr
    first_name: str
    last_name: str
    role: UserRole = UserRole.viewer
    department: Optional[str] = None
    location: Optional[str] = None
    phone: Optional[str] = None
    market_edge_access: bool = False
    causal_edge_access: bool = False
    value_edge_access: bool = False
    send_invitation: bool = True

    class Config:
        str_strip_whitespace = True


class CSVValidationResult(BaseModel):
    """Result of CSV validation"""
    is_valid: bool
    total_rows: int
    valid_rows: List[CSVUserRow]
    errors: List[Dict[str, Any]]
    duplicates: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]


class CSVImportService:
    """Service for handling CSV user imports"""
    
    REQUIRED_HEADERS = ['email', 'first_name', 'last_name']
    OPTIONAL_HEADERS = ['role', 'department', 'location', 'phone', 
                       'market_edge_access', 'causal_edge_access', 'value_edge_access', 
                       'send_invitation']
    ALL_HEADERS = REQUIRED_HEADERS + OPTIONAL_HEADERS
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_ROWS = 5000  # Maximum rows to process
    
    def __init__(self, db: Session):
        self.db = db
    
    @staticmethod
    def sanitize_csv_cell(value: str) -> str:
        """Sanitize CSV cells to prevent injection attacks"""
        if not value:
            return value
            
        # Check for formula injection characters
        dangerous_prefixes = ('=', '+', '-', '@', '\t', '\r', '\n')
        if value.strip() and value.strip()[0] in dangerous_prefixes:
            # Prefix with single quote to escape formula interpretation
            return "'" + value
        
        return value
    
    async def validate_csv_file(self, file: UploadFile) -> CSVValidationResult:
        """Validate uploaded CSV file and return validation results"""
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV file")
        
        # Check file size
        content = await file.read()
        file_size = len(content)
        
        if file_size > self.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400, 
                detail=f"File too large. Maximum size is {self.MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        if file_size == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        await file.seek(0)  # Reset file pointer
        
        logger.info(f"Validating CSV file: {file.filename}, size: {file_size} bytes")
        
        try:
            content_str = content.decode('utf-8')
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="File must be UTF-8 encoded")
        
        # Parse CSV
        csv_reader = csv.DictReader(io.StringIO(content_str))
        
        # Validate headers
        headers = csv_reader.fieldnames
        if not headers:
            raise HTTPException(status_code=400, detail="CSV file is empty or has no headers")
        
        missing_headers = [h for h in self.REQUIRED_HEADERS if h not in headers]
        if missing_headers:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required headers: {', '.join(missing_headers)}"
            )
        
        # Validate and parse rows
        valid_rows = []
        errors = []
        duplicates = []
        warnings = []
        emails_seen = set()
        
        for row_num, row in enumerate(csv_reader, start=2):  # Start from 2 (header is row 1)
            # Check row limit
            if row_num - 1 > self.MAX_ROWS:
                warnings.append({
                    'row': row_num,
                    'message': f'Exceeded maximum row limit of {self.MAX_ROWS}. Remaining rows ignored.'
                })
                break
            try:
                # Check for duplicate emails within the CSV
                email = row.get('email', '').strip().lower()
                if email in emails_seen:
                    duplicates.append({
                        'row': row_num,
                        'email': email,
                        'message': 'Duplicate email in CSV file'
                    })
                    continue
                
                # Validate row data
                validated_row = self._validate_row(row, row_num)
                
                # Check for existing user in database
                existing_user = self.db.query(User).filter(User.email == validated_row.email).first()
                if existing_user:
                    duplicates.append({
                        'row': row_num,
                        'email': validated_row.email,
                        'message': 'User already exists in database',
                        'existing_user_id': str(existing_user.id)
                    })
                    continue
                
                emails_seen.add(email)
                valid_rows.append(validated_row)
                
            except ValidationError as e:
                for error in e.errors():
                    field = error['loc'][0] if error['loc'] else 'unknown'
                    errors.append({
                        'row': row_num,
                        'field': field,
                        'message': error['msg'],
                        'value': row.get(str(field), '')
                    })
            except Exception as e:
                errors.append({
                    'row': row_num,
                    'field': 'general',
                    'message': str(e),
                    'value': str(row)
                })
        
        return CSVValidationResult(
            is_valid=len(errors) == 0,
            total_rows=len(valid_rows) + len(errors) + len(duplicates),
            valid_rows=valid_rows,
            errors=errors,
            duplicates=duplicates,
            warnings=warnings
        )
    
    def _validate_row(self, row: Dict[str, str], row_num: int) -> CSVUserRow:
        """Validate a single CSV row"""
        # Clean and prepare row data
        clean_row = {}
        
        for field in self.ALL_HEADERS:
            # Sanitize the value to prevent CSV injection
            value = self.sanitize_csv_cell(row.get(field, '').strip())
            
            # Handle boolean fields
            if field.endswith('_access') or field == 'send_invitation':
                clean_row[field] = self._parse_boolean(value)
            # Handle role field
            elif field == 'role':
                clean_row[field] = self._validate_role(value)
            # Handle phone number
            elif field == 'phone':
                clean_row[field] = self._validate_phone(value) if value else None
            # Handle required string fields
            elif field in self.REQUIRED_HEADERS:
                if not value:
                    raise ValidationError([{
                        'loc': (field,),
                        'msg': f'{field} is required',
                        'type': 'value_error'
                    }], CSVUserRow)
                clean_row[field] = value
            # Handle optional string fields
            else:
                clean_row[field] = value if value else None
        
        return CSVUserRow(**clean_row)
    
    def _parse_boolean(self, value: str) -> bool:
        """Parse boolean values from CSV"""
        if not value:
            return False
        
        value_lower = value.lower().strip()
        return value_lower in ['true', 'yes', '1', 'y', 'on', 'enabled']
    
    def _validate_role(self, value: str) -> UserRole:
        """Validate and convert role value"""
        if not value:
            return UserRole.viewer
        
        value_lower = value.lower().strip()
        role_mapping = {
            'admin': UserRole.admin,
            'administrator': UserRole.admin,
            'analyst': UserRole.analyst,
            'user': UserRole.analyst,
            'viewer': UserRole.viewer,
            'read-only': UserRole.viewer,
            'readonly': UserRole.viewer
        }
        
        if value_lower in role_mapping:
            return role_mapping[value_lower]
        
        # Try direct enum match
        try:
            return UserRole(value_lower)
        except ValueError:
            raise ValidationError([{
                'loc': ('role',),
                'msg': f'Invalid role: {value}. Valid roles are: admin, analyst, viewer',
                'type': 'value_error'
            }], CSVUserRow)
    
    def _validate_phone(self, value: str) -> str:
        """Validate phone number format"""
        if not value:
            return None
        
        # Basic phone number validation (allows various formats)
        phone_pattern = re.compile(r'^[\+]?[\d\s\-\(\)\.]{10,20}$')
        if not phone_pattern.match(value):
            raise ValidationError([{
                'loc': ('phone',),
                'msg': 'Invalid phone number format',
                'type': 'value_error'
            }], CSVUserRow)
        
        return value
    
    async def create_import_batch(
        self, 
        filename: str, 
        total_rows: int,
        organisation_id: str,
        uploaded_by: str
    ) -> ImportBatch:
        """Create a new import batch record"""
        import_batch = ImportBatch(
            filename=filename,
            total_rows=total_rows,
            organisation_id=organisation_id,
            uploaded_by=uploaded_by,
            status=ImportStatus.PENDING
        )
        
        self.db.add(import_batch)
        self.db.commit()
        self.db.refresh(import_batch)
        
        return import_batch
    
    async def log_import_error(
        self, 
        import_batch_id: str,
        row_number: int,
        field_name: str,
        error_message: str,
        row_data: Dict[str, Any] = None
    ):
        """Log an import error"""
        import_error = ImportError(
            import_batch_id=import_batch_id,
            row_number=row_number,
            field_name=field_name,
            error_message=error_message,
            row_data=json.dumps(row_data) if row_data else None
        )
        
        self.db.add(import_error)
        self.db.commit()
    
    async def update_import_progress(
        self, 
        import_batch: ImportBatch,
        processed_rows: int,
        successful_rows: int,
        failed_rows: int,
        status: ImportStatus = None
    ):
        """Update import batch progress"""
        import_batch.processed_rows = processed_rows
        import_batch.successful_rows = successful_rows
        import_batch.failed_rows = failed_rows
        
        if status:
            import_batch.status = status
            
        if status == ImportStatus.PROCESSING and not import_batch.started_at:
            import_batch.started_at = datetime.utcnow()
        elif status in [ImportStatus.COMPLETED, ImportStatus.FAILED]:
            import_batch.completed_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(import_batch)
    
    def get_csv_template(self) -> str:
        """Generate CSV template with headers and example data"""
        headers = self.ALL_HEADERS
        example_data = [
            'john.doe@example.com',
            'John',
            'Doe',
            'analyst',
            'Engineering',
            'London',
            '+44 20 1234 5678',
            'true',
            'false',
            'true',
            'true'
        ]
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerow(example_data)
        
        return output.getvalue()