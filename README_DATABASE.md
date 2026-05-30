# Nanobot Database Migration

## Overview

This document provides a complete guide to setting up and using PostgreSQL database with nanobot.

## Quick Links

- [Quick Start Guide](DATABASE_QUICKSTART.md) - 5-minute setup
- [Full Documentation](docs/database-setup.md) - Comprehensive setup guide
- [Migration Summary](DATABASE_MIGRATION.md) - Technical details and schema
- [Examples](examples/) - Code examples

## What's Included

### Database Models

- **User** - User accounts (teacher, student, researcher)
- **Course** - Course information and metadata
- **CourseMember** - Course enrollment relationships
- **Lesson** - Lesson metadata
- **Homework** - Homework assignments
- **Question** - Homework questions
- **Submission** - Student homework submissions

### Storage Layer

- **DatabaseStorage** - Direct database operations
- **StorageWrapper** - Unified interface for database and file storage

### Migration Tools

- **CLI Commands** - `nanobot migrate-db run/status/reset`
- **Migration Scripts** - Automated data migration from files to database

### Development Tools

- **Docker Compose** - PostgreSQL setup for development
- **Test Scripts** - Database connection and migration tests
- **Examples** - Usage examples and best practices

## Installation

### 1. Install Dependencies

```bash
pip install -e ".[dev]"
# or
uv sync --all-extras
```

### 2. Start PostgreSQL

```bash
# Using Docker (recommended)
docker-compose -f docker-compose.dev.yml up -d postgres

# Or install PostgreSQL manually
```

### 3. Configure Database

**Option A: Environment Variable**

```bash
export NANOBOT_DATABASE_URL="postgresql+asyncpg://nanobot:nanobot@localhost:5432/nanobot"
```

**Option B: Config File**

Edit `~/.nanobot/config.json`:

```json
{
  "database": {
    "url": "postgresql+asyncpg://nanobot:nanobot@localhost:5432/nanobot"
  }
}
```

### 4. Initialize Database

```bash
# Create tables and migrate existing data
nanobot migrate-db run
```

## Usage

### CLI Commands

```bash
# Run migration
nanobot migrate-db run

# Check status
nanobot migrate-db status

# Reset database (caution!)
nanobot migrate-db reset
```

### Python API

```python
from nanobot.config.database import db_manager
from nanobot.storage.database_storage import DatabaseStorage

# Initialize
await db_manager.initialize()
await db_manager.create_tables()

# Use storage
async for session in db_manager.get_session():
    storage = DatabaseStorage(session)
    
    # Create user
    user = await storage.create_user("teacher", "teacher1", "张老师")
    
    # Create course
    course = await storage.create_course({...})
    
    # Add member
    await storage.add_member(course_id, student_id, display_name)
```

### Storage Wrapper

```python
from nanobot.storage.storage_wrapper import StorageWrapper

# With database
wrapper = StorageWrapper(session=session)
user = await wrapper.create_user(...)

# Without database (file-based)
wrapper = StorageWrapper(nanobot_dir=Path("~/.nanobot"))
user = await wrapper.create_user(...)
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

## Testing

### Run Tests

```bash
# Run all database tests
pytest tests/test_models.py tests/test_storage.py tests/test_migration.py

# Run specific test
pytest tests/test_models.py::TestUser::test_user_creation

# Run with verbose output
pytest -v tests/test_models.py
```

### Test Scripts

```bash
# Check database connection
python scripts/check_db_connection.py

# Run full test suite
python scripts/test_database.py

# Run examples
python examples/simple_database_example.py
```

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
│   └── schema.py
├── migrations/
│   ├── __init__.py
│   └── file_to_db.py
├── cli/
│   └── commands.py
├── examples/
│   ├── config_with_database.json
│   ├── database_usage.py
│   └── simple_database_example.py
├── scripts/
│   ├── setup_dev_db.sh
│   ├── setup_dev_db.ps1
│   ├── check_db_connection.py
│   └── test_database.py
├── tests/
│   ├── test_models.py
│   ├── test_storage.py
│   └── test_migration.py
├── docs/
│   └── database-setup.md
├── docker-compose.dev.yml
├── DATABASE_QUICKSTART.md
├── DATABASE_MIGRATION.md
└── README_DATABASE.md
```

## Documentation

### Quick Start

- [DATABASE_QUICKSTART.md](DATABASE_QUICKSTART.md) - 5-minute setup guide

### Full Documentation

- [docs/database-setup.md](docs/database-setup.md) - Comprehensive setup guide
- [DATABASE_MIGRATION.md](DATABASE_MIGRATION.md) - Technical details and schema

### Examples

- [examples/config_with_database.json](examples/config_with_database.json) - Config example
- [examples/database_usage.py](examples/database_usage.py) - Full usage example
- [examples/simple_database_example.py](examples/simple_database_example.py) - Simple example

### Development

- [docker-compose.dev.yml](docker-compose.dev.yml) - Docker setup
- [scripts/setup_dev_db.sh](scripts/setup_dev_db.sh) - Linux/Mac setup script
- [scripts/setup_dev_db.ps1](scripts/setup_dev_db.ps1) - Windows setup script

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NANOBOT_DATABASE_URL` | `postgresql+asyncpg://nanobot:nanobot@localhost:5432/nanobot` | Database connection URL |
| `NANOBOT_DB_ECHO` | `false` | Enable SQL logging |
| `NANOBOT_DB_POOL_SIZE` | `5` | Connection pool size |
| `NANOBOT_DB_MAX_OVERFLOW` | `10` | Max overflow connections |

## Troubleshooting

### Connection Issues

```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Test connection
docker exec -it nanobot-postgres psql -U nanobot -d nanobot

# Check logs
docker-compose -f docker-compose.dev.yml logs postgres
```

### Migration Issues

```bash
# Reset database
nanobot migrate-db reset

# Run migration again
nanobot migrate-db run

# Check status
nanobot migrate-db status
```

### Common Errors

1. **Connection refused** - PostgreSQL not running
2. **Authentication failed** - Wrong credentials
3. **Tables not found** - Run migration first
4. **Duplicate key** - Data already migrated

## Performance Tips

### Connection Pool

Adjust pool settings in config:

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
- Frequently queried fields
- Unique constraints

### Query Optimization

- Use `selectinload()` for relationships
- Add filters before joins
- Use async sessions for concurrent operations

## Security

### Database Credentials

Use environment variables or secure config:

```bash
export NANOBOT_DATABASE_URL="postgresql+asyncpg://user:password@host:port/db"
```

### Access Control

- Use PostgreSQL roles and permissions
- Limit database user privileges
- Enable SSL for production

### Backup

Regular backups recommended:

```bash
# Backup
docker exec nanobot-postgres pg_dump -U nanobot -d nanobot > backup.sql

# Restore
docker exec -i nanobot-postgres psql -U nanobot -d nanobot < backup.sql
```

## Next Steps

1. **Quick Start** - Follow [DATABASE_QUICKSTART.md](DATABASE_QUICKSTART.md)
2. **Read Docs** - Review [docs/database-setup.md](docs/database-setup.md)
3. **Run Examples** - Try [examples/](examples/)
4. **Run Tests** - Execute `pytest tests/`
5. **Deploy** - Use managed PostgreSQL for production

## Support

- **Documentation** - [docs/](docs/)
- **Examples** - [examples/](examples/)
- **Tests** - [tests/](tests/)
- **Issues** - GitHub Issues

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) for details.
