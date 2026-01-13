"""GitHub issue tools."""

from __future__ import annotations

from typing import Any, Dict

from rig_core.rtp import CallContext, ToolError
from rig_core.runtime import RigToolRaised


def issues_create(
    args: Dict[str, Any], secrets: Dict[str, str], ctx: CallContext
) -> Dict[str, Any]:
    """Create a GitHub issue.
    
    Args:
        args: Input with repo, title, body, labels
        secrets: Must contain GITHUB_TOKEN
        ctx: Call context
        
    Returns:
        Issue number and URL
    """
    from github import Github, GithubException
    
    token = secrets.get("GITHUB_TOKEN")
    if not token:
        raise RigToolRaised(ToolError(
            type="auth_error",
            message="GITHUB_TOKEN not configured",
            retryable=False,
        ))
    
    try:
        g = Github(token)
        repo = g.get_repo(args["repo"])
        
        issue = repo.create_issue(
            title=args["title"],
            body=args.get("body", ""),
            labels=args.get("labels", []),
        )
        
        return {
            "number": issue.number,
            "url": issue.html_url,
            "state": issue.state,
        }
    except GithubException as e:
        raise RigToolRaised(ToolError(
            type="upstream_error",
            message=str(e),
            upstream_code=str(e.status),
            retryable=e.status in [502, 503],
        ))


def issues_comment(
    args: Dict[str, Any], secrets: Dict[str, str], ctx: CallContext
) -> Dict[str, Any]:
    """Comment on a GitHub issue.
    
    Args:
        args: Input with repo, issue_number, body
        secrets: Must contain GITHUB_TOKEN
        ctx: Call context
        
    Returns:
        Comment ID and URL
    """
    from github import Github, GithubException
    
    token = secrets.get("GITHUB_TOKEN")
    if not token:
        raise RigToolRaised(ToolError(
            type="auth_error",
            message="GITHUB_TOKEN not configured",
            retryable=False,
        ))
    
    try:
        g = Github(token)
        repo = g.get_repo(args["repo"])
        issue = repo.get_issue(args["issue_number"])
        
        comment = issue.create_comment(args["body"])
        
        return {
            "id": comment.id,
            "url": comment.html_url,
        }
    except GithubException as e:
        raise RigToolRaised(ToolError(
            type="upstream_error",
            message=str(e),
            upstream_code=str(e.status),
            retryable=False,
        ))

