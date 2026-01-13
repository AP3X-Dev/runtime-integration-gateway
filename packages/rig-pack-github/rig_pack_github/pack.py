"""GitHub pack registration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from rig_core.rtp import ToolDef
from rig_core.runtime import RegisteredTool

from rig_pack_github.tools import issues_create, issues_comment, pulls_create, pulls_list


TOOL_DEFS = [
    ToolDef(
        name="github.issues.create",
        description="Create a GitHub issue",
        input_schema={
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "Repository (owner/repo)"},
                "title": {"type": "string", "description": "Issue title"},
                "body": {"type": "string", "description": "Issue body"},
                "labels": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["repo", "title"],
        },
        output_schema={
            "type": "object",
            "properties": {"number": {"type": "integer"}, "url": {"type": "string"}},
        },
        error_schema={"type": "object"},
        auth_slots=["GITHUB_TOKEN"],
        risk_class="write",
    ),
    ToolDef(
        name="github.issues.comment",
        description="Comment on a GitHub issue",
        input_schema={
            "type": "object",
            "properties": {
                "repo": {"type": "string"},
                "issue_number": {"type": "integer"},
                "body": {"type": "string"},
            },
            "required": ["repo", "issue_number", "body"],
        },
        output_schema={
            "type": "object",
            "properties": {"id": {"type": "integer"}, "url": {"type": "string"}},
        },
        error_schema={"type": "object"},
        auth_slots=["GITHUB_TOKEN"],
        risk_class="write",
    ),
    ToolDef(
        name="github.pulls.create",
        description="Create a GitHub pull request",
        input_schema={
            "type": "object",
            "properties": {
                "repo": {"type": "string"},
                "title": {"type": "string"},
                "head": {"type": "string", "description": "Branch with changes"},
                "base": {"type": "string", "description": "Target branch"},
                "body": {"type": "string"},
            },
            "required": ["repo", "title", "head"],
        },
        output_schema={
            "type": "object",
            "properties": {"number": {"type": "integer"}, "url": {"type": "string"}},
        },
        error_schema={"type": "object"},
        auth_slots=["GITHUB_TOKEN"],
        risk_class="write",
    ),
    ToolDef(
        name="github.pulls.list",
        description="List GitHub pull requests",
        input_schema={
            "type": "object",
            "properties": {
                "repo": {"type": "string"},
                "state": {"type": "string", "enum": ["open", "closed", "all"]},
                "limit": {"type": "integer", "default": 20},
            },
            "required": ["repo"],
        },
        output_schema={
            "type": "object",
            "properties": {"pull_requests": {"type": "array"}},
        },
        error_schema={"type": "object"},
        auth_slots=["GITHUB_TOKEN"],
        risk_class="read",
    ),
]

TOOL_IMPLS = {
    "github.issues.create": issues_create,
    "github.issues.comment": issues_comment,
    "github.pulls.create": pulls_create,
    "github.pulls.list": pulls_list,
}


@dataclass
class GitHubPack:
    name: str = "rig-pack-github"
    version: str = "0.1.0"
    
    def rig_pack_metadata(self) -> Dict[str, str]:
        return {"name": self.name, "version": self.version}
    
    def rig_tools(self) -> List[ToolDef]:
        return TOOL_DEFS
    
    def rig_impls(self) -> Dict[str, RegisteredTool]:
        result = {}
        for tool in TOOL_DEFS:
            if tool.name in TOOL_IMPLS:
                result[tool.name] = RegisteredTool(
                    tool=tool, impl=TOOL_IMPLS[tool.name],
                    pack=self.name, pack_version=self.version,
                )
        return result


PACK = GitHubPack()

