"""Simple agent manager for education scenarios."""

from typing import Dict, Optional


class AgentProfile:
    """智能体配置文件"""

    def __init__(self, config: dict):
        self.name = config['name']
        self.display_name = config.get('display_name', self.name)
        self.role = config.get('role', '')
        self.description = config.get('description', '')
        self.system_prompt_override = config.get('system_prompt_override')
        self.temperature = config.get('temperature')
        self.enabled = config.get('enabled', True)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'name': self.name,
            'display_name': self.display_name,
            'role': self.role,
            'description': self.description,
            'system_prompt_override': self.system_prompt_override,
            'temperature': self.temperature,
        }


class SimpleAgentManager:
    """简单的智能体管理器 - 无需复杂协作"""

    def __init__(self, config: dict):
        self.agents: Dict[str, AgentProfile] = {}
        self.active_agent_name: str = config.get('activeAgent', 'ai_tutor')

        # 加载智能体配置
        for agent_config in config.get('agents', []):
            if agent_config.get('enabled', True):
                profile = AgentProfile(agent_config)
                self.agents[profile.name] = profile

    def get_agent(self, name: str) -> Optional[AgentProfile]:
        """获取指定智能体"""
        return self.agents.get(name)

    def get_active_agent(self) -> Optional[AgentProfile]:
        """获取当前激活的智能体"""
        return self.agents.get(self.active_agent_name)

    def switch_agent(self, name: str) -> bool:
        """切换智能体"""
        if name in self.agents:
            self.active_agent_name = name
            return True
        return False

    def list_agents(self) -> list[dict]:
        """列出所有智能体"""
        return [agent.to_dict() for agent in self.agents.values()]
