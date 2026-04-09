"""Mygithubtriage Environment Client."""

"""Mygithubtriage Environment Client."""

from typing import Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

try:
    from .models import MygithubtriageAction, MygithubtriageObservation
except (ImportError, ValueError):
    try:
        from models import MygithubtriageAction, MygithubtriageObservation
    except ImportError:
        from server.models import MygithubtriageAction, MygithubtriageObservation


class MygithubtriageEnv(
    EnvClient[MygithubtriageAction, MygithubtriageObservation, State]
):
    """
    Client for the Mygithubtriage Environment.
    """

    def _step_payload(self, action: MygithubtriageAction) -> Dict:
        """
        Convert MygithubtriageAction to JSON payload for step message.
        """
        return {
            "apply_labels": action.apply_labels,
            "remove_labels": action.remove_labels,
            "assign_to": action.assign_to,
            "leave_comment": action.leave_comment,
            "submit_decision": action.submit_decision,
        }

    def _parse_result(self, payload: Dict) -> StepResult[MygithubtriageObservation]:
        """
        Parse server response into StepResult[MygithubtriageObservation].
        """
        obs_data = payload.get("observation", {})
        observation = MygithubtriageObservation(
            issue_id=obs_data.get("issue_id", 0),
            title=obs_data.get("title", ""),
            body=obs_data.get("body", ""),
            author=obs_data.get("author", ""),
            current_labels=obs_data.get("current_labels", []),
            current_assignees=obs_data.get("current_assignees", []),
            comments=obs_data.get("comments", []),
            available_labels=obs_data.get("available_labels", []),
            available_assignees=obs_data.get("available_assignees", []),
            task_difficulty=obs_data.get("task_difficulty", ""),
            feedback=obs_data.get("feedback", ""),
            done=payload.get("done", False),
            reward=payload.get("reward", 0.0),
            metadata=obs_data.get("metadata", {}),
        )

        return StepResult(
            observation=observation,
            reward=payload.get("reward", 0.0),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> State:
        """
        Parse server response into State object.
        """
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )
