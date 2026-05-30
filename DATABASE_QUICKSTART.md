# Database Quick Start Guide

## 5-Minute Setup

### 1. Start PostgreSQL

```bash
# Using Docker (easiest)
docker-compose -f docker-compose.dev.yml up -d postgres

# Wait for PostgreSQL to be ready
sleep 5
```

### 2. Configure Database

Create or update `~/.nanobot/config.json`:

```json
{
  "database": {
    "url": "postgresql+asyncpg://nanobot:nanobot@localhost:5432/nanobot"
  }
}
```

Or set environment variable:

```bash
export NANOBOT_DATABASE_URL="postgresql+asyncpg://nanobot:nanobot@localhost:5432/nanobot"
```

### 3. Initialize Database

```bash
# Create tables and migrate existing data
nanobot migrate-db run
```

### 4. Verify

```bash
# Check database status
nanobot migrate-db status

# Expected output:
# Database Status:
#   Users: X
#   Courses: Y
```

## Common Commands

```bash
# Run migration (creates tables + migrates data)
nanobot migrate-db run

# Check database status
nanobot migrate-db status

# Reset database (drops all tables - USE WITH CAUTION!)
nanobot migrate-db reset

# Specify custom database URL
nanobot migrate-db run --db-url "postgresql+asyncpg://user:pass@host:port/db"

# Specify custom nanobot directory
nanobot migrate-db run --nanobot-dir /path/to/.nanobot
```

## Using in Code

### DatabaseStorage (Direct Database Access)

```python
from nanobot.config.database import db_manager
from nanobot.storage.database_storage import DatabaseStorage

# Initialize database
await db_manager.initialize()
await db_manager.create_tables()

# Get session and storage
async for session in db_manager.get_session():
    storage = DatabaseStorage(session)
    
    # Create user
    user = await storage.create_user("teacher", "teacher1", "张老师")
    
    # Create course
    course = await storage.create_course({
        "courseId": "course123",
        "courseName": "Python编程基础",
        "subject": "计算机科学",
        "grade": "大一",
        "teacherId": "teacher1",
        "teacherName": "张老师",
        "joinCode": "123456",
    })

# Close connection
await db_manager.close()
```

### StorageWrapper (Unified Interface)

```python
from nanobot.storage.storage_wrapper import StorageWrapper

# With database
wrapper = StorageWrapper(session=session)
user = await wrapper.create_user("teacher", "teacher1", "张老师")

# Without database (file-based)
wrapper = StorageWrapper(nanobot_dir=Path("~/.nanobot"))
user = await wrapper.create_user("teacher", "teacher1", "张老师")
```

## Docker Commands

```bash
# Start PostgreSQL
docker-compose -f docker-compose.dev.yml up -d postgres

# Start PostgreSQL + pgAdmin
docker-compose -f docker-compose.dev.yml --profile admin up -d

# Stop services
docker-compose -f docker-compose.dev.yml down

# View logs
docker-compose -f docker-compose.dev.yml logs -f postgres

# Connect to database
docker exec -it nanobot-postgres psql -U nanobot -d nanobot
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NANOBOT_DATABASE_URL` | `postgresql+asyncpg://nanobot:nanobot@localhost:5432/nanobot` | Database connection URL |
| `NANOBOT_DB_ECHO` | `false` | Enable SQL logging |
| `NANOBOT_DB_POOL_SIZE` | `5` | Connection pool size |
| `NANOBOT_DB_MAX_OVERFLOW` | `10` | Max overflow connections |

## Database Management

### Backup

```bash
# Backup database
docker exec nanobot-postgres pg_dump -U nanobot -d nanobot > backup.sql

# Backup with timestamp
docker exec nanobot-postgres pg_dump -U nanobot -d nanobot > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restore

```bash
# Restore database
docker exec -i nanobot-postgres psql -U nanobot -d nanobot < backup.sql
```

### Query Database

```bash
# Connect to database
docker exec -it nanobot-postgres psql -U nanobot -d nanobot

# List tables
\dt

# Count users
SELECT COUNT(*) FROM users;

# Count courses
SELECT COUNT(*) FROM courses;

# View users
SELECT * FROM users;

# View courses
SELECT course_id, course_name, teacher_name, join_code FROM courses;
```

## Troubleshooting

### Connection Refused

```
Error: Connection refused
```

**Solution**: Ensure PostgreSQL is running

```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Start PostgreSQL if not running
docker-compose -f docker-compose.dev.yml up -d postgres
```

### Authentication Failed

```
Error: authentication failed
```

**Solution**: Check credentials

```bash
# Test connection
docker exec -it nanobot-postgres psql -U nanobot -d nanobot

# If failed, reset password
docker exec -it nanobot-postgres psql -U postgres -c "ALTER USER nanobot PASSWORD 'nanobot';"
```

### Tables Not Found

```
Error: relation "users" does not exist
```

**Solution**: Initialize database

```bash
# Create tables
nanobot migrate-db run

# Or reset and recreate
nanobot migrate-db reset
nanobot migrate-db run
```

## Next Steps

1. **Read the full documentation**: [Database Setup Guide](docs/database-setup.md)
2. **Review the schema**: [Database Schema](DATABASE_MIGRATION.md#database-schema)
3. **Check examples**: [Database Usage Examples](examples/database_usage.py)
4. **Run tests**: `pytest tests/test_models.py tests/test_storage.py`

## Getting Help

- **Documentation**: [docs/database-setup.md](docs/database-setup.md)
- **Examples**: [examples/](examples/)
- **Issues**: GitHub Issues
