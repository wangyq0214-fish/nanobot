# 数据库设置脚本

本目录包含数据库设置和测试脚本。

## 脚本说明

### 1. test_connection.py - 测试数据库连接

测试 PostgreSQL 数据库连接是否正常。

**使用方法：**

```bash
python scripts/test_connection.py
```

**输出示例：**

```
============================================================
数据库连接测试
============================================================
测试数据库连接...
数据库 URL: postgresql+asyncpg://nanobot:nanobot@localhost:5432/nanobot
PostgreSQL 版本: PostgreSQL 16.3 on x86_64-pc-linux-gnu, compiled by gcc (GCC) 13.2.0, 64-bit
当前数据库: nanobot
当前用户: nanobot
当前连接数: 5
✓ 数据库连接成功

============================================================
✓ 数据库连接测试通过
============================================================
```

### 2. setup_database.py - 设置数据库

连接数据库并创建所有表和索引。

**使用方法：**

```bash
python scripts/setup_database.py
```

**输出示例：**

```
============================================================
数据库设置
============================================================
数据库 URL: postgresql+asyncpg://nanobot:nanobot@localhost:5432/nanobot
测试数据库连接...
✓ 数据库连接成功
创建数据库表...
  创建表 1/12: users
  创建表 2/12: courses
  创建表 3/12: course_members
  创建表 4/12: teacher_lessons
  创建表 5/12: course_lessons
  创建表 6/12: homework
  创建表 7/12: questions
  创建表 8/12: submissions
  创建表 9/12: course_resources
  创建表 10/12: learning_progress
  创建表 11/12: notifications
  创建表 12/12: audit_logs
✓ 成功创建 12 个表
创建索引...
  创建索引 1/30: idx_users_display_name
  创建索引 2/30: idx_users_registered_at
  ...
✓ 成功创建 30 个索引
验证表...
数据库中的表 (12 个):
  - audit_logs
  - course_lessons
  - course_members
  - course_resources
  - courses
  - homework
  - learning_progress
  - notifications
  - questions
  - submissions
  - teacher_lessons
  - users
✓ 所有必需的表都已创建

============================================================
✓ 数据库设置完成！
============================================================
```

## 前置条件

### 1. 安装 PostgreSQL

**Windows:**

```bash
# 使用 Chocolatey
choco install postgresql

# 或者下载安装包
# https://www.postgresql.org/download/windows/
```

**macOS:**

```bash
# 使用 Homebrew
brew install postgresql
brew services start postgresql
```

**Linux (Ubuntu):**

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 2. 创建数据库和用户

连接到 PostgreSQL：

```bash
# 使用 psql
psql -U postgres
```

创建数据库和用户：

```sql
-- 创建用户
CREATE USER nanobot WITH PASSWORD 'nanobot';

-- 创建数据库
CREATE DATABASE nanobot OWNER nanobot;

-- 授权
GRANT ALL PRIVILEGES ON DATABASE nanobot TO nanobot;

-- 退出
\q
```

### 3. 安装 Python 依赖

```bash
pip install sqlalchemy asyncpg loguru
```

## 配置数据库连接

### 方法1：修改脚本中的 DATABASE_URL

编辑 `test_connection.py` 和 `setup_database.py`：

```python
# 数据库配置
DATABASE_URL = "postgresql+asyncpg://用户名:密码@主机:端口/数据库名"
```

**示例：**

```python
# 本地数据库
DATABASE_URL = "postgresql+asyncpg://nanobot:nanobot@localhost:5432/nanobot"

# 远程数据库
DATABASE_URL = "postgresql+asyncpg://user:pass@remote-host:5432/mydb"

# 带 SSL
DATABASE_URL = "postgresql+asyncpg://user:pass@host:5432/db?ssl=require"
```

### 方法2：使用环境变量

```bash
# 设置环境变量
export DATABASE_URL="postgresql+asyncpg://nanobot:nanobot@localhost:5432/nanobot"

# 运行脚本
python scripts/test_connection.py
```

## 故障排除

### 1. 连接失败

**错误：**

```
asyncpg.exceptions.InvalidCatalogNameError: database "nanobot" does not exist
```

**解决：**

```bash
# 创建数据库
psql -U postgres -c "CREATE DATABASE nanobot;"
```

### 2. 认证失败

**错误：**

```
asyncpg.exceptions.InvalidAuthorizationSpecificationError: password authentication failed for user "nanobot"
```

**解决：**

```bash
# 重置密码
psql -U postgres -c "ALTER USER nanobot WITH PASSWORD 'nanobot';"
```

### 3. 连接被拒绝

**错误：**

```
asyncpg.exceptions.ConnectionDoesNotExistError: connection was closed
```

**解决：**

```bash
# 检查 PostgreSQL 是否运行
sudo systemctl status postgresql

# 启动 PostgreSQL
sudo systemctl start postgresql

# 检查端口
netstat -tlnp | grep 5432
```

### 4. 权限不足

**错误：**

```
asyncpg.exceptions.InsufficientPrivilegeError: permission denied for table users
```

**解决：**

```bash
# 授权
psql -U postgres -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO nanobot;"
psql -U postgres -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO nanobot;"
```

## 高级配置

### 1. 使用 Docker

```bash
# 启动 PostgreSQL
docker run -d \
  --name nanobot-postgres \
  -e POSTGRES_USER=nanobot \
  -e POSTGRES_PASSWORD=nanobot \
  -e POSTGRES_DB=nanobot \
  -p 5432:5432 \
  postgres:16

# 等待启动
sleep 5

# 测试连接
python scripts/test_connection.py
```

### 2. 使用 Docker Compose

创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16
    container_name: nanobot-postgres
    environment:
      POSTGRES_USER: nanobot
      POSTGRES_PASSWORD: nanobot
      POSTGRES_DB: nanobot
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

启动：

```bash
docker-compose up -d

# 等待启动
sleep 5

# 测试连接
python scripts/test_connection.py
```

### 3. 修改 PostgreSQL 配置

编辑 `postgresql.conf`：

```ini
# 监听地址
listen_addresses = '*'

# 最大连接数
max_connections = 100

# 共享内存
shared_buffers = 256MB
```

编辑 `pg_hba.conf`：

```ini
# 允许本地连接
local   all   all                 trust
host    all   all   127.0.0.1/32  trust
host    all   all   ::1/128       trust
```

重启 PostgreSQL：

```bash
sudo systemctl restart postgresql
```

## 下一步

数据库设置完成后，可以：

1. **运行迁移脚本** - 将现有数据迁移到数据库
2. **修改 websocket.py** - 使用数据库存储
3. **测试 API** - 验证数据库功能

## 相关文档

- [数据库表结构设计](../docs/数据库表结构设计.md)
- [数据库设计文档](../docs/database-design.md)
- [数据库迁移指南](../DATABASE_MIGRATION.md)
- [快速入门](../DATABASE_QUICKSTART.md)
