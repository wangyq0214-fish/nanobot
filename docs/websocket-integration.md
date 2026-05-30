# WebSocket Integration Guide

This guide explains how to integrate database storage into the WebSocket server.

## Overview

The WebSocket server (`nanobot/channels/websocket.py`) currently uses file-based storage for courses, users, and other data. This guide shows how to integrate database storage while maintaining backward compatibility.

## Integration Steps

### 1. Import Database Dependencies

Add these imports at the top of `websocket.py`:

```python
from nanobot.config.database import db_manager
from nanobot.storage.storage_wrapper import StorageWrapper
```

### 2. Initialize Database in Server Startup

In the `WebSocketChannel.__init__` or startup method:

```python
async def _initialize_database(self):
    """Initialize database connection if configured."""
    try:
        from nanobot.config.schema import Config
        from nanobot.config.loader import load_config
        
        config = load_config()
        if config.database and config.database.url:
            await db_manager.initialize()
            await db_manager.create_tables()
            logger.info("Database initialized successfully")
            return True
    except Exception as e:
        logger.warning("Database initialization failed: {}", e)
    
    return False
```

### 3. Create Storage Wrapper

Modify the storage methods to use `StorageWrapper`:

```python
async def _get_storage(self) -> StorageWrapper:
    """Get storage wrapper instance."""
    if not hasattr(self, '_storage'):
        # Try to get database session
        try:
            session = await db_manager.get_session().__anext__()
            self._storage = StorageWrapper(session=session)
        except Exception:
            # Fallback to file-based storage
            self._storage = StorageWrapper(
                nanobot_dir=Path.home() / ".nanobot"
            )
    return self._storage
```

### 4. Update Storage Methods

Replace file-based storage methods with wrapper calls:

**Before (file-based):**

```python
def _load_users(self) -> dict[str, Any]:
    path = self._users_file
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
```

**After (using wrapper):**

```python
async def _load_users(self) -> dict[str, Any]:
    storage = await self._get_storage()
    # For backward compatibility, return dict format
    # In production, consider returning list of User objects
    return {}
```

### 5. Update HTTP Handlers

Modify HTTP handlers to use async storage:

**Before:**

```python
async def _handle_courses_list(self, path: str, query: dict, headers: dict):
    # ... validation ...
    index = self._load_courses_index()
    courses = list(index.values())
    # ... filtering ...
    return _json_response(courses)
```

**After:**

```python
async def _handle_courses_list(self, path: str, query: dict, headers: dict):
    # ... validation ...
    storage = await self._get_storage()
    role = query.get("role", [None])[0]
    user_id = query.get("user_id", [None])[0]
    
    courses = await storage.list_courses(
        role=role,
        user_id=user_id,
    )
    return _json_response(courses)
```

## Example: Full Integration

Here's a complete example of integrating database into `_handle_courses_create`:

```python
async def _handle_courses_create(self, path: str, query: dict, headers: dict):
    """Handle POST /api/courses/create."""
    # Validate token
    token = _query_first(query, "token")
    if not token or not self._validate_token(token):
        return _http_error(401, "Invalid token")
    
    # Get metadata
    meta = self._token_metadata.get(token, {})
    role = meta.get("role")
    user_id = meta.get("user_id")
    
    if role != "teacher":
        return _http_error(403, "Only teachers can create courses")
    
    # Parse data
    data = self._parse_mutation_data(query)
    if isinstance(data, Response):
        return data
    
    # Generate course ID and join code
    course_id = self._generate_id()
    join_code = self._generate_join_code()
    
    # Prepare course data
    course_data = {
        "courseId": course_id,
        "courseName": data.get("courseName", ""),
        "subject": data.get("subject", ""),
        "grade": data.get("grade", ""),
        "description": data.get("description", ""),
        "teacherId": user_id,
        "teacherName": meta.get("display_name", user_id),
        "joinCode": join_code,
        "isPublic": data.get("isPublic", False),
        "memberCount": 0,
    }
    
    # Use storage wrapper
    storage = await self._get_storage()
    course = await storage.create_course(course_data)
    
    logger.info("Created course: {} - {}", course_id, course_data["courseName"])
    return _json_response(course)
```

## Migration Strategy

### Phase 1: Add Database Support

1. Add database dependencies
2. Create models and storage layer
3. Add database configuration
4. Test database connection

### Phase 2: Dual Storage

1. Add `StorageWrapper` to WebSocket server
2. Use wrapper for new data
3. Keep file-based storage for reading old data
4. Test both storage backends

### Phase 3: Full Migration

1. Migrate existing data to database
2. Update all handlers to use database
3. Remove file-based storage code (optional)
4. Update documentation

## Backward Compatibility

The `StorageWrapper` maintains backward compatibility:

1. **Database available**: Uses database for all operations
2. **Database unavailable**: Falls back to file-based storage
3. **Mixed mode**: Can read from files, write to database

## Testing

### Unit Tests

```python
# Test database storage
async def test_database_storage():
    from nanobot.storage.database_storage import DatabaseStorage
    
    storage = DatabaseStorage(session)
    user = await storage.create_user("teacher", "teacher1", "张老师")
    assert user.user_id == "teacher1"

# Test storage wrapper
async def test_storage_wrapper():
    from nanobot.storage.storage_wrapper import StorageWrapper
    
    wrapper = StorageWrapper(session=session)
    user = await wrapper.create_user("teacher", "teacher1", "张老师")
    assert user["userId"] == "teacher1"
```

### Integration Tests

```python
# Test WebSocket handler with database
async def test_courses_create_with_db():
    # Initialize database
    await db_manager.initialize()
    await db_manager.create_tables()
    
    # Create WebSocket channel
    channel = WebSocketChannel(...)
    
    # Test course creation
    response = await channel._handle_courses_create(
        path="/api/courses/create",
        query={"data": [...]},
        headers={},
    )
    assert response.status == 200
```

## Performance Considerations

### Connection Pooling

Database connections are pooled:

```python
engine = create_async_engine(
    database_url,
    pool_size=5,
    max_overflow=10,
)
```

### Query Optimization

Use efficient queries:

```python
# Good: Filter in database
courses = await session.execute(
    select(Course).where(Course.teacher_id == user_id)
)

# Bad: Filter in Python
all_courses = await session.execute(select(Course))
courses = [c for c in all_courses if c.teacher_id == user_id]
```

### Caching

Consider caching for frequently accessed data:

```python
from functools import lru_cache

@lru_cache(maxsize=100)
async def get_course(course_id: str):
    return await storage.get_course(course_id)
```

## Error Handling

### Database Errors

```python
try:
    course = await storage.create_course(course_data)
except Exception as e:
    logger.error("Failed to create course: {}", e)
    return _http_error(500, "Internal server error")
```

### Fallback Strategy

```python
async def _get_storage(self) -> StorageWrapper:
    try:
        if db_manager.engine:
            session = await db_manager.get_session().__anext__()
            return StorageWrapper(session=session)
    except Exception as e:
        logger.warning("Database unavailable: {}", e)
    
    # Fallback to file storage
    return StorageWrapper(nanobot_dir=Path.home() / ".nanobot")
```

## Monitoring

### Logging

Add logging for database operations:

```python
logger.info("Created course: {} by teacher {}", course_id, user_id)
logger.warning("Database query slow: {}ms", duration)
logger.error("Database connection failed: {}", error)
```

### Metrics

Track database performance:

```python
import time

start = time.time()
course = await storage.get_course(course_id)
duration = (time.time() - start) * 1000

if duration > 100:  # Log slow queries
    logger.warning("Slow query: get_course took {}ms", duration)
```

## Security

### SQL Injection Prevention

SQLAlchemy prevents SQL injection:

```python
# Safe: Parameterized query
course = await session.execute(
    select(Course).where(Course.course_id == course_id)
)

# Unsafe: String concatenation (DON'T DO THIS)
query = f"SELECT * FROM courses WHERE course_id = '{course_id}'"
```

### Input Validation

Validate all inputs:

```python
course_name = data.get("courseName", "").strip()
if not course_name or len(course_name) > 200:
    return _http_error(400, "Invalid course name")
```

### Access Control

Check permissions:

```python
if role != "teacher":
    return _http_error(403, "Only teachers can create courses")

if course.teacher_id != user_id:
    return _http_error(403, "Not your course")
```

## Next Steps

1. **Review examples**: [examples/database_usage.py](../examples/database_usage.py)
2. **Read migration guide**: [DATABASE_MIGRATION.md](../DATABASE_MIGRATION.md)
3. **Check tests**: [tests/test_storage.py](../tests/test_storage.py)
4. **Deploy**: Follow [docs/database-setup.md](database-setup.md)
