# Web UI 多智能体测试指南

## 前端组件已完成

已添加以下前端组件：

### 1. AgentSwitcher 组件
- 位置：`webui/src/components/AgentSwitcher.tsx`
- 功能：
  - 自动获取智能体列表
  - 显示当前激活的智能体
  - 下拉菜单切换智能体
  - 显示智能体描述信息
  - 当前选中的智能体显示勾选标记

### 2. Sidebar 组件更新
- 位置：`webui/src/components/Sidebar.tsx`
- 修改：在"新建聊天"按钮下方添加了智能体选择器

## 测试步骤

### 1. 启动后端服务
```bash
nanobot gateway
```

### 2. 启动前端开发服务器
```bash
cd webui
bun install
bun run dev
```

### 3. 访问 Web UI
打开浏览器访问：`http://127.0.0.1:5173`

### 4. 测试功能

#### 测试智能体选择器显示
- 查看侧边栏顶部是否显示智能体选择器
- 默认应该显示"AI领域知识导师"

#### 测试智能体切换
- 点击智能体选择器按钮
- 应该看到下拉菜单，显示两个智能体
- 点击另一个智能体进行切换
- 选择器按钮文本应该更新

#### 测试智能体功能
- 切换到"AI领域知识导师"，问技术问题
- 切换到"AI前沿文献追踪助手"，问研究问题
- 验证回答风格是否不同

## API 测试
```bash
curl http://localhost:8765/api/agents
curl http://localhost:8765/api/agents/current
curl http://localhost:8765/api/agents/ai_literature_tracker/switch
```

## 构建生产版本
```bash
cd webui
bun run build
```
