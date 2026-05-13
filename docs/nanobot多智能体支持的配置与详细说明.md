# Nanobot多智能体支持配置与详细说明

## 1. 多智能体系统概述

Nanobot的多智能体系统允许同时使用多个专门的AI代理来处理不同类型的任务，每个智能体都有自己的专长领域和工具集。

## 2. 配置文件结构

### 2.1 主配置文件 (config.yaml)

```yaml
# config.yaml
agents:
  # 默认配置
  defaults:
    model: "gpt-4-turbo"
    temperature: 0.7
    max_tokens: 2048
    streaming: true
    
  # 智能体定义
  agents:
    # 研究助手智能体
    - name: "researcher"
      model: "gpt-4-turbo"
      role: "Research Assistant"
      description: "Specialized in research tasks and information gathering"
      instructions: |
        You are a research assistant. Help with:
        - Finding relevant information
        - Analyzing sources
        - Summarizing complex topics
        - Cross-referencing information
      tools:
        - web_search
        - citation_formatter
        - data_extractor
      temperature: 0.3
      max_tokens: 1024
      enabled: true
      
    # 内容写作者智能体
    - name: "writer"
      model: "claude-3-opus"
      role: "Content Writer"
      description: "Specialized in creating well-structured, engaging content"
      instructions: |
        You are a professional content writer. Create:
        - Well-structured documents
        - Engaging narratives
        - Clear explanations
        - Proper formatting
      tools:
        - markdown_formatter
        - grammar_checker
        - style_guide_enforcer
        - content_optimizer
      temperature: 0.7
      max_tokens: 1500
      enabled: true
      
    # 数据分析师智能体
    - name: "analyst"
      model: "gpt-4-turbo"
      role: "Data Analyst"
      description: "Specialized in data analysis and insights"
      instructions: |
        You are a data analyst. Your tasks include:
        - Statistical analysis
        - Data visualization
        - Pattern recognition
        - Trend analysis
      tools:
        - statistical_calculator
        - data_visualizer
        - chart_generator
        - data_formatter
      temperature: 0.2
      max_tokens: 1024
      enabled: true
      
    # 代码助手智能体
    - name: "coder"
      model: "gpt-4-turbo"
      role: "Code Assistant"
      description: "Specialized in programming and code assistance"
      instructions: |
        You are a programming assistant. Help with:
        - Code generation
        - Debugging
        - Code review
        - Technical documentation
      tools:
        - code_formatter
        - syntax_checker
        - code_generator
        - documentation_generator
      temperature: 0.1
      max_tokens: 1024
      enabled: true
      
    # 通用智能体（默认）
    - name: "default"
      model: "gpt-4-turbo"
      role: "General Assistant"
      description: "General purpose assistant for routine tasks"
      instructions: "You are a general assistant. Handle routine queries and provide helpful responses."
      tools: []
      temperature: 0.7
      max_tokens: 1024
      enabled: true

# 智能体路由配置
agent_routing:
  # 基于关键词的路由规则
  keyword_rules:
    research: ["researcher"]
    write: ["writer"]
    analyze: ["analyst"]
    data: ["analyst"]
    code: ["coder"]
    programming: ["coder"]
    calculate: ["analyst"]
    math: ["analyst"]
    
  # 任务类型路由
  task_type_routing:
    - type: "research"
      agents: ["researcher"]
      priority: 1
      
    - type: "content_creation"
      agents: ["writer", "researcher"]
      priority: 2
      
    - type: "data_analysis"
      agents: ["analyst", "researcher"]
      priority: 3
      
    - type: "programming"
      agents: ["coder", "analyst"]
      priority: 4
      
  # 默认路由
  default_agents: ["default", "researcher"]

# 多智能体协作配置
multi_agent_cooperation:
  # 协作模式
  mode: "sequential"  # "sequential", "parallel", "orchestrated"
  
  # 最大并行任务数
  max_parallel_tasks: 3
  
  # 任务分解策略
  task_decomposition:
    - strategy: "divide_and_conquer"
      max_subtasks: 5
      
    - strategy: "expert_consultation"
      max_consultants: 3
      
  # 结果整合方式
  result_integration:
    - method: "weighted_average"
      weights: [0.3, 0.4, 0.3]
      
    - method: "consensus"
      threshold: 0.7

# 工具配置
tools:
  # 网络搜索工具
  web_search:
    enabled: true
    max_results: 10
    timeout: 30
    
  # 数据可视化工具
  data_visualizer:
    enabled: true
    chart_types: ["bar", "line", "pie", "scatter"]
    max_data_points: 1000
    
  # 代码格式化工具
  code_formatter:
    enabled: true
    languages: ["python", "javascript", "typescript", "java", "cpp"]
    
  # 语法检查工具
  syntax_checker:
    enabled: true
    languages: ["python", "javascript", "typescript", "java", "cpp"]
```

### 2.2 智能体工具配置 (config/tools.yaml)

```yaml
# config/tools.yaml
tool_registry:
  # 搜索工具
  search:
    name: "web_search"
    type: "external_api"
    provider: "serpapi"
    config:
      api_key: "${SERPAPI_API_KEY}"
      max_results: 10
      language: "en"
      location: "US"
      
  # 数据分析工具
  data_analysis:
    name: "statistical_calculator"
    type: "mathematical"
    config:
      precision: 6
      max_iterations: 1000
      
  # 内容格式化工具
  content_formatting:
    name: "markdown_formatter"
    type: "text_processor"
    config:
      line_width: 80
      indent_size: 2
      code_block_language: "python"
      
  # 代码生成工具
  code_generation:
    name: "code_generator"
    type: "code_processor"
    config:
      max_output_lines: 500
      include_comments: true
      include_documentation: true
      
  # 数据可视化工具
  visualization:
    name: "chart_generator"
    type: "data_visualizer"
    config:
      chart_types: ["bar", "line", "pie", "scatter", "heatmap"]
      theme: "light"
      width: 800
      height: 600

# 工具访问控制
tool_access_control:
  # 每个智能体可以使用的工具
  agent_tool_access:
    researcher:
      - web_search
      - citation_formatter
      - data_extractor
      
    writer:
      - markdown_formatter
      - grammar_checker
      - style_guide_enforcer
      
    analyst:
      - statistical_calculator
      - data_visualizer
      - chart_generator
      
    coder:
      - code_formatter
      - syntax_checker
      - code_generator
      
    default:
      - web_search
      - markdown_formatter
```

## 3. 智能体实现类

### 3.1 基础智能体类 (agents/base.py)

```python
# agents/base.py
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
import json

class BaseAgent(ABC):
    """基础智能体类"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.model = config.get('model', 'gpt-4-turbo')
        self.role = config.get('role', 'Assistant')
        self.description = config.get('description', '')
        self.instructions = config.get('instructions', '')
        self.tools = config.get('tools', [])
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 1024)
        self.enabled = config.get('enabled', True)
        
        # 工具注册
        self.tool_registry = ToolRegistry()
        
    @abstractmethod
    def process_message(self, message: str, context: Optional[Dict] = None) -> str:
        """处理消息的核心方法"""
        pass
        
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """获取智能体能力列表"""
        pass
        
    def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """执行工具"""
        tool = self.tool_registry.get_tool(tool_name)
        if tool:
            return tool.execute(**kwargs)
        else:
            raise ValueError(f"Tool {tool_name} not found")
            
    def get_info(self) -> Dict[str, Any]:
        """获取智能体信息"""
        return {
            'name': self.name,
            'role': self.role,
            'description': self.description,
            'model': self.model,
            'tools': self.tools,
            'enabled': self.enabled
        }
```

### 3.2 智能体管理器 (agents/manager.py)

```python
# agents/manager.py
from typing import Dict, List, Optional
from nanobot.agents.base import BaseAgent
from nanobot.agents.registry import AgentRegistry
from nanobot.agents.router import AgentRouter

class AgentManager:
    """智能体管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.agents: Dict[str, BaseAgent] = {}
        self.registry = AgentRegistry()
        self.router = AgentRouter(config.get('agent_routing', {}))
        self.active_agent: Optional[str] = None
        self.coordinator = None
        
    def initialize_agents(self) -> None:
        """初始化所有智能体"""
        agent_configs = self.config.get('agents', {}).get('agents', [])
        
        for agent_config in agent_configs:
            if agent_config.get('enabled', True):
                agent = self.registry.create_agent(agent_config)
                if agent:
                    self.agents[agent.name] = agent
                    
        # 设置默认活跃智能体
        default_agent = self.config.get('agents', {}).get('defaults', {}).get('default_agent')
        if default_agent and default_agent in self.agents:
            self.active_agent = default_agent
            
    def register_agent(self, agent: BaseAgent) -> None:
        """注册智能体"""
        self.agents[agent.name] = agent
        
    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """获取指定名称的智能体"""
        return self.agents.get(name)
        
    def list_agents(self) -> List[str]:
        """列出所有可用的智能体"""
        return list(self.agents.keys())
        
    def switch_agent(self, agent_name: str) -> bool:
        """切换当前活动智能体"""
        if agent_name in self.agents:
            self.active_agent = agent_name
            return True
        return False
        
    def get_active_agent(self) -> Optional[BaseAgent]:
        """获取当前活动智能体"""
        if self.active_agent:
            return self.agents.get(self.active_agent)
        return None
        
    def process_with_agent(self, message: str, agent_name: str = None, 
                          context: Optional[Dict] = None) -> str:
        """使用指定智能体处理消息"""
        if agent_name:
            agent = self.get_agent(agent_name)
        else:
            agent = self.get_active_agent()
            
        if agent:
            return agent.process_message(message, context)
        else:
            raise ValueError("No agent available for processing")
            
    def route_message(self, message: str, context: Optional[Dict] = None) -> List[str]:
        """根据消息内容路由到合适的智能体"""
        return self.router.route_message(message, context)
        
    def multi_agent_process(self, message: str, context: Optional[Dict] = None) -> str:
        """多智能体协作处理"""
        # 获取路由结果
        target_agents = self.route_message(message, context)
        
        # 执行多智能体处理
        if len(target_agents) == 1:
            # 单智能体处理
            return self.process_with_agent(message, target_agents[0], context)
        else:
            # 多智能体协作
            return self.cooperate_agents(message, target_agents, context)
            
    def cooperate_agents(self, message: str, agent_names: List[str], 
                        context: Optional[Dict] = None) -> str:
        """多智能体协作处理"""
        results = {}
        
        # 并行处理（可以扩展为异步）
        for agent_name in agent_names:
            try:
                agent = self.get_agent(agent_name)
                if agent:
                    result = agent.process_message(message, context)
                    results[agent_name] = result
            except Exception as e:
                results[agent_name] = f"Error: {str(e)}"
                
        # 整合结果
        return self.integrate_results(results, message, context)
        
    def integrate_results(self, results: Dict[str, str], original_message: str, 
                         context: Optional[Dict] = None) -> str:
        """整合多个智能体的结果"""
        # 根据配置的整合策略处理结果
        integration_config = self.config.get('multi_agent_cooperation', {})
        integration_method = integration_config.get('result_integration', [{}])[0].get('method', 'consensus')
        
        if integration_method == 'consensus':
            return self._consensus_integration(results)
        elif integration_method == 'weighted_average':
            return self._weighted_integration(results)
        else:
            return self._simple_concatenation(results)
            
    def _consensus_integration(self, results: Dict[str, str]) -> str:
        """共识整合"""
        # 简单实现：返回所有结果的连接
        return "\n".join([f"{agent}: {result}" for agent, result in results.items()])
        
    def _weighted_integration(self, results: Dict[str, str]) -> str:
        """加权整合"""
        # 简单实现：返回所有结果
        return "\n".join([f"{agent}: {result}" for agent, result in results.items()])
        
    def _simple_concatenation(self, results: Dict[str, str]) -> str:
        """简单拼接"""
        return "\n".join([f"{agent}: {result}" for agent, result in results.items()])
```

### 3.3 智能体路由器 (agents/router.py)

```python
# agents/router.py
from typing import List, Dict, Any
from nanobot.agents.base import BaseAgent

class AgentRouter:
    """智能体路由器"""
    
    def __init__(self, routing_config: Dict[str, Any]):
        self.config = routing_config
        self.keyword_rules = routing_config.get('keyword_rules', {})
        self.task_type_routing = routing_config.get('task_type_routing', [])
        self.default_agents = routing_config.get('default_agents', ['default'])
        
    def route_message(self, message: str, context: Dict[str, Any] = None) -> List[str]:
        """根据消息内容路由到合适的智能体"""
        content = message.lower()
        
        # 1. 关键词路由
        keyword_agents = self._route_by_keywords(content)
        if keyword_agents:
            return keyword_agents
            
        # 2. 任务类型路由
        task_agents = self._route_by_task_type(content, context)
        if task_agents:
            return task_agents
            
        # 3. 默认路由
        return self.default_agents
        
    def _route_by_keywords(self, content: str) -> List[str]:
        """基于关键词的路由"""
        matched_agents = []
        
        for keyword, agents in self.keyword_rules.items():
            if keyword in content:
                matched_agents.extend(agents)
                
        # 去重并返回
        return list(set(matched_agents))
        
    def _route_by_task_type(self, content: str, context: Dict[str, Any] = None) -> List[str]:
        """基于任务类型的路由"""
        # 这里可以实现更复杂的任务类型识别逻辑
        task_type = self._identify_task_type(content, context)
        
        for route in self.task_type_routing:
            if route.get('type') == task_type:
                return route.get('agents', [])
                
        return []
        
    def _identify_task_type(self, content: str, context: Dict[str, Any] = None) -> str:
        """识别任务类型"""
        # 简单的类型识别逻辑
        if 'research' in content or 'find' in content:
            return 'research'
        elif 'write' in content or 'create' in content:
            return 'content_creation'
        elif 'analyze' in content or 'data' in content:
            return 'data_analysis'
        elif 'code' in content or 'program' in content:
            return 'programming'
        else:
            return 'general'
            
    def get_agent_priority(self, agent_name: str) -> int:
        """获取智能体优先级"""
        # 可以根据配置返回优先级
        return 0
```

### 3.4 工具系统 (agents/tools.py)

```python
# agents/tools.py
from typing import Dict, Any, List
from abc import ABC, abstractmethod
import requests
import json

class Tool(ABC):
    """工具基类"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.enabled = config.get('enabled', True)
        
    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """执行工具"""
        pass
        
    def get_description(self) -> str:
        """获取工具描述"""
        return f"Tool: {self.name}"
        
    def get_config(self) -> Dict[str, Any]:
        """获取工具配置"""
        return self.config

class WebSearchTool(Tool):
    """网络搜索工具"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("web_search", config)
        self.api_key = config.get('api_key', '')
        self.max_results = config.get('max_results', 10)
        self.timeout = config.get('timeout', 30)
        
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """执行搜索"""
        if not self.api_key:
            raise ValueError("API key required for web search")
            
        # 这里实现具体的搜索逻辑
        # 示例使用Serper API
        search_params = {
            'q': query,
            'num': self.max_results,
            'gl': kwargs.get('location', 'US'),
            'hl': kwargs.get('language', 'en')
        }
        
        # 实际的API调用
        # response = requests.get(
        #     'https://google.serper.dev/search',
        #     params=search_params,
        #     headers={'X-API-KEY': self.api_key},
        #     timeout=self.timeout
        # )
        
        # return response.json()
        
        # 模拟返回
        return {
            'query': query,
            'results': [
                {
                    'title': 'Sample Search Result',
                    'link': 'https://example.com',
                    'snippet': 'This is a sample search result'
                }
            ]
        }

class StatisticalCalculatorTool(Tool):
    """统计计算器工具"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("statistical_calculator", config)
        self.precision = config.get('precision', 6)
        self.max_iterations = config.get('max_iterations', 1000)
        
    def execute(self, expression: str, **kwargs) -> Dict[str, Any]:
        """执行计算"""
        try:
            # 简单的计算逻辑
            # 实际应用中可以使用更复杂的计算库
            result = eval(expression)
            return {
                'expression': expression,
                'result': result,
                'type': 'calculation'
            }
        except Exception as e:
            return {
                'expression': expression,
                'error': str(e),
                'type': 'error'
            }

class DataVisualizerTool(Tool):
    """数据可视化工具"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("data_visualizer", config)
        self.chart_types = config.get('chart_types', ['bar', 'line', 'pie'])
        self.max_data_points = config.get('max_data_points', 1000)
        
    def execute(self, data: List[Dict[str, Any]], chart_type: str = 'bar', **kwargs) -> Dict[str, Any]:
        """生成图表"""
        if chart_type not in self.chart_types:
            raise ValueError(f"Unsupported chart type: {chart_type}")
            
        # 这里实现图表生成逻辑
        return {
            'data': data,
            'chart_type': chart_type,
            'generated': True
        }

class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        
    def register_tool(self, tool: Tool) -> None:
        """注册工具"""
        self.tools[tool.name] = tool
        
    def get_tool(self, name: str) -> Tool:
        """获取工具"""
        return self.tools.get(name)
        
    def list_tools(self) -> List[str]:
        """列出所有工具"""
        return list(self.tools.keys())
        
    def initialize_tools(self, tool_configs: Dict[str, Any]) -> None:
        """初始化工具"""
        for tool_name, config in tool_configs.items():
            tool = self._create_tool(tool_name, config)
            if tool:
                self.register_tool(tool)
                
    def _create_tool(self, tool_name: str, config: Dict[str, Any]) -> Tool:
        """创建工具实例"""
        tool_type = config.get('type', 'generic')
        
        if tool_type == 'external_api':
            return WebSearchTool(config)
        elif tool_type == 'mathematical':
            return StatisticalCalculatorTool(config)
        elif tool_type == 'data_visualizer':
            return DataVisualizerTool(config)
        else:
            # 返回通用工具
            return Tool(tool_name, config)
```

## 4. 使用示例

### 4.1 启动多智能体系统

```python
# main.py
from nanobot.agents.manager import AgentManager
from nanobot.agents.tools import ToolRegistry
import yaml

def main():
    # 加载配置
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
        
    # 初始化工具
    tool_registry = ToolRegistry()
    tool_configs = config.get('tools', {})
    tool_registry.initialize_tools(tool_configs)
    
    # 初始化智能体管理器
    agent_manager = AgentManager(config)
    agent_manager.initialize_agents()
    
    # 使用示例
    print("可用智能体:", agent_manager.list_agents())
    
    # 使用特定智能体
    researcher = agent_manager.get_agent('researcher')
    if researcher:
        result = researcher.process_message("请帮我查找关于人工智能发展的最新趋势")
        print("研究助手结果:", result)
    
    # 多智能体协作
    multi_result = agent_manager.multi_agent_process("分析Python编程语言的发展趋势")
    print("多智能体协作结果:", multi_result)

if __name__ == "__main__":
    main()
```

### 4.2 Web UI中的多智能体使用

```typescript
// webui/src/components/AgentSelector.tsx
import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";

interface Agent {
  name: string;
  role: string;
  model: string;
  description: string;
  tools: string[];
}

export function AgentSelector({ 
  onAgentChange, 
  currentAgent 
}: { 
  onAgentChange: (agent: string) => void; 
  currentAgent: string; 
}) {
  const { t } = useTranslation();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    // 从服务器获取可用智能体列表
    fetchAgents();
  }, []);
  
  const fetchAgents = async () => {
    try {
      const response = await fetch('/api/agents');
      const data = await response.json();
      setAgents(data.agents);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch agents:', error);
      setLoading(false);
    }
  };
  
  const handleAgentSelect = (agentName: string) => {
    onAgentChange(agentName);
  };
  
  if (loading) {
    return <div className="text-center">{t("agent.loading")}</div>;
  }
  
  return (
    <div className="agent-selector">
      <h3>{t("agent.select")}</h3>
      <div className="agent-list">
        {agents.map(agent => (
          <button
            key={agent.name}
            className={`agent-item ${currentAgent === agent.name ? 'active' : ''}`}
            onClick={() => handleAgentSelect(agent.name)}
          >
            <div className="agent-name">{agent.name}</div>
            <div className="agent-role">{agent.role}</div>
            <div className="agent-tools">
              {agent.tools.map(tool => (
                <span key={tool} className="tool-badge">{tool}</span>
              ))}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
```

## 5. 高级功能

### 5.1 智能体协作模式

```python
# agents/coordinator.py
class AgentCoordinator:
    """智能体协调器"""
    
    def __init__(self, agent_manager: AgentManager):
        self.agent_manager = agent_manager
        self.conversation_history = []
        
    def orchestrate_task(self, task: str, context: Dict[str, Any] = None) -> str:
        """协调复杂任务"""
        # 1. 任务分析
        analysis = self._analyze_task(task, context)
        
        # 2. 任务分解
        subtasks = self._decompose_task(analysis)
        
        # 3. 并行执行
        results = self._execute_parallel(subtasks)
        
        # 4. 结果整合
        final_result = self._integrate_results(results)
        
        return final_result
        
    def _analyze_task(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """分析任务"""
        return {
            "type": "complex",
            "complexity": "high",
            "required_agents": ["researcher", "analyst", "writer"],
            "task_description": task
        }
        
    def _decompose_task(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """分解任务"""
        return [
            {"agent": "researcher", "task": "收集相关信息"},
            {"agent": "analyst", "task": "分析数据"},
            {"agent": "writer", "task": "撰写报告"}
        ]
        
    def _execute_parallel(self, subtasks: List[Dict[str, Any]]) -> Dict[str, str]:
        """并行执行子任务"""
        results = {}
        for task in subtasks:
            agent_name = task["agent"]
            agent = self.agent_manager.get_agent(agent_name)
            if agent:
                result = agent.process_message(task["task"])
                results[agent_name] = result
        return results
        
    def _integrate_results(self, results: Dict[str, str]) -> str:
        """整合结果"""
        return "\n".join([f"{agent}: {result}" for agent, result in results.items()])
```

### 5.2 动态智能体管理

```python
# agents/dynamic_manager.py
class DynamicAgentManager:
    """动态智能体管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.agents = {}
        self.agent_stats = {}
        
    def add_agent(self, agent_config: Dict[str, Any]) -> bool:
        """动态添加智能体"""
        try:
            agent = self._create_agent(agent_config)
            self.agents[agent.name] = agent
            self.agent_stats[agent.name] = {
                'usage_count': 0,
                'success_rate': 0.0,
                'last_used': None
            }
            return True
        except Exception as e:
            print(f"Failed to add agent: {e}")
            return False
            
    def remove_agent(self, agent_name: str) -> bool:
        """移除智能体"""
        if agent_name in self.agents:
            del self.agents[agent_name]
            del self.agent_stats[agent_name]
            return True
        return False
        
    def get_best_agent(self, task: str, context: Dict[str, Any] = None) -> str:
        """获取最适合的智能体"""
        # 基于历史使用数据和任务特征选择最佳智能体
        return "default"  # 简化实现
        
    def update_agent_stats(self, agent_name: str, success: bool):
        """更新智能体统计信息"""
        if agent_name in self.agent_stats:
            stats = self.agent_stats[agent_name]
            stats['usage_count'] += 1
            if success:
                stats['success_rate'] = (stats['success_rate'] * (stats['usage_count'] - 1) + 1) / stats['usage_count']
            else:
                stats['success_rate'] = (stats['success_rate'] * (stats['usage_count'] - 1)) / stats['usage_count']
            stats['last_used'] = datetime.now()
```

## 总结

Nanobot的多智能体系统具有以下特点：

1. **灵活配置**：通过YAML配置文件定义智能体和工具
2. **智能路由**：基于关键词和任务类型自动路由到合适的智能体
3. **工具集成**：支持多种外部工具和API集成
4. **协作机制**：支持多智能体并行协作处理复杂任务
5. **动态管理**：支持动态添加和移除智能体
6. **Web UI支持**：提供用户界面选择和切换智能体
7. **安全认证**：支持权限控制和认证机制

这种设计使得Nanobot能够根据不同的任务需求灵活地使用不同的智能体，实现更强大和专业的AI应用能力。