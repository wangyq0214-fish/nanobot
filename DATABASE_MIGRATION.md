# Database Migration Summary

This document summarizes the database migration implementation for nanobot.

## Overview

The migration introduces PostgreSQL database support for persistent storage, replacing the file-based JSON storage for structured data (users, courses, homework, submissions). The migration is **gradual** and **non-destructive** - existing file-based storage continues to work.

## Key Components

### 1. Database Models (`nanobot/models/`)

SQLAlchemy models for all entities:

- **User** - User accounts (teacher, student, researcher)
- **Course** - Course information and metadata
- **CourseMember** - Course enrollment relationships
- **Lesson** - Lesson metadata (plan.md remains on filesystem)
- **Homework** - Homework assignments
- **Question** - Homework questions
- **Submission** - Student homework submissions

### 2. Database Configuration (`nanobot/config/database.py`)

- `DatabaseManager` - Manages database connections and sessions
- `get_database_url()` - Gets URL from environment or config
- `get_database_config()` - Loads config from file or environment

### 3. Storage Layer (`nanobot/storage/`)

- **DatabaseStorage** - Direct database operations using SQLAlchemy
- **StorageWrapper** - Unified interface that can use database or file-based storage

### 4. Migration Scripts (`nanobot/migrations/`)

- `file_to_db.py` - Migrates data from file-based storage to database

### 5. CLI Commands (`nanobot/cli/commands.py`)

- `migrate-db run` - Run migration from files to database
- `migrate-db status` - Check database status
- `migrate-db reset` - Reset database (drops all tables)

## File Structure

```
nanobot/
├── models/
│   ├── __init__.py
│   ├── user.py
│   ├── course.py
│   ├── lesson.py
│   ├── homework.py
│   └── submission.py
├── storage/
│   ├── __init__.py
│   ├── database_storage.py
│   └── storage_wrapper.py
├── config/
│   ├── database.py
│   └── schema.py (updated with DatabaseConfig)
├── migrations/
│   ├── __init__.py
│   └── file_to_db.py
├── cli/
│   └── commands.py (updated with migrate-db command)
├── examples/
│   ├── config_with_database.json
│   └── database_usage.py
├── scripts/
│   ├── setup_dev_db.sh
│   ├── setup_dev_db.ps1
│   └── test_database.py
└── docs/
    └── database-setup.md
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -e ".[dev]"
# or
uv sync --all-extras
```

### 2. Start PostgreSQL

```bash
# Using Docker (recommended for development)
docker-compose -f docker-compose.dev.yml up -d postgres

# Or use existing PostgreSQL installation
```

### 3. Configure Database

**Option A: Environment Variable**

```bash
export NANOBOT_DATABASE_URL="postgresql+asyncpg://nanobot:nanobot@localhost:5432/nanobot"
```

**Option B: Config File**

Add to `~/.nanobot/config.json`:

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

### 4. Initialize Database

```bash
# Create tables
nanobot migrate-db run

# Migrate existing data (if any)
nanobot migrate-db run --nanobot-dir ~/.nanobot
```

### 5. Verify

```bash
# Check status
nanobot migrate-db status

# Run test script
python scripts/test_database.py
```

## Database Schema

### Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│    Users    │       │   Courses   │       │   Lessons   │
├─────────────┤       ├─────────────┤       ├─────────────┤
│ PK: role    │←─┐    │ PK: course  │←──────│ FK: course  │
│ PK: user_id │  │    │     _id     │       │ PK: lesson  │
│ display_name│  │    │ course_name │       │     _id     │
│ registered  │  │    │ subject     │       │ title       │
│     _at     │  │    │ grade       │       │ description │
└─────────────┘  │    │ description │       │ order       │
                 │    │ FK: teacher │       │ plan_path   │
                 │    │     _id     │       └─────────────┘
                 │    │ join_code   │
                 │    │ is_public   │
                 │    │ member_count│
                 │    └─────────────┘
                 │            │
                 │            ▼
                 │    ┌─────────────┐       ┌─────────────┐
                 │    │CourseMembers│       │  Homework   │
                 │    ├─────────────┤       ├─────────────┤
                 │    │ FK: course  │       │ PK: hw_id   │
                 ├───→│     _id     │       │ FK: course  │
                 │    │ FK: user_id │       │     _id     │
                 │    │ display_name│       │ title       │
                 │    │ joined_at   │       │ description │
                 │    └─────────────┘       │ total_points│
                 │                          │ deadline    │
                 │                          │ created_by  │
                 │                          └─────────────┘
                 │                                  │
                 │                                  ▼
                 │                          ┌─────────────┐
                 │                          │  Questions  │
                 │                          ├─────────────┤
                 │                          │ FK: hw_id   │
                 │                          │ question_id │
                 │                          │ type        │
                 │                          │ content     │
                 │                          │ points      │
                 │                          └─────────────┘
                 │
                 │                          ┌─────────────┐
                 │                          │ Submissions │
                 └─────────────────────────→├─────────────┤
                                            │ FK: hw_id   │
                                            │ FK: user_id │
                                            │ FK: course  │
                                            │     _id     │
                                            │ answers     │
                                            │ status      │
                                            │ score       │
                                            │ feedback    │
                                            │ submitted_at│
                                            │ graded_at   │
                                            │ graded_by   │
                                            └─────────────┘
```

## Migration Strategy

### Phase 1: Core Tables (Current)

- Users
- Courses
- Course Members
- Lessons
- Homework
- Questions
- Submissions

### Phase 2: Future Enhancements

- Chat sessions (currently JSONL files)
- User memory/history
- Analytics data

## Backward Compatibility

The migration maintains full backward compatibility:

1. **File-based storage still works** - If database is not configured, nanobot uses file storage
2. **StorageWrapper abstraction** - Unified interface for both storage backends
3. **Non-destructive migration** - Original files are not modified
4. **Idempotent operations** - Running migration multiple times is safe

## Testing

### Unit Tests

```bash
pytest tests/test_database.py
```

### Integration Tests

```bash
python scripts/test_database.py
```

### Manual Testing

```bash
# Start database
docker-compose -f docker-compose.dev.yml up -d postgres

# Run migration
nanobot migrate-db run

# Check status
nanobot migrate-db status

# Query database directly
psql -U nanobot -d nanobot -c "SELECT * FROM users;"
```

## Troubleshooting

### Common Issues

1. **Connection refused**
   - Ensure PostgreSQL is running
   - Check connection URL and credentials

2. **Tables not created**
   - Run `nanobot migrate-db reset` then `nanobot migrate-db run`

3. **Migration fails**
   - Check logs for specific error
   - Verify data format in JSON files

### Debug Mode

Enable SQL logging in config:

```json
{
  "database": {
    "echo": true
  }
}
```

## Performance Considerations

### Connection Pool

Default pool settings:
- `pool_size`: 5 connections
- `max_overflow`: 10 additional connections

Adjust based on your workload:

```json
{
  "database": {
    "poolSize": 10,
    "maxOverflow": 20
  }
}
```

### Indexes

The models include indexes on:
- Foreign keys
- Frequently queried fields (user_id, course_id)
- Unique constraints (join_code)

## Security Notes

1. **Database credentials** - Use environment variables or secure config
2. **Connection encryption** - Enable SSL for production
3. **Access control** - Use PostgreSQL roles and permissions
4. **Backup** - Regular database backups recommended

## Next Steps

After successful migration:

1. **Verify data integrity** - Check all entities migrated correctly
2. **Test API endpoints** - Ensure all course/user operations work
3. **Monitor performance** - Check query performance and connection usage
4. **Set up backups** - Configure automated database backups
5. **Production deployment** - Use managed PostgreSQL service

## References

- [Database Setup Guide](docs/database-setup.md)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [asyncpg Documentation](https://magicstack.github.io/asyncpg/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
