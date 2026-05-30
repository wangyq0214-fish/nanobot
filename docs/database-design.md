# 数据库详细设计文档

## 目录

1. [概述](#1-概述)
2. [设计原则](#2-设计原则)
3. [数据库选型](#3-数据库选型)
4. [表结构设计](#4-表结构设计)
5. [关系设计](#5-关系设计)
6. [索引策略](#6-索引策略)
7. [数据类型说明](#7-数据类型说明)
8. [扩展性设计](#8-扩展性设计)
9. [数据迁移策略](#9-数据迁移策略)
10. [性能考虑](#10-性能考虑)
11. [安全考虑](#11-安全考虑)
12. [备份和恢复](#12-备份和恢复)
13. [监控和维护](#13-监控和维护)

---

## 1. 概述

### 1.1 项目背景

nanobot 是一个轻量级 AI Agent 框架，支持多角色（教师、学生、研究者）的教育平台。随着功能扩展，原有文件系统存储已无法满足需求，需要迁移到数据库存储。

### 1.2 设计目标

- **数据完整性**：确保数据一致性和完整性
- **可扩展性**：支持未来功能扩展
- **高性能**：满足并发访问需求
- **易维护**：简化数据管理和维护
- **安全性**：保护敏感数据

### 1.3 数据规模预估

| 实体 | 预估数据量 | 增长趋势 |
|------|-----------|----------|
| 用户 | 1,000 - 10,000 | 低 |
| 课程 | 100 - 1,000 | 中 |
| 课时 | 1,000 - 10,000 | 中 |
| 作业 | 500 - 5,000 | 中 |
| 提交 | 10,000 - 100,000 | 高 |

---

## 2. 设计原则

### 2.1 范式化设计

采用第三范式（3NF）设计，减少数据冗余：

- 每个实体有唯一主键
- 非主键字段完全依赖于主键
- 消除传递依赖

### 2.2 命名规范

- **表名**：小写复数形式（如 `users`, `courses`）
- **字段名**：小写下划线分隔（如 `user_id`, `course_name`）
- **主键**：`id` 或 `{entity}_id`
- **外键**：`{referenced_table}_id`
- **索引**：`idx_{table}_{field}`
- **唯一约束**：`uq_{table}_{field}`

### 2.3 数据类型选择

- 优先使用原生类型（如 `INTEGER` 而非 `VARCHAR` 存储数字）
- 使用 `TIMESTAMP WITH TIME ZONE` 存储时间
- 使用 `JSONB` 存储灵活结构数据
- 使用 `TEXT` 存储大文本

### 2.4 约束设计

- 主键约束：每个表必须有主键
- 外键约束：维护引用完整性
- 唯一约束：确保业务唯一性
- 非空约束：确保必填字段
- 检查约束：验证数据有效性

---

## 3. 数据库选型

### 3.1 PostgreSQL 优势

| 特性 | 说明 |
|------|------|
| **JSONB 支持** | 原生 JSON 存储和查询 |
| **全文搜索** | 内置文本搜索功能 |
| **扩展性** | 支持自定义类型和函数 |
| **并发性能** | MVCC 机制，高并发支持 |
| **数据完整性** | 强大的约束系统 |
| **社区活跃** | 丰富的生态和文档 |

### 3.2 版本选择

- **推荐版本**：PostgreSQL 16+
- **最低版本**：PostgreSQL 14+

### 3.3 配置建议

```ini
# postgresql.conf

# 连接配置
max_connections = 100
superuser_reserved_connections = 3

# 内存配置
shared_buffers = 256MB
effective_cache_size = 768MB
work_mem = 4MB
maintenance_work_mem = 64MB

# WAL 配置
wal_buffers = 16MB
checkpoint_completion_target = 0.9

# 日志配置
log_min_duration_statement = 1000
log_checkpoints = on
log_connections = on
log_disconnections = on
```

---

## 4. 表结构设计

### 4.1 用户表 (users)

```sql
CREATE TABLE users (
    -- 主键
    role VARCHAR(20) NOT NULL,
    user_id VARCHAR(64) NOT NULL,
    
    -- 基本信息
    display_name VARCHAR(100) NOT NULL,
    
    -- 扩展信息（JSONB）
    profile JSONB DEFAULT '{}',
    /*
    profile 示例：
    {
        "avatar": "https://...",
        "bio": "用户简介",
        "phone": "13800138000",
        "email": "user@example.com"
    }
    */
    
    -- 用户设置（JSONB）
    settings JSONB DEFAULT '{}',
    /*
    settings 示例：
    {
        "theme": "light",
        "language": "zh-CN",
        "notifications": true
    }
    */
    
    -- 时间戳
    registered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 约束
    CONSTRAINT pk_users PRIMARY KEY (role, user_id),
    CONSTRAINT chk_user_role CHECK (role IN ('teacher', 'student', 'researcher')),
    CONSTRAINT chk_user_id_length CHECK (LENGTH(user_id) >= 1 AND LENGTH(user_id) <= 64)
);

-- 索引
CREATE INDEX idx_users_display_name ON users(display_name);
CREATE INDEX idx_users_registered_at ON users(registered_at);
CREATE INDEX idx_users_profile ON users USING GIN (profile);
```

**字段说明：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `role` | VARCHAR(20) | ✓ | 用户角色：teacher/student/researcher |
| `user_id` | VARCHAR(64) | ✓ | 用户唯一标识 |
| `display_name` | VARCHAR(100) | ✓ | 显示名称 |
| `profile` | JSONB | ✗ | 扩展信息（头像、简介等） |
| `settings` | JSONB | ✗ | 用户设置 |
| `registered_at` | TIMESTAMPTZ | ✓ | 注册时间 |
| `updated_at` | TIMESTAMPTZ | ✓ | 更新时间 |

### 4.2 课程表 (courses)

```sql
CREATE TABLE courses (
    -- 主键
    course_id VARCHAR(12) NOT NULL,
    
    -- 基本信息
    course_name VARCHAR(200) NOT NULL,
    subject VARCHAR(50) NOT NULL,
    grade VARCHAR(20) NOT NULL,
    description TEXT,
    
    -- 教师信息
    teacher_id VARCHAR(64) NOT NULL,
    teacher_role VARCHAR(20) NOT NULL DEFAULT 'teacher',
    teacher_name VARCHAR(100) NOT NULL,
    
    -- 课程设置
    join_code VARCHAR(6) NOT NULL,
    is_public BOOLEAN DEFAULT FALSE,
    member_count INTEGER DEFAULT 0,
    
    -- 扩展数据（JSONB）
    metadata JSONB DEFAULT '{}',
    /*
    metadata 示例：
    {
        "tags": ["Python", "编程"],
        "cover": "https://...",
        "syllabus": "课程大纲",
        "max_students": 50
    }
    */
    
    -- 课程设置（JSONB）
    settings JSONB DEFAULT '{}',
    /*
    settings 示例：
    {
        "allow_late_submission": true,
        "late_penalty_percent": 10,
        "auto_grade": false,
        "show_answers": false
    }
    */
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 约束
    CONSTRAINT pk_courses PRIMARY KEY (course_id),
    CONSTRAINT fk_courses_teacher FOREIGN KEY (teacher_id, teacher_role) 
        REFERENCES users(user_id, role) ON DELETE CASCADE,
    CONSTRAINT uq_courses_join_code UNIQUE (join_code),
    CONSTRAINT chk_courses_subject CHECK (subject IN (
        '农学', '园艺', '植物保护', '土壤肥料', 
        '智慧农业', '畜牧兽医', '食品科学', '农业经济'
    )),
    CONSTRAINT chk_courses_grade CHECK (grade IN (
        '大一', '大二', '大三', '大四', 
        '研一', '研二'
    )),
    CONSTRAINT chk_courses_member_count CHECK (member_count >= 0)
);

-- 索引
CREATE INDEX idx_courses_teacher ON courses(teacher_id, teacher_role);
CREATE INDEX idx_courses_subject ON courses(subject);
CREATE INDEX idx_courses_grade ON courses(grade);
CREATE INDEX idx_courses_is_public ON courses(is_public);
CREATE INDEX idx_courses_created_at ON courses(created_at);
CREATE INDEX idx_courses_metadata ON courses USING GIN (metadata);
```

**字段说明：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `course_id` | VARCHAR(12) | ✓ | 课程唯一标识 |
| `course_name` | VARCHAR(200) | ✓ | 课程名称 |
| `subject` | VARCHAR(50) | ✓ | 学科 |
| `grade` | VARCHAR(20) | ✓ | 年级 |
| `description` | TEXT | ✗ | 课程描述 |
| `teacher_id` | VARCHAR(64) | ✓ | 教师ID |
| `teacher_role` | VARCHAR(20) | ✓ | 教师角色 |
| `teacher_name` | VARCHAR(100) | ✓ | 教师姓名 |
| `join_code` | VARCHAR(6) | ✓ | 加入码 |
| `is_public` | BOOLEAN | ✓ | 是否公开 |
| `member_count` | INTEGER | ✓ | 成员数量 |
| `metadata` | JSONB | ✗ | 扩展数据 |
| `settings` | JSONB | ✗ | 课程设置 |
| `created_at` | TIMESTAMPTZ | ✓ | 创建时间 |
| `updated_at` | TIMESTAMPTZ | ✓ | 更新时间 |

### 4.3 课程成员表 (course_members)

```sql
CREATE TABLE course_members (
    -- 主键
    id SERIAL NOT NULL,
    
    -- 关联信息
    course_id VARCHAR(12) NOT NULL,
    user_id VARCHAR(64) NOT NULL,
    user_role VARCHAR(20) NOT NULL DEFAULT 'student',
    
    -- 成员信息
    display_name VARCHAR(100) NOT NULL,
    
    -- 扩展数据（JSONB）
    metadata JSONB DEFAULT '{}',
    /*
    metadata 示例：
    {
        "progress": 75,
        "last_accessed": "2026-05-30T10:00:00Z",
        "notes": "学生备注"
    }
    */
    
    -- 时间戳
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 约束
    CONSTRAINT pk_course_members PRIMARY KEY (id),
    CONSTRAINT fk_course_members_course FOREIGN KEY (course_id) 
        REFERENCES courses(course_id) ON DELETE CASCADE,
    CONSTRAINT fk_course_members_user FOREIGN KEY (user_id, user_role) 
        REFERENCES users(user_id, role) ON DELETE CASCADE,
    CONSTRAINT uq_course_member UNIQUE (course_id, user_id, user_role)
);

-- 索引
CREATE INDEX idx_course_members_course ON course_members(course_id);
CREATE INDEX idx_course_members_user ON course_members(user_id, user_role);
CREATE INDEX idx_course_members_joined_at ON course_members(joined_at);
```

**字段说明：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | SERIAL | ✓ | 自增主键 |
| `course_id` | VARCHAR(12) | ✓ | 课程ID |
| `user_id` | VARCHAR(64) | ✓ | 用户ID |
| `user_role` | VARCHAR(20) | ✓ | 用户角色 |
| `display_name` | VARCHAR(100) | ✓ | 显示名称 |
| `metadata` | JSONB | ✗ | 扩展数据 |
| `joined_at` | TIMESTAMPTZ | ✓ | 加入时间 |

### 4.4 课时表 (lessons)

```sql
CREATE TABLE lessons (
    -- 主键
    lesson_id VARCHAR(12) NOT NULL,
    
    -- 关联信息
    course_id VARCHAR(12) NOT NULL,
    
    -- 基本信息
    title VARCHAR(200) NOT NULL,
    description TEXT,
    "order" INTEGER DEFAULT 0,
    
    -- 内容信息
    content_type VARCHAR(20) DEFAULT 'markdown',
    content TEXT,
    content_hash VARCHAR(64),
    
    -- 扩展数据（JSONB）
    metadata JSONB DEFAULT '{}',
    /*
    metadata 示例：
    {
        "duration": 45,
        "objectives": ["学习Python基础", "掌握变量类型"],
        "resources": [
            {"type": "video", "url": "https://..."},
            {"type": "pdf", "url": "https://..."}
        ]
    }
    */
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 约束
    CONSTRAINT pk_lessons PRIMARY KEY (lesson_id),
    CONSTRAINT fk_lessons_course FOREIGN KEY (course_id) 
        REFERENCES courses(course_id) ON DELETE CASCADE,
    CONSTRAINT chk_lessons_content_type CHECK (content_type IN (
        'markdown', 'html', 'video', 'pdf', 'interactive'
    )),
    CONSTRAINT chk_lessons_order CHECK ("order" >= 0)
);

-- 索引
CREATE INDEX idx_lessons_course ON lessons(course_id);
CREATE INDEX idx_lessons_order ON lessons(course_id, "order");
CREATE INDEX idx_lessons_content_type ON lessons(content_type);
CREATE INDEX idx_lessons_content_hash ON lessons(content_hash);
CREATE INDEX idx_lessons_metadata ON lessons USING GIN (metadata);
```

**字段说明：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `lesson_id` | VARCHAR(12) | ✓ | 课时唯一标识 |
| `course_id` | VARCHAR(12) | ✓ | 课程ID |
| `title` | VARCHAR(200) | ✓ | 课时标题 |
| `description` | TEXT | ✗ | 课时描述 |
| `order` | INTEGER | ✓ | 排序顺序 |
| `content_type` | VARCHAR(20) | ✓ | 内容类型 |
| `content` | TEXT | ✗ | 课时内容 |
| `content_hash` | VARCHAR(64) | ✗ | 内容哈希 |
| `metadata` | JSONB | ✗ | 扩展数据 |
| `created_at` | TIMESTAMPTZ | ✓ | 创建时间 |
| `updated_at` | TIMESTAMPTZ | ✓ | 更新时间 |

### 4.5 作业表 (homework)

```sql
CREATE TABLE homework (
    -- 主键
    hw_id VARCHAR(15) NOT NULL,
    
    -- 关联信息
    course_id VARCHAR(12) NOT NULL,
    
    -- 基本信息
    title VARCHAR(200) NOT NULL,
    description TEXT,
    total_points INTEGER DEFAULT 0,
    
    -- 时间设置
    deadline TIMESTAMP WITH TIME ZONE,
    
    -- 创建者信息
    created_by VARCHAR(64) NOT NULL,
    
    -- 题目信息（JSONB）
    questions JSONB DEFAULT '[]',
    /*
    questions 示例：
    [
        {
            "id": "q1",
            "type": "short_answer",
            "content": "Python是什么类型的编程语言？",
            "points": 20,
            "options": null,
            "answer": "解释型编程语言"
        },
        {
            "id": "q2",
            "type": "multiple_choice",
            "content": "以下哪个是Python的特点？",
            "points": 10,
            "options": ["A. 编译型", "B. 解释型", "C. 汇编型", "D. 机器语言"],
            "answer": "B"
        },
        {
            "id": "q3",
            "type": "code",
            "content": "写一个Hello World程序",
            "points": 30,
            "answer": "print('Hello World')",
            "test_cases": [
                {"input": "", "output": "Hello World"}
            ]
        }
    ]
    */
    
    -- 作业设置（JSONB）
    settings JSONB DEFAULT '{}',
    /*
    settings 示例：
    {
        "allow_multiple_attempts": true,
        "max_attempts": 3,
        "show_correct_answers": false,
        "time_limit": 60,
        "shuffle_questions": false,
        "proctoring": false
    }
    */
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 约束
    CONSTRAINT pk_homework PRIMARY KEY (hw_id),
    CONSTRAINT fk_homework_course FOREIGN KEY (course_id) 
        REFERENCES courses(course_id) ON DELETE CASCADE,
    CONSTRAINT chk_homework_total_points CHECK (total_points >= 0)
);

-- 索引
CREATE INDEX idx_homework_course ON homework(course_id);
CREATE INDEX idx_homework_created_by ON homework(created_by);
CREATE INDEX idx_homework_deadline ON homework(deadline);
CREATE INDEX idx_homework_created_at ON homework(created_at);
CREATE INDEX idx_homework_questions ON homework USING GIN (questions);
```

**字段说明：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `hw_id` | VARCHAR(15) | ✓ | 作业唯一标识 |
| `course_id` | VARCHAR(12) | ✓ | 课程ID |
| `title` | VARCHAR(200) | ✓ | 作业标题 |
| `description` | TEXT | ✗ | 作业描述 |
| `total_points` | INTEGER | ✓ | 总分 |
| `deadline` | TIMESTAMPTZ | ✗ | 截止时间 |
| `created_by` | VARCHAR(64) | ✓ | 创建者ID |
| `questions` | JSONB | ✓ | 题目列表 |
| `settings` | JSONB | ✗ | 作业设置 |
| `created_at` | TIMESTAMPTZ | ✓ | 创建时间 |

### 4.6 提交表 (submissions)

```sql
CREATE TABLE submissions (
    -- 主键
    id SERIAL NOT NULL,
    
    -- 关联信息
    hw_id VARCHAR(15) NOT NULL,
    student_id VARCHAR(64) NOT NULL,
    student_role VARCHAR(20) NOT NULL DEFAULT 'student',
    course_id VARCHAR(12) NOT NULL,
    
    -- 提交信息
    attempt_number INTEGER DEFAULT 1,
    
    -- 答案信息（JSONB）
    answers JSONB DEFAULT '{}',
    /*
    answers 示例：
    {
        "q1": "Python是解释型编程语言",
        "q2": "B",
        "q3": "print('Hello World')"
    }
    */
    
    -- 评分信息
    status VARCHAR(20) DEFAULT 'submitted',
    score INTEGER DEFAULT 0,
    
    -- 反馈信息（JSONB）
    feedback JSONB DEFAULT '{}',
    /*
    feedback 示例：
    {
        "q1": {"score": 18, "comment": "基本正确"},
        "q2": {"score": 10, "comment": "正确"},
        "q3": {"score": 25, "comment": "缺少注释"},
        "overall": "作业完成良好"
    }
    */
    
    -- 时间戳
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    graded_at TIMESTAMP WITH TIME ZONE,
    graded_by VARCHAR(64),
    
    -- 约束
    CONSTRAINT pk_submissions PRIMARY KEY (id),
    CONSTRAINT fk_submissions_homework FOREIGN KEY (hw_id) 
        REFERENCES homework(hw_id) ON DELETE CASCADE,
    CONSTRAINT fk_submissions_student FOREIGN KEY (student_id, student_role) 
        REFERENCES users(user_id, role) ON DELETE CASCADE,
    CONSTRAINT fk_submissions_course FOREIGN KEY (course_id) 
        REFERENCES courses(course_id) ON DELETE CASCADE,
    CONSTRAINT chk_submissions_status CHECK (status IN (
        'submitted', 'grading', 'graded', 'returned'
    )),
    CONSTRAINT chk_submissions_score CHECK (score >= 0),
    CONSTRAINT chk_submissions_attempt CHECK (attempt_number >= 1)
);

-- 索引
CREATE INDEX idx_submissions_homework ON submissions(hw_id);
CREATE INDEX idx_submissions_student ON submissions(student_id, student_role);
CREATE INDEX idx_submissions_course ON submissions(course_id);
CREATE INDEX idx_submissions_status ON submissions(status);
CREATE INDEX idx_submissions_submitted_at ON submissions(submitted_at);
CREATE INDEX idx_submissions_graded_at ON submissions(graded_at);
CREATE INDEX idx_submissions_answers ON submissions USING GIN (answers);
CREATE INDEX idx_submissions_feedback ON submissions USING GIN (feedback);

-- 唯一约束：每个学生每个作业每次尝试只能提交一次
CREATE UNIQUE INDEX uq_submission_attempt 
    ON submissions(hw_id, student_id, attempt_number);
```

**字段说明：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | SERIAL | ✓ | 自增主键 |
| `hw_id` | VARCHAR(15) | ✓ | 作业ID |
| `student_id` | VARCHAR(64) | ✓ | 学生ID |
| `student_role` | VARCHAR(20) | ✓ | 学生角色 |
| `course_id` | VARCHAR(12) | ✓ | 课程ID |
| `attempt_number` | INTEGER | ✓ | 尝试次数 |
| `answers` | JSONB | ✓ | 答案 |
| `status` | VARCHAR(20) | ✓ | 状态 |
| `score` | INTEGER | ✓ | 分数 |
| `feedback` | JSONB | ✗ | 反馈 |
| `submitted_at` | TIMESTAMPTZ | ✓ | 提交时间 |
| `graded_at` | TIMESTAMPTZ | ✗ | 批改时间 |
| `graded_by` | VARCHAR(64) | ✗ | 批改者ID |

---

## 5. 关系设计

### 5.1 ER 图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                  用户表                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  users (role, user_id)                                               │  │
│  │  ├── display_name                                                    │  │
│  │  ├── profile (JSONB)                                                 │  │
│  │  └── settings (JSONB)                                                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                    │                    │                    │
                    │ 1:N                │ 1:N                │ 1:N
                    ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                课程表                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  courses (course_id)                                                 │  │
│  │  ├── teacher_id, teacher_role → users                                │  │
│  │  ├── course_name, subject, grade                                     │  │
│  │  ├── join_code (UNIQUE)                                              │  │
│  │  └── metadata, settings (JSONB)                                      │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                    │                    │                    │
                    │ 1:N                │ 1:N                │ 1:N
                    ▼                    ▼                    ▼
┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
│    课程成员表         │  │      课时表           │  │      作业表           │
│  ┌────────────────┐  │  │  ┌────────────────┐  │  │  ┌────────────────┐  │
│  │course_members   │  │  │  │lessons         │  │  │  │homework        │  │
│  │(id)            │  │  │  │(lesson_id)     │  │  │  │(hw_id)         │  │
│  │├─course_id     │  │  │  │├─course_id     │  │  │  │├─course_id     │  │
│  │├─user_id, role │  │  │  │├─title         │  │  │  │├─title         │  │
│  │├─display_name  │  │  │  │├─content       │  │  │  │├─questions     │  │
│  │└─metadata      │  │  │  │└─metadata      │  │  │  │└─settings      │  │
│  └────────────────┘  │  │  └────────────────┘  │  │  └────────────────┘  │
└──────────────────────┘  └──────────────────────┘  └──────────────────────┘
                                                          │
                                                          │ 1:N
                                                          ▼
                                          ┌──────────────────────┐
                                          │      提交表           │
                                          │  ┌────────────────┐  │
                                          │  │submissions      │  │
                                          │  │(id)            │  │
                                          │  │├─hw_id         │  │
                                          │  │├─student_id    │  │
                                          │  │├─answers       │  │
                                          │  │├─score         │  │
                                          │  │└─feedback      │  │
                                          │  └────────────────┘  │
                                          └──────────────────────┘
```

### 5.2 关系说明

| 关系 | 类型 | 说明 |
|------|------|------|
| users → courses | 1:N | 一个教师创建多个课程 |
| users → course_members | 1:N | 一个学生加入多个课程 |
| courses → lessons | 1:N | 一个课程包含多个课时 |
| courses → homework | 1:N | 一个课程包含多个作业 |
| homework → submissions | 1:N | 一个作业有多个提交 |
| users → submissions | 1:N | 一个学生有多个提交 |

### 5.3 外键约束策略

- **ON DELETE CASCADE**：删除父记录时自动删除子记录
- 适用于：课程删除时删除课时、作业、成员

---

## 6. 索引策略

### 6.1 主键索引

每个表自动创建主键索引，用于唯一标识记录。

### 6.2 外键索引

为所有外键字段创建索引，加速关联查询：

```sql
-- 课程表
CREATE INDEX idx_courses_teacher ON courses(teacher_id, teacher_role);

-- 课程成员表
CREATE INDEX idx_course_members_course ON course_members(course_id);
CREATE INDEX idx_course_members_user ON course_members(user_id, user_role);

-- 课时表
CREATE INDEX idx_lessons_course ON lessons(course_id);

-- 作业表
CREATE INDEX idx_homework_course ON homework(course_id);

-- 提交表
CREATE INDEX idx_submissions_homework ON submissions(hw_id);
CREATE INDEX idx_submissions_student ON submissions(student_id, student_role);
CREATE INDEX idx_submissions_course ON submissions(course_id);
```

### 6.3 业务索引

为常用查询字段创建索引：

```sql
-- 用户表
CREATE INDEX idx_users_display_name ON users(display_name);
CREATE INDEX idx_users_registered_at ON users(registered_at);

-- 课程表
CREATE INDEX idx_courses_subject ON courses(subject);
CREATE INDEX idx_courses_grade ON courses(grade);
CREATE INDEX idx_courses_is_public ON courses(is_public);
CREATE INDEX idx_courses_created_at ON courses(created_at);

-- 作业表
CREATE INDEX idx_homework_deadline ON homework(deadline);
CREATE INDEX idx_homework_created_at ON homework(created_at);

-- 提交表
CREATE INDEX idx_submissions_status ON submissions(status);
CREATE INDEX idx_submissions_submitted_at ON submissions(submitted_at);
CREATE INDEX idx_submissions_graded_at ON submissions(graded_at);
```

### 6.4 JSONB 索引

为 JSONB 字段创建 GIN 索引，支持 JSON 查询：

```sql
CREATE INDEX idx_users_profile ON users USING GIN (profile);
CREATE INDEX idx_courses_metadata ON courses USING GIN (metadata);
CREATE INDEX idx_lessons_metadata ON lessons USING GIN (metadata);
CREATE INDEX idx_homework_questions ON homework USING GIN (questions);
CREATE INDEX idx_submissions_answers ON submissions USING GIN (answers);
CREATE INDEX idx_submissions_feedback ON submissions USING GIN (feedback);
```

### 6.5 唯一索引

```sql
-- 课程加入码
CREATE UNIQUE INDEX uq_courses_join_code ON courses(join_code);

-- 课程成员唯一性
CREATE UNIQUE INDEX uq_course_member 
    ON course_members(course_id, user_id, user_role);

-- 提交尝试唯一性
CREATE UNIQUE INDEX uq_submission_attempt 
    ON submissions(hw_id, student_id, attempt_number);
```

### 6.6 复合索引

为常用复合查询创建索引：

```sql
-- 课时排序
CREATE INDEX idx_lessons_order ON lessons(course_id, "order");

-- 提交状态和时间
CREATE INDEX idx_submissions_status_time 
    ON submissions(status, submitted_at);
```

---

## 7. 数据类型说明

### 7.1 字符串类型

| 类型 | 用途 | 示例 |
|------|------|------|
| VARCHAR(n) | 固定长度字符串 | user_id, course_id |
| TEXT | 可变长度大文本 | description, content |

### 7.2 数值类型

| 类型 | 用途 | 示例 |
|------|------|------|
| INTEGER | 整数 | score, member_count |
| SERIAL | 自增整数 | id |

### 7.3 时间类型

| 类型 | 用途 | 示例 |
|------|------|------|
| TIMESTAMP WITH TIME ZONE | 带时区时间 | created_at, updated_at |

### 7.4 布尔类型

| 类型 | 用途 | 示例 |
|------|------|------|
| BOOLEAN | 布尔值 | is_public |

### 7.5 JSON 类型

| 类型 | 用途 | 示例 |
|------|------|------|
| JSONB | 二进制 JSON | profile, settings, metadata |

**JSONB 优势：**
- 存储效率高
- 支持索引
- 支持查询和更新
- 支持约束验证

### 7.6 类型选择原则

1. **优先使用原生类型**：INTEGER 优于 VARCHAR 存储数字
2. **使用 TIMESTAMPTZ**：统一时区处理
3. **使用 JSONB**：存储灵活结构数据
4. **使用 TEXT**：存储大文本内容

---

## 8. 扩展性设计

### 8.1 JSONB 扩展字段

所有表都包含 `metadata` 或 `settings` JSONB 字段，用于存储：

- 未来新增的属性
- 自定义配置
- 扩展数据

**示例：**

```sql
-- 添加新属性无需修改表结构
UPDATE users SET profile = profile || '{"phone": "13800138000"}' 
WHERE user_id = 'user1';

-- 查询 JSON 字段
SELECT * FROM users WHERE profile->>'phone' = '13800138000';
```

### 8.2 预留扩展点

| 表 | 扩展点 | 说明 |
|------|--------|------|
| users | profile, settings | 用户信息和设置 |
| courses | metadata, settings | 课程配置和扩展 |
| lessons | metadata, content_type | 内容类型和资源 |
| homework | questions, settings | 题目类型和设置 |
| submissions | answers, feedback | 答案格式和反馈 |

### 8.3 未来扩表示例

```sql
-- 课程资源表
CREATE TABLE course_resources (
    id SERIAL PRIMARY KEY,
    course_id VARCHAR(12) REFERENCES courses(course_id),
    resource_type VARCHAR(20) NOT NULL,
    title VARCHAR(200) NOT NULL,
    url VARCHAR(500),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 讨论区表
CREATE TABLE discussions (
    id SERIAL PRIMARY KEY,
    course_id VARCHAR(12) REFERENCES courses(course_id),
    user_id VARCHAR(64),
    user_role VARCHAR(20),
    title VARCHAR(200) NOT NULL,
    content TEXT,
    parent_id INTEGER REFERENCES discussions(id),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 学习进度表
CREATE TABLE learning_progress (
    id SERIAL PRIMARY KEY,
    student_id VARCHAR(64),
    student_role VARCHAR(20),
    course_id VARCHAR(12),
    lesson_id VARCHAR(12),
    progress_percent INTEGER DEFAULT 0,
    last_accessed TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}',
    UNIQUE (student_id, lesson_id)
);

-- 通知表
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(64),
    user_role VARCHAR(20),
    notification_type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

### 8.4 架构演进策略

1. **向后兼容**：新增字段使用 DEFAULT 值
2. **JSONB 扩展**：优先使用 JSONB 而非新增列
3. **版本迁移**：使用 Alembic 管理数据库版本

---

## 9. 数据迁移策略

### 9.1 迁移流程

```
┌─────────────────────────────────────────────────────────────────┐
│                        数据迁移流程                              │
├─────────────────────────────────────────────────────────────────┤
│  1. 准备阶段                                                     │
│     ├── 备份现有数据                                              │
│     ├── 创建数据库和表                                            │
│     └── 验证数据库连接                                            │
│                                                                  │
│  2. 迁移阶段                                                     │
│     ├── 迁移用户数据                                              │
│     ├── 迁移课程数据                                              │
│     ├── 迁移成员数据                                              │
│     ├── 迁移课时数据                                              │
│     ├── 迁移作业数据                                              │
│     └── 迁移提交数据                                              │
│                                                                  │
│  3. 验证阶段                                                     │
│     ├── 验证数据完整性                                            │
│     ├── 验证关系一致性                                            │
│     └── 验证业务逻辑                                              │
│                                                                  │
│  4. 切换阶段                                                     │
│     ├── 更新配置文件                                              │
│     ├── 重启服务                                                  │
│     └── 监控运行状态                                              │
└─────────────────────────────────────────────────────────────────┘
```

### 9.2 迁移脚本

```python
# nanobot/migrations/file_to_db.py

async def migrate_users(session, users_file):
    """迁移用户数据"""
    data = json.loads(users_file.read_text())
    for key, user_data in data.items():
        user = User.from_dict(user_data)
        session.add(user)
    await session.commit()

async def migrate_courses(session, courses_dir):
    """迁移课程数据"""
    index_file = courses_dir / "index.json"
    index = json.loads(index_file.read_text())
    for course_id in index:
        course_file = courses_dir / course_id / "course.json"
        course_data = json.loads(course_file.read_text())
        course = Course.from_dict(course_data)
        session.add(course)
    await session.commit()

# ... 其他迁移函数
```

### 9.3 数据验证

```sql
-- 验证用户数量
SELECT COUNT(*) FROM users;

-- 验证课程数量
SELECT COUNT(*) FROM courses;

-- 验证成员关系
SELECT c.course_name, COUNT(cm.id) as member_count
FROM courses c
LEFT JOIN course_members cm ON c.course_id = cm.course_id
GROUP BY c.course_id;

-- 验证作业提交
SELECT h.title, COUNT(s.id) as submission_count
FROM homework h
LEFT JOIN submissions s ON h.hw_id = s.hw_id
GROUP BY h.hw_id;
```

### 9.4 回滚策略

1. **保留原文件**：迁移过程中不删除原文件
2. **分步迁移**：每个实体独立迁移，可单独回滚
3. **备份数据库**：迁移前备份数据库

---

## 10. 性能考虑

### 10.1 查询优化

**常见查询场景：**

```sql
-- 1. 查询用户的课程
SELECT * FROM courses 
WHERE teacher_id = 'user1' AND teacher_role = 'teacher'
ORDER BY created_at DESC;

-- 2. 查询课程的成员
SELECT cm.* FROM course_members cm
WHERE cm.course_id = 'course1'
ORDER BY cm.joined_at;

-- 3. 查询作业的提交
SELECT s.* FROM submissions s
WHERE s.hw_id = 'hw1' AND s.status = 'graded'
ORDER BY s.score DESC;

-- 4. 查询学生的成绩
SELECT 
    c.course_name,
    h.title,
    s.score,
    h.total_points
FROM submissions s
JOIN homework h ON s.hw_id = h.hw_id
JOIN courses c ON h.course_id = c.course_id
WHERE s.student_id = 'student1' AND s.status = 'graded';
```

### 10.2 连接池配置

```python
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    database_url,
    pool_size=5,        # 连接池大小
    max_overflow=10,    # 最大溢出连接
    pool_pre_ping=True, # 连接健康检查
    pool_recycle=3600,  # 连接回收时间
)
```

### 10.3 批量操作

```python
# 批量插入
async def bulk_insert_users(session, users_data):
    users = [User.from_dict(data) for data in users_data]
    session.add_all(users)
    await session.commit()

# 批量更新
async def bulk_update_scores(session, scores):
    for hw_id, student_id, score in scores:
        await session.execute(
            update(Submission)
            .where(Submission.hw_id == hw_id)
            .where(Submission.student_id == student_id)
            .values(score=score, status='graded')
        )
    await session.commit()
```

### 10.4 缓存策略

```python
from functools import lru_cache
from datetime import datetime, timedelta

# 内存缓存
@lru_cache(maxsize=1000)
async def get_course(course_id: str):
    return await storage.get_course(course_id)

# 带过期的缓存
course_cache = {}
CACHE_TTL = timedelta(minutes=5)

async def get_course_with_cache(course_id: str):
    if course_id in course_cache:
        data, timestamp = course_cache[course_id]
        if datetime.now() - timestamp < CACHE_TTL:
            return data
    
    course = await storage.get_course(course_id)
    course_cache[course_id] = (course, datetime.now())
    return course
```

### 10.5 分页查询

```python
async def list_courses_paginated(
    page: int = 1,
    page_size: int = 20,
    filters: dict = None
):
    query = select(Course)
    
    if filters:
        if filters.get('subject'):
            query = query.where(Course.subject == filters['subject'])
        if filters.get('grade'):
            query = query.where(Course.grade == filters['grade'])
    
    # 计算总数
    count_query = select(func.count()).select_from(query.subquery())
    total = await session.scalar(count_query)
    
    # 分页查询
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(query)
    courses = result.scalars().all()
    
    return {
        'data': courses,
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': (total + page_size - 1) // page_size
    }
```

---

## 11. 安全考虑

### 11.1 SQL 注入防护

SQLAlchemy 使用参数化查询，自动防止 SQL 注入：

```python
# 安全：参数化查询
user = await session.execute(
    select(User).where(User.user_id == user_id)
)

# 不安全：字符串拼接（不要这样做！）
# query = f"SELECT * FROM users WHERE user_id = '{user_id}'"
```

### 11.2 数据加密

**敏感字段加密：**

```python
from cryptography.fernet import Fernet

# 生成密钥
key = Fernet.generate_key()
cipher = Fernet(key)

# 加密
encrypted = cipher.encrypt(b"sensitive data")

# 解密
decrypted = cipher.decrypt(encrypted)
```

**应用层加密：**

```python
class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(String(64), primary_key=True)
    _email = Column('email', String(200))
    
    @property
    def email(self):
        return decrypt(self._email)
    
    @email.setter
    def email(self, value):
        self._email = encrypt(value)
```

### 11.3 访问控制

**角色权限：**

```python
# 教师权限
async def check_teacher_permission(user_id: str, course_id: str):
    course = await storage.get_course(course_id)
    if course.teacher_id != user_id:
        raise PermissionError("Not your course")

# 学生权限
async def check_student_permission(user_id: str, course_id: str):
    is_member = await storage.is_member(course_id, user_id)
    if not is_member:
        raise PermissionError("Not a member")
```

### 11.4 数据脱敏

```python
def mask_sensitive_data(user_data: dict) -> dict:
    """脱敏敏感数据"""
    masked = user_data.copy()
    if 'phone' in masked.get('profile', {}):
        phone = masked['profile']['phone']
        masked['profile']['phone'] = phone[:3] + '****' + phone[-4:]
    return masked
```

### 11.5 审计日志

```sql
-- 审计日志表
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    record_id VARCHAR(64) NOT NULL,
    action VARCHAR(20) NOT NULL,  -- INSERT, UPDATE, DELETE
    old_data JSONB,
    new_data JSONB,
    user_id VARCHAR(64),
    user_role VARCHAR(20),
    ip_address VARCHAR(45),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 触发器函数
CREATE OR REPLACE FUNCTION audit_trigger_func()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_logs (table_name, record_id, action, new_data)
        VALUES (TG_TABLE_NAME, NEW.user_id, 'INSERT', to_jsonb(NEW));
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_logs (table_name, record_id, action, old_data, new_data)
        VALUES (TG_TABLE_NAME, NEW.user_id, 'UPDATE', to_jsonb(OLD), to_jsonb(NEW));
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_logs (table_name, record_id, action, old_data)
        VALUES (TG_TABLE_NAME, OLD.user_id, 'DELETE', to_jsonb(OLD));
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 创建触发器
CREATE TRIGGER users_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
```

---

## 12. 备份和恢复

### 12.1 备份策略

**全量备份：**

```bash
# 每日全量备份
pg_dump -U nanobot -d nanobot > backup_$(date +%Y%m%d).sql

# 压缩备份
pg_dump -U nanobot -d nanobot | gzip > backup_$(date +%Y%m%d).sql.gz
```

**增量备份：**

```bash
# 启用 WAL 归档
archive_mode = on
archive_command = 'cp %p /var/lib/postgresql/archive/%f'

# 基础备份
pg_basebackup -U nanobot -D /backup/base -Ft -z

# 恢复到指定时间点
restore_command = 'cp /var/lib/postgresql/archive/%f %p'
recovery_target_time = '2026-05-30 10:00:00'
```

### 12.2 恢复流程

```bash
# 1. 停止服务
systemctl stop nanobot

# 2. 恢复数据库
psql -U nanobot -d nanobot < backup_20260530.sql

# 3. 验证数据
psql -U nanobot -d nanobot -c "SELECT COUNT(*) FROM users;"

# 4. 启动服务
systemctl start nanobot
```

### 12.3 备份验证

```bash
# 验证备份完整性
pg_restore -l backup_20260530.sql

# 测试恢复到临时数据库
createdb -U nanobot nanobot_test
psql -U nanobot -d nanobot_test < backup_20260530.sql

# 验证数据
psql -U nanobot -d nanobot_test -c "
SELECT 
    (SELECT COUNT(*) FROM users) as users,
    (SELECT COUNT(*) FROM courses) as courses,
    (SELECT COUNT(*) FROM lessons) as lessons;
"
```

### 12.4 自动备份脚本

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/var/backups/nanobot"
RETENTION_DAYS=30

# 创建备份目录
mkdir -p $BACKUP_DIR

# 执行备份
pg_dump -U nanobot -d nanobot | gzip > "$BACKUP_DIR/nanobot_$(date +%Y%m%d_%H%M%S).sql.gz"

# 删除旧备份
find $BACKUP_DIR -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete

# 记录日志
echo "Backup completed at $(date)" >> /var/log/nanobot/backup.log
```

**Cron 定时任务：**

```bash
# 每天凌晨2点执行备份
0 2 * * * /path/to/backup.sh
```

---

## 13. 监控和维护

### 13.1 性能监控

**查询慢查询：**

```sql
-- 启用慢查询日志
log_min_duration_statement = 1000  -- 记录超过1秒的查询

-- 查看慢查询
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;
```

**连接监控：**

```sql
-- 查看当前连接
SELECT 
    pid,
    usename,
    application_name,
    client_addr,
    state,
    query
FROM pg_stat_activity;

-- 查看连接数
SELECT count(*) FROM pg_stat_activity;
```

### 13.2 空间监控

```sql
-- 查看数据库大小
SELECT pg_size_pretty(pg_database_size('nanobot'));

-- 查看表大小
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(tablename::text)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(tablename::text) DESC;

-- 查看索引大小
SELECT 
    indexname,
    pg_size_pretty(pg_relation_size(indexname::text)) as size
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY pg_relation_size(indexname::text) DESC;
```

### 13.3 维护任务

**定期维护：**

```sql
-- 更新统计信息
ANALYZE;

-- 清理死元组
VACUUM;

-- 重建索引
REINDEX INDEX idx_users_display_name;
REINDEX INDEX idx_courses_teacher;
```

**自动维护脚本：**

```bash
#!/bin/bash
# maintenance.sh

# 更新统计信息
psql -U nanobot -d nanobot -c "ANALYZE;"

# 清理死元组
psql -U nanobot -d nanobot -c "VACUUM;"

# 重建索引
psql -U nanobot -d nanobot -c "REINDEX INDEX idx_users_display_name;"
psql -U nanobot -d nanobot -c "REINDEX INDEX idx_courses_teacher;"
```

**Cron 定时任务：**

```bash
# 每周日凌晨3点执行维护
0 3 * * 0 /path/to/maintenance.sh
```

### 13.4 告警配置

**连接数告警：**

```sql
-- 创建告警函数
CREATE OR REPLACE FUNCTION check_connections()
RETURNS void AS $$
DECLARE
    conn_count INTEGER;
    max_conn INTEGER;
BEGIN
    SELECT count(*) INTO conn_count FROM pg_stat_activity;
    SELECT setting INTO max_conn FROM pg_settings WHERE name = 'max_connections';
    
    IF conn_count > max_conn * 0.8 THEN
        RAISE WARNING 'Connection count high: %/%', conn_count, max_conn;
    END IF;
END;
$$ LANGUAGE plpgsql;
```

**空间告警：**

```sql
-- 检查表空间
CREATE OR REPLACE FUNCTION check_table_space()
RETURNS void AS $$
DECLARE
    table_size BIGINT;
BEGIN
    SELECT pg_total_relation_size('submissions') INTO table_size;
    
    IF table_size > 1073741824 THEN  -- 1GB
        RAISE WARNING 'submissions table size exceeds 1GB: %', 
            pg_size_pretty(table_size);
    END IF;
END;
$$ LANGUAGE plpgsql;
```

---

## 附录

### A. 完整建表脚本

```sql
-- 完整建表脚本
-- nanobot/sql/create_tables.sql

-- 1. 用户表
CREATE TABLE users (
    role VARCHAR(20) NOT NULL,
    user_id VARCHAR(64) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    profile JSONB DEFAULT '{}',
    settings JSONB DEFAULT '{}',
    registered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_users PRIMARY KEY (role, user_id),
    CONSTRAINT chk_user_role CHECK (role IN ('teacher', 'student', 'researcher'))
);

-- 2. 课程表
CREATE TABLE courses (
    course_id VARCHAR(12) NOT NULL,
    course_name VARCHAR(200) NOT NULL,
    subject VARCHAR(50) NOT NULL,
    grade VARCHAR(20) NOT NULL,
    description TEXT,
    teacher_id VARCHAR(64) NOT NULL,
    teacher_role VARCHAR(20) NOT NULL DEFAULT 'teacher',
    teacher_name VARCHAR(100) NOT NULL,
    join_code VARCHAR(6) NOT NULL,
    is_public BOOLEAN DEFAULT FALSE,
    member_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_courses PRIMARY KEY (course_id),
    CONSTRAINT fk_courses_teacher FOREIGN KEY (teacher_id, teacher_role) 
        REFERENCES users(user_id, role) ON DELETE CASCADE,
    CONSTRAINT uq_courses_join_code UNIQUE (join_code)
);

-- 3. 课程成员表
CREATE TABLE course_members (
    id SERIAL NOT NULL,
    course_id VARCHAR(12) NOT NULL,
    user_id VARCHAR(64) NOT NULL,
    user_role VARCHAR(20) NOT NULL DEFAULT 'student',
    display_name VARCHAR(100) NOT NULL,
    metadata JSONB DEFAULT '{}',
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_course_members PRIMARY KEY (id),
    CONSTRAINT fk_course_members_course FOREIGN KEY (course_id) 
        REFERENCES courses(course_id) ON DELETE CASCADE,
    CONSTRAINT fk_course_members_user FOREIGN KEY (user_id, user_role) 
        REFERENCES users(user_id, role) ON DELETE CASCADE,
    CONSTRAINT uq_course_member UNIQUE (course_id, user_id, user_role)
);

-- 4. 课时表
CREATE TABLE lessons (
    lesson_id VARCHAR(12) NOT NULL,
    course_id VARCHAR(12) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    "order" INTEGER DEFAULT 0,
    content_type VARCHAR(20) DEFAULT 'markdown',
    content TEXT,
    content_hash VARCHAR(64),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_lessons PRIMARY KEY (lesson_id),
    CONSTRAINT fk_lessons_course FOREIGN KEY (course_id) 
        REFERENCES courses(course_id) ON DELETE CASCADE
);

-- 5. 作业表
CREATE TABLE homework (
    hw_id VARCHAR(15) NOT NULL,
    course_id VARCHAR(12) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    total_points INTEGER DEFAULT 0,
    deadline TIMESTAMP WITH TIME ZONE,
    created_by VARCHAR(64) NOT NULL,
    questions JSONB DEFAULT '[]',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_homework PRIMARY KEY (hw_id),
    CONSTRAINT fk_homework_course FOREIGN KEY (course_id) 
        REFERENCES courses(course_id) ON DELETE CASCADE
);

-- 6. 提交表
CREATE TABLE submissions (
    id SERIAL NOT NULL,
    hw_id VARCHAR(15) NOT NULL,
    student_id VARCHAR(64) NOT NULL,
    student_role VARCHAR(20) NOT NULL DEFAULT 'student',
    course_id VARCHAR(12) NOT NULL,
    attempt_number INTEGER DEFAULT 1,
    answers JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'submitted',
    score INTEGER DEFAULT 0,
    feedback JSONB DEFAULT '{}',
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    graded_at TIMESTAMP WITH TIME ZONE,
    graded_by VARCHAR(64),
    CONSTRAINT pk_submissions PRIMARY KEY (id),
    CONSTRAINT fk_submissions_homework FOREIGN KEY (hw_id) 
        REFERENCES homework(hw_id) ON DELETE CASCADE,
    CONSTRAINT fk_submissions_student FOREIGN KEY (student_id, student_role) 
        REFERENCES users(user_id, role) ON DELETE CASCADE,
    CONSTRAINT fk_submissions_course FOREIGN KEY (course_id) 
        REFERENCES courses(course_id) ON DELETE CASCADE,
    CONSTRAINT uq_submission_attempt UNIQUE (hw_id, student_id, attempt_number)
);

-- 7. 创建索引
CREATE INDEX idx_users_display_name ON users(display_name);
CREATE INDEX idx_users_registered_at ON users(registered_at);
CREATE INDEX idx_users_profile ON users USING GIN (profile);

CREATE INDEX idx_courses_teacher ON courses(teacher_id, teacher_role);
CREATE INDEX idx_courses_subject ON courses(subject);
CREATE INDEX idx_courses_grade ON courses(grade);
CREATE INDEX idx_courses_is_public ON courses(is_public);
CREATE INDEX idx_courses_created_at ON courses(created_at);
CREATE INDEX idx_courses_metadata ON courses USING GIN (metadata);

CREATE INDEX idx_course_members_course ON course_members(course_id);
CREATE INDEX idx_course_members_user ON course_members(user_id, user_role);

CREATE INDEX idx_lessons_course ON lessons(course_id);
CREATE INDEX idx_lessons_order ON lessons(course_id, "order");
CREATE INDEX idx_lessons_content_type ON lessons(content_type);
CREATE INDEX idx_lessons_metadata ON lessons USING GIN (metadata);

CREATE INDEX idx_homework_course ON homework(course_id);
CREATE INDEX idx_homework_created_by ON homework(created_by);
CREATE INDEX idx_homework_deadline ON homework(deadline);
CREATE INDEX idx_homework_questions ON homework USING GIN (questions);

CREATE INDEX idx_submissions_homework ON submissions(hw_id);
CREATE INDEX idx_submissions_student ON submissions(student_id, student_role);
CREATE INDEX idx_submissions_course ON submissions(course_id);
CREATE INDEX idx_submissions_status ON submissions(status);
CREATE INDEX idx_submissions_submitted_at ON submissions(submitted_at);
CREATE INDEX idx_submissions_answers ON submissions USING GIN (answers);
CREATE INDEX idx_submissions_feedback ON submissions USING GIN (feedback);
```

### B. 常用查询示例

```sql
-- 1. 查询用户的课程（教师）
SELECT * FROM courses 
WHERE teacher_id = 'user1' AND teacher_role = 'teacher'
ORDER BY created_at DESC;

-- 2. 查询公开课程
SELECT * FROM courses 
WHERE is_public = TRUE
ORDER BY member_count DESC;

-- 3. 查询课程的成员
SELECT cm.* FROM course_members cm
WHERE cm.course_id = 'course1'
ORDER BY cm.joined_at;

-- 4. 查询课程的课时
SELECT * FROM lessons
WHERE course_id = 'course1'
ORDER BY "order";

-- 5. 查询作业的提交
SELECT s.*, u.display_name
FROM submissions s
JOIN users u ON s.student_id = u.user_id AND s.student_role = u.role
WHERE s.hw_id = 'hw1'
ORDER BY s.submitted_at DESC;

-- 6. 查询学生的成绩
SELECT 
    c.course_name,
    h.title,
    s.score,
    h.total_points,
    ROUND(s.score * 100.0 / h.total_points, 2) as percentage
FROM submissions s
JOIN homework h ON s.hw_id = h.hw_id
JOIN courses c ON h.course_id = c.course_id
WHERE s.student_id = 'student1' AND s.status = 'graded'
ORDER BY s.submitted_at DESC;

-- 7. 查询课程统计
SELECT 
    c.course_name,
    COUNT(DISTINCT cm.id) as member_count,
    COUNT(DISTINCT l.lesson_id) as lesson_count,
    COUNT(DISTINCT h.hw_id) as homework_count
FROM courses c
LEFT JOIN course_members cm ON c.course_id = cm.course_id
LEFT JOIN lessons l ON c.course_id = l.course_id
LEFT JOIN homework h ON c.course_id = h.course_id
WHERE c.course_id = 'course1'
GROUP BY c.course_id;

-- 8. 查询作业提交统计
SELECT 
    h.title,
    COUNT(s.id) as submission_count,
    AVG(s.score) as avg_score,
    MIN(s.score) as min_score,
    MAX(s.score) as max_score
FROM homework h
LEFT JOIN submissions s ON h.hw_id = s.hw_id AND s.status = 'graded'
WHERE h.course_id = 'course1'
GROUP BY h.hw_id;
```

### C. 性能优化建议

1. **查询优化**
   - 使用 EXPLAIN ANALYZE 分析查询计划
   - 避免 SELECT *，只查询需要的字段
   - 使用 LIMIT 限制结果集

2. **索引优化**
   - 为常用查询字段创建索引
   - 避免过度索引
   - 定期重建索引

3. **连接优化**
   - 使用连接池
   - 设置合适的连接超时
   - 监控连接数

4. **缓存优化**
   - 使用 Redis 缓存热点数据
   - 设置合理的缓存过期时间
   - 实现缓存失效策略

---

**文档版本：** v1.0  
**最后更新：** 2026-05-30  
**维护者：** nanobot 团队
