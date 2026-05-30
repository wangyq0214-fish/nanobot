# Database Setup Guide

This guide explains how to set up and use PostgreSQL database with nanobot for persistent storage.

## Prerequisites

1. **PostgreSQL** installed and running
2. **Python 3.11+** with pip or uv

## Installation

Install the required dependencies:

```bash
# Using pip
pip install -e ".[dev]"

# Or using uv
uv sync --all-extras
```

The database dependencies are included in the base installation:
- `sqlalchemy[asyncio]` - SQL toolkit and ORM
- `asyncpg` - Async PostgreSQL driver
- `alembic` - Database migration tool

## Database Setup

### 1. Create PostgreSQL Database

```bash
# Connect to PostgreSQL as superuser
psql -U postgres

# Create database and user
CREATE USER nanobot WITH PASSWORD 'nanobot';
CREATE DATABASE nanobot OWNER nanobot;
GRANT ALL PRIVILEGES ON DATABASE nanobot TO nanobot;
```

### 2. Configure Database Connection

**Option A: Environment Variable**

```bash
export NANOBOT_DATABASE_URL="postgresql+asyncpg://nanobot:nanobot@localhost:5432/nanobot"
```

**Option B: Config File**

Add to your `~/.nanobot/config.json`:

```json
{
  "database": {
    "url": "postgresql+asyncpg://nanobot:nanobot@localhost:5432/nanobot",
    "echo": false,
    "poolSize": 5,
    "maxOverflow": 10
  }
}
```

### 3. Initialize Database Tables

```bash
# Create all tables
nanobot migrate-db run

# Check migration status
nanobot migrate-db status
```

## Migrating Existing Data

If you have existing data in file-based storage (`~/.nanobot/courses/` and `~/.nanobot/users.json`), you can migrate it to the database:

```bash
# Run migration (default paths)
nanobot migrate-db run

# Specify custom nanobot directory
nanobot migrate-db run --nanobot-dir /path/to/.nanobot

# Specify custom database URL
nanobot migrate-db run --db-url "postgresql+asyncpg://user:pass@host:port/db"
```

The migration will:
1. Read all users from `~/.nanobot/users.json`
2. Read all courses from `~/.nanobot/courses/`
3. Migrate course members, lessons, homework, and submissions
4. Preserve relationships between entities

## Database Schema

### Users Table
- `role` (PK) - User role: teacher, student, researcher
- `user_id` (PK) - Unique user identifier
- `display_name` - User display name
- `registered_at` - Registration timestamp

### Courses Table
- `course_id` (PK) - Unique course identifier
- `course_name` - Course title
- `subject` - Subject area
- `grade` - Grade level
- `description` - Course description
- `teacher_id` - Teacher user ID
- `teacher_role` - Teacher role
- `teacher_name` - Teacher display name
- `join_code` - 6-digit join code
- `is_public` - Public visibility flag
- `member_count` - Number of enrolled students
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

### Course Members Table
- `id` (PK) - Auto-increment ID
- `course_id` (FK) - Reference to course
- `user_id` - Student user ID
- `user_role` - Student role
- `display_name` - Student display name
- `joined_at` - Join timestamp

### Lessons Table
- `lesson_id` (PK) - Unique lesson identifier
- `course_id` (FK) - Reference to course
- `title` - Lesson title
- `description` - Lesson description
- `order` - Lesson order in course
- `plan_path` - Path to plan.md file (filesystem storage)
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

### Homework Table
- `hw_id` (PK) - Unique homework identifier
- `course_id` (FK) - Reference to course
- `title` - Homework title
- `description` - Homework description
- `total_points` - Total points
- `deadline` - Submission deadline
- `created_by` - Teacher user ID
- `created_at` - Creation timestamp

### Questions Table
- `id` (PK) - Auto-increment ID
- `hw_id` (FK) - Reference to homework
- `question_id` - Question identifier (e.g., q1, q2)
- `question_type` - Question type
- `content` - Question content
- `points` - Points for this question

### Submissions Table
- `id` (PK) - Auto-increment ID
- `hw_id` (FK) - Reference to homework
- `student_id` - Student user ID
- `student_role` - Student role
- `course_id` (FK) - Reference to course
- `answers` - JSON object with answers
- `status` - Submission status (submitted/graded)
- `score` - Earned score
- `total_score` - Total possible score
- `feedback` - JSON object with feedback
- `submitted_at` - Submission timestamp
- `graded_at` - Grading timestamp
- `graded_by` - Teacher user ID who graded

## Usage with WebSocket Server

The database storage layer is integrated into the WebSocket server. When the server starts, it will:

1. Check if database is configured
2. Initialize database connection if configured
3. Use database for all course and user operations
4. Fall back to file-based storage if database is not configured

## Backup and Restore

### Backup Database

```bash
pg_dump -U nanobot -d nanobot > backup.sql
```

### Restore Database

```bash
psql -U nanobot -d nanobot < backup.sql
```

## Troubleshooting

### Connection Refused

```
sqlalchemy.exc.OperationalError: (asyncpg.exceptions.ConnectionDoesNotExistError)
```

**Solution**: Ensure PostgreSQL is running and accepting connections:
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Start PostgreSQL if needed
sudo systemctl start postgresql
```

### Authentication Failed

```
sqlalchemy.exc.ProgrammingError: (asyncpg.exceptions.InvalidCatalogNameError)
```

**Solution**: Verify database credentials:
```bash
# Test connection
psql -U nanobot -d nanobot -h localhost
```

### Tables Not Created

```bash
# Manually create tables
nanobot migrate-db reset
nanobot migrate-db run
```

## Advanced Configuration

### Connection Pool Settings

Adjust pool settings in config:

```json
{
  "database": {
    "url": "postgresql+asyncpg://nanobot:nanobot@localhost:5432/nanobot",
    "poolSize": 10,
    "maxOverflow": 20
  }
}
```

### SQL Debugging

Enable SQL query logging:

```json
{
  "database": {
    "echo": true
  }
}
```

## Migration from File-based Storage

The migration process is designed to be safe and idempotent:

1. **Non-destructive**: Original files are not modified
2. **Idempotent**: Running migration multiple times won't create duplicates
3. **Incremental**: Only new/changed data is migrated

### Migration Order

Migrations run in dependency order:
1. Users (no dependencies)
2. Courses (depends on users)
3. Course Members (depends on courses)
4. Lessons (depends on courses)
5. Homework (depends on courses)
6. Submissions (depends on homework)

### Verifying Migration

After migration, verify data integrity:

```bash
# Check counts
nanobot migrate-db status

# Query database directly
psql -U nanobot -d nanobot -c "SELECT COUNT(*) FROM users;"
psql -U nanobot -d nanobot -c "SELECT COUNT(*) FROM courses;"
```
