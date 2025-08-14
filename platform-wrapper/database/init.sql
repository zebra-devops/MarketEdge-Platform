-- Enable Row Level Security
ALTER DATABASE platform_wrapper SET row_security = on;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable RLS on all tables
-- This will be applied after tables are created via Alembic migrations