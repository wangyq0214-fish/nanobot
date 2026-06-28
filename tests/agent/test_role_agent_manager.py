from nanobot.agent.manager import SimpleAgentManager, manager_config_from_defaults
from nanobot.config.schema import AgentDefaults


def _manager() -> SimpleAgentManager:
    defaults = AgentDefaults.model_validate(
        {
            "activeAgent": "teacher_lesson",
            "agents": [
                {
                    "name": "student_tutor",
                    "displayName": "Student Tutor",
                    "description": "Helps students",
                    "systemPromptOverride": "student prompt",
                },
                {
                    "name": "teacher_lesson",
                    "displayName": "Teacher Lesson",
                    "description": "Helps teachers",
                    "systemPromptOverride": "teacher prompt",
                },
                {
                    "name": "researcher_lit",
                    "displayName": "Researcher Literature",
                    "description": "Helps researchers",
                    "systemPromptOverride": "researcher prompt",
                },
            ],
            "roleAgents": {
                "student": {
                    "defaultAgent": "student_tutor",
                    "availableAgents": ["student_tutor"],
                    "traversalFlow": ["student_tutor", "missing_agent"],
                },
                "teacher": {
                    "defaultAgent": "teacher_lesson",
                    "availableAgents": ["teacher_lesson"],
                },
                "researcher": {
                    "defaultAgent": "researcher_lit",
                    "availableAgents": ["researcher_lit"],
                },
            },
        }
    )
    return SimpleAgentManager(manager_config_from_defaults(defaults))


def test_role_agents_are_filtered_by_role() -> None:
    manager = _manager()

    assert [a["name"] for a in manager.list_agents("student")] == ["student_tutor"]
    assert [a["name"] for a in manager.list_agents("teacher")] == ["teacher_lesson"]
    assert [a["name"] for a in manager.list_agents("researcher")] == ["researcher_lit"]


def test_role_default_agent_is_used() -> None:
    manager = _manager()

    assert manager.get_active_agent("student").name == "student_tutor"
    assert manager.get_active_agent("teacher").name == "teacher_lesson"
    assert manager.get_active_agent("researcher").name == "researcher_lit"


def test_role_switch_rejects_agents_outside_role() -> None:
    manager = _manager()

    assert manager.switch_agent("teacher_lesson", role="student") is False
    assert manager.get_active_agent("student").name == "student_tutor"


def test_role_traversal_flow_ignores_missing_agents() -> None:
    manager = _manager()

    assert manager.get_traversal_flow_for_role("student") == ["student_tutor"]
