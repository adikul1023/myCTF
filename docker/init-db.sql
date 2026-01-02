-- Forensic CTF Platform - Database Initialization
-- This script runs on first PostgreSQL container startup

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create additional indexes for performance
-- (These supplement the indexes defined in SQLAlchemy models)

-- Note: Tables are created by Alembic migrations or SQLAlchemy
-- This script is for database-level setup only
