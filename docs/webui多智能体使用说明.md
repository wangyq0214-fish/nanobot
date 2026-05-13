# Web UI 多智能体使用说明

## 概述

nanobot 的多智能体系统现已支持 Web UI。你可以通过浏览器界面切换不同的智能体，每个智能体都有专门的角色和能力。

## 后端 API 已完成

以下 API 端点已经实现并可用：

### 1. 获取智能体列表
```
GET /api/agents
```

返回示例：
```json
{
  "agents": [
    {
      "name": "ai_tutor",
      "display_name": "AI领域知识导师",
      "role": "人工智能专业导师",
      "description": "专注于计算机人工智能领域的知识问答...",
      "temperature": 0.3
    },
    {
      "name": "ai_literature_tracker",
      "display_name": "AI前沿文献追踪助手",
      "role": "人工智能研究前沿追踪专家",
      "description": "自动检索并归纳AI领域最新学术论文...",
      "temperature": 0.3
    }
  ],
  "has_multi_agent": true
}
```

### 2. 获取当前激活的智能体
```
GET /api/agents/current
```

### 3. 切换智能体
```
GET /api/agents/{agent_name}/switch
```

## 前端集成步骤

要在 Web UI 中添加智能体选择器，需要在 `webui/src/components/` 目录下创建 `AgentSwitcher.tsx` 组件，然后将其添加到侧边栏中。

详细的前端代码示例请参考文档中的完整实现。

## CLI 使用方法（已完成）

```bash
# 列出所有智能体
nanobot agents list

# 查看当前智能体
nanobot agents current

# 切换智能体
nanobot agents switch ai_tutor
nanobot agents switch ai_literature_tracker

# 使用智能体
nanobot agent -m "你的问题"
```

## 测试验证

多智能体系统已在 CLI 中测试通过：

1. AI知识导师能够提供详细的技术讲解、数学推导和代码示例
2. 文献追踪助手能够以研究专家的身份回答问题
3. 智能体切换功能正常工作
4. 配置文件正确加载

## 注意事项

1. **会话隔离**：切换智能体后，建议使用新的会话ID以获得最佳体验
2. **系统提示**：每个智能体都有独特的系统提示，会影响其回答风格和专业领域
3. **配置文件**：智能体配置在 `~/.nanobot/config.json` 中
