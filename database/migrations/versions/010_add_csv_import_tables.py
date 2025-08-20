"""Add CSV import tables

Revision ID: 010
Revises: 009
Create Date: 2025-01-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade():
    # Create import status enum
    op.execute("CREATE TYPE importstatus AS ENUM ('pending', 'processing', 'completed', 'failed', 'cancelled')")
    
    # Create import_batches table
    op.create_table('import_batches',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('status', sa.Enum('pending', 'processing', 'completed', 'failed', 'cancelled', name='importstatus'), nullable=False, default='pending'),
        sa.Column('total_rows', sa.Integer(), nullable=False, default=0),
        sa.Column('processed_rows', sa.Integer(), nullable=False, default=0),
        sa.Column('successful_rows', sa.Integer(), nullable=False, default=0),
        sa.Column('failed_rows', sa.Integer(), nullable=False, default=0),
        sa.Column('organisation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['organisation_id'], ['organisations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create import_errors table
    op.create_table('import_errors',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('import_batch_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('row_number', sa.Integer(), nullable=False),
        sa.Column('field_name', sa.String(100), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=False),
        sa.Column('row_data', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['import_batch_id'], ['import_batches.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index('idx_import_batches_organisation_id', 'import_batches', ['organisation_id'])
    op.create_index('idx_import_batches_uploaded_by', 'import_batches', ['uploaded_by'])
    op.create_index('idx_import_batches_status', 'import_batches', ['status'])
    op.create_index('idx_import_batches_created_at', 'import_batches', ['created_at'])
    op.create_index('idx_import_errors_import_batch_id', 'import_errors', ['import_batch_id'])
    op.create_index('idx_import_errors_row_number', 'import_errors', ['row_number'])
    
    # Add extended user fields for CSV import
    op.add_column('users', sa.Column('department', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('location', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('phone', sa.String(20), nullable=True))


def downgrade():
    # Remove extended user fields
    op.drop_column('users', 'phone')
    op.drop_column('users', 'location')
    op.drop_column('users', 'department')
    
    # Drop indexes
    op.drop_index('idx_import_errors_row_number')
    op.drop_index('idx_import_errors_import_batch_id')
    op.drop_index('idx_import_batches_created_at')
    op.drop_index('idx_import_batches_status')
    op.drop_index('idx_import_batches_uploaded_by')
    op.drop_index('idx_import_batches_organisation_id')
    
    # Drop tables
    op.drop_table('import_errors')
    op.drop_table('import_batches')
    
    # Drop enum
    op.execute('DROP TYPE IF EXISTS importstatus')