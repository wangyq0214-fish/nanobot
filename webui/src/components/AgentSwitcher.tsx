import { useEffect, useState } from "react";
import { Bot, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useClient } from "@/providers/ClientProvider";

interface Agent {
  name: string;
  display_name: string;
  role: string;
  description: string;
  temperature?: number;
}

interface AgentSwitcherProps {
  onAgentChange?: (agent: Agent) => void;
}

export function AgentSwitcher({ onAgentChange }: AgentSwitcherProps) {
  const { token } = useClient();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [currentAgent, setCurrentAgent] = useState<Agent | null>(null);
  const [hasMultiAgent, setHasMultiAgent] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAgents();
    fetchCurrentAgent();
  }, []);

  const fetchAgents = async () => {
    try {
      const response = await fetch(`/api/agents?token=${encodeURIComponent(token)}`);
      console.log("Agents API response status:", response.status);
      const data = await response.json();
      console.log("Agents API data:", data);
      setAgents(data.agents || []);
      setHasMultiAgent(data.has_multi_agent);
    } catch (error) {
      console.error("Failed to fetch agents:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchCurrentAgent = async () => {
    try {
      const response = await fetch(`/api/agents/current?token=${encodeURIComponent(token)}`);
      const data = await response.json();
      if (data.agent) {
        setCurrentAgent(data.agent);
      }
    } catch (error) {
      console.error("Failed to fetch current agent:", error);
    }
  };

  const switchAgent = async (agent: Agent) => {
    try {
      const response = await fetch(`/api/agents/${agent.name}/switch?token=${encodeURIComponent(token)}`);
      const data = await response.json();
      if (data.success) {
        setCurrentAgent(agent);
        if (onAgentChange) {
          onAgentChange(agent);
        }
      }
    } catch (error) {
      console.error("Failed to switch agent:", error);
    }
  };

  if (loading || !hasMultiAgent || agents.length === 0) {
    return null;
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className="h-8.5 w-full justify-start gap-2 rounded-lg border border-sidebar-border/80 bg-card/25 px-3 text-[13px] font-medium text-sidebar-foreground shadow-none hover:bg-sidebar-accent/80"
        >
          <Bot className="h-3.5 w-3.5" />
          <span className="truncate">{currentAgent?.display_name || "选择智能体"}</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-[260px]">
        {agents.map((agent) => (
          <DropdownMenuItem
            key={agent.name}
            onClick={() => switchAgent(agent)}
            className="flex items-start gap-2 py-2.5 cursor-pointer"
          >
            <div className="flex h-5 w-5 items-center justify-center">
              {currentAgent?.name === agent.name && (
                <Check className="h-4 w-4 text-primary" />
              )}
            </div>
            <div className="flex-1 space-y-0.5">
              <div className="text-sm font-medium">{agent.display_name}</div>
              <div className="text-xs text-muted-foreground line-clamp-2">
                {agent.description}
              </div>
            </div>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
