"""Simple role-aware agent manager for education scenarios."""

from typing import Any


class AgentProfile:
    """Single agent profile loaded from configuration."""

    def __init__(self, config: dict[str, Any]):
        self.name = config["name"]
        self.display_name = config.get("display_name") or config.get("displayName") or self.name
        self.role = config.get("role", "")
        self.description = config.get("description", "")
        self.system_prompt_override = (
            config.get("system_prompt_override") or config.get("systemPromptOverride")
        )
        self.temperature = config.get("temperature")
        self.enabled = config.get("enabled", True)

    def to_dict(self) -> dict[str, Any]:
        """Convert to the JSON shape consumed by CLI and Web UI."""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "role": self.role,
            "description": self.description,
            "system_prompt_override": self.system_prompt_override,
            "temperature": self.temperature,
        }


class RoleAgentProfile:
    """Agent selection rules for one user role."""

    def __init__(self, config: dict[str, Any]):
        self.default_agent = config.get("default_agent") or config.get("defaultAgent") or ""
        self.available_agents = list(
            config.get("available_agents") or config.get("availableAgents") or []
        )
        self.traversal_flow = list(
            config.get("traversal_flow") or config.get("traversalFlow") or []
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "default_agent": self.default_agent,
            "available_agents": list(self.available_agents),
            "traversal_flow": list(self.traversal_flow),
        }


class SimpleAgentManager:
    """Role-aware manager for configured agent profiles."""

    def __init__(self, config: dict[str, Any]):
        self.agents: dict[str, AgentProfile] = {}
        self.active_agent_name: str = config.get("activeAgent", "ai_tutor")
        self.role_agents: dict[str, RoleAgentProfile] = {}
        self._active_by_role: dict[str, str] = {}

        for agent_config in config.get("agents", []):
            if agent_config.get("enabled", True):
                profile = AgentProfile(agent_config)
                self.agents[profile.name] = profile

        for role, role_config in (config.get("roleAgents") or {}).items():
            if isinstance(role_config, dict):
                profile = RoleAgentProfile(role_config)
                self.role_agents[role] = profile
                if profile.default_agent in self.agents:
                    self._active_by_role[role] = profile.default_agent

    def get_agent(self, name: str) -> AgentProfile | None:
        """Get one configured agent by name."""
        return self.agents.get(name)

    def get_active_agent(self, role: str | None = None) -> AgentProfile | None:
        """Get the globally active agent or the active agent for a role."""
        if role:
            role_active = self._active_by_role.get(role)
            if role_active:
                return self.agents.get(role_active)
            default_name = self.get_default_agent_for_role(role)
            if default_name:
                return self.agents.get(default_name)
        return self.agents.get(self.active_agent_name)

    def switch_agent(self, name: str, role: str | None = None) -> bool:
        """Switch active agent globally or within a role."""
        if name not in self.agents:
            return False
        if role:
            if not self.is_agent_allowed_for_role(name, role):
                return False
            self._active_by_role[role] = name
            return True
        self.active_agent_name = name
        return True

    def upsert_agent(self, config: dict[str, Any], role: str | None = None) -> AgentProfile:
        """Create or update an agent profile and optionally expose it to one role."""
        profile = AgentProfile(config)
        self.agents[profile.name] = profile

        if role:
            role_profile = self.role_agents.get(role)
            if role_profile is None:
                role_profile = RoleAgentProfile({
                    "defaultAgent": profile.name,
                    "availableAgents": [profile.name],
                    "traversalFlow": [profile.name],
                })
                self.role_agents[role] = role_profile
                self._active_by_role.setdefault(role, profile.name)
            else:
                if profile.name not in role_profile.available_agents:
                    role_profile.available_agents.append(profile.name)
                if profile.name not in role_profile.traversal_flow:
                    role_profile.traversal_flow.append(profile.name)
                if not role_profile.default_agent:
                    role_profile.default_agent = profile.name
                self._active_by_role.setdefault(role, role_profile.default_agent or profile.name)

        return profile

    def list_agents(self, role: str | None = None) -> list[dict[str, Any]]:
        """List all agents, or only agents available to one role."""
        if not role or role not in self.role_agents:
            return [agent.to_dict() for agent in self.agents.values()]
        allowed = self.role_agents[role].available_agents
        if not allowed:
            return [agent.to_dict() for agent in self.agents.values()]
        return [
            self.agents[name].to_dict()
            for name in allowed
            if name in self.agents
        ]

    def get_default_agent_for_role(self, role: str) -> str | None:
        """Return the configured default agent name for a role."""
        profile = self.role_agents.get(role)
        if not profile:
            return None
        if profile.default_agent in self.agents:
            return profile.default_agent
        return None

    def get_traversal_flow_for_role(self, role: str) -> list[str]:
        """Return enabled traversal agent names for a role."""
        profile = self.role_agents.get(role)
        if not profile:
            return []
        return [name for name in profile.traversal_flow if name in self.agents]

    def is_agent_allowed_for_role(self, name: str, role: str) -> bool:
        """Return True if an agent can be selected by the given role."""
        profile = self.role_agents.get(role)
        if not profile or not profile.available_agents:
            return True
        return name in profile.available_agents


def manager_config_from_defaults(defaults: Any) -> dict[str, Any]:
    """Build SimpleAgentManager config from AgentDefaults-like objects."""
    return {
        "activeAgent": defaults.active_agent or "ai_tutor",
        "agents": [a.model_dump(by_alias=False) for a in defaults.agents],
        "roleAgents": {
            role: cfg.model_dump(by_alias=False)
            for role, cfg in getattr(defaults, "role_agents", {}).items()
        },
    }
