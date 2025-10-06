"""fix industry enum case to lowercase

Revision ID: d6c9079c6960
Revises: 7fd3054ae797
Create Date: 2025-10-06 14:28:47.729388

"""
from alembic import op
import sqlalchemy as sa


revision = 'd6c9079c6960'
down_revision = '7fd3054ae797'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Fix industry enum values to use lowercase consistently.

    The database enum already uses lowercase ('cinema', 'hotel', 'gym', 'b2b', 'retail', 'default'),
    but the Python code was using uppercase. This migration ensures any existing data
    is properly handled (though ideally none should exist since the enum constraint
    would have prevented insertion of uppercase values).
    """
    # The database enum is already correct (lowercase)
    # The Python code has been updated to match
    # No actual migration needed - this is a code-only fix

    # For safety, attempt to update any records that might have been created
    # before the enum constraint was enforced (should be none)
    op.execute("""
        -- This should affect 0 rows since the enum constraint prevents uppercase
        UPDATE organisations
        SET industry_type = LOWER(industry_type::text)::industry
        WHERE industry_type::text ~ '[A-Z]'
    """)


def downgrade() -> None:
    """
    No downgrade needed - the database enum definition doesn't change.
    This was purely a Python code fix to match the existing database schema.
    """
    pass