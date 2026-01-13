"""GitHub pull request tools."""

from __future__ import annotations

from typing import Any, Dict

from rig_core.rtp import CallContext, ToolError
from rig_core.runtime import RigToolRaised


def pulls_create(
    args: Dict[str, Any], secrets: Dict[str, str], ctx: CallContext
) -> Dict[str, Any]:
    """Create a GitHub pull request.
    
    Args:
        args: Input with repo, title, head, base, body
        secrets: Must contain GITHUB_TOKEN
        ctx: Call context
        
    Returns:
        PR number and URL
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
        
        pr = repo.create_pull(
            title=args["title"],
            head=args["head"],
            base=args.get("base", "main"),
            body=args.get("body", ""),
        )
        
        return {
            "number": pr.number,
            "url": pr.html_url,
            "state": pr.state,
        }
    except GithubException as e:
        raise RigToolRaised(ToolError(
            type="upstream_error",
            message=str(e),
            upstream_code=str(e.status),
            retryable=False,
        ))


def pulls_list(
    args: Dict[str, Any], secrets: Dict[str, str], ctx: CallContext
) -> Dict[str, Any]:
    """List GitHub pull requests.
    
    Args:
        args: Input with repo, state, base
        secrets: Must contain GITHUB_TOKEN
        ctx: Call context
        
    Returns:
        List of PRs
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
        
        prs = repo.get_pulls(
            state=args.get("state", "open"),
            base=args.get("base"),
        )
        
        result = []
        for pr in prs[:args.get("limit", 20)]:
            result.append({
                "number": pr.number,
                "title": pr.title,
                "state": pr.state,
                "url": pr.html_url,
            })
        
        return {"pull_requests": result}
    except GithubException as e:
        raise RigToolRaised(ToolError(
            type="upstream_error",
            message=str(e),
            upstream_code=str(e.status),
            retryable=False,
        ))

