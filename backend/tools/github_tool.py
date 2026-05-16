import os
import base64
from github import Github, GithubException


def _get_client() -> Github:
    """Initialize GitHub client using token from environment."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN environment variable not set.")
    return Github(token)


async def get_repo_structure(repo_name: str, path: str = "") -> str:
    """
    List the file and folder structure of a GitHub repository.

    Args:
        repo_name: Full repo name in 'owner/repo' format (e.g. 'getshipstack/memory-agent')
        path: Subdirectory path to list (defaults to root)

    Returns:
        A formatted string listing the repo contents at the given path
    """
    try:
        g = _get_client()
        repo = g.get_repo(repo_name)
        contents = repo.get_contents(path)

        lines = [f"Repo: {repo_name}", f"Path: /{path or ''}", ""]
        for item in sorted(contents, key=lambda x: (x.type != "dir", x.name)):
            prefix = "📁" if item.type == "dir" else "📄"
            lines.append(f"{prefix} {item.name}")

        return "\n".join(lines)
    except GithubException as e:
        return f"GitHub error: {e.status} — {e.data.get('message', str(e))}"


async def read_file(repo_name: str, file_path: str, branch: str = "main") -> str:
    """
    Read the contents of a file from a GitHub repository.

    Args:
        repo_name: Full repo name in 'owner/repo' format
        file_path: Path to the file within the repo (e.g. 'src/main.py')
        branch: Branch to read from (defaults to 'main')

    Returns:
        The decoded file contents as a string
    """
    try:
        g = _get_client()
        repo = g.get_repo(repo_name)
        file = repo.get_contents(file_path, ref=branch)
        content = base64.b64decode(file.content).decode("utf-8")
        return f"File: {file_path} (branch: {branch})\n\n{content}"
    except GithubException as e:
        return f"GitHub error: {e.status} — {e.data.get('message', str(e))}"


async def push_file(
    repo_name: str,
    file_path: str,
    content: str,
    commit_message: str,
    branch: str = "main",
) -> str:
    """
    Create or update a file directly in a GitHub repository.

    Args:
        repo_name: Full repo name in 'owner/repo' format
        file_path: Path to the file within the repo (e.g. 'docs/README.md')
        content: New file content as a plain string
        commit_message: Commit message describing the change
        branch: Branch to push to (defaults to 'main')

    Returns:
        A confirmation string with the commit SHA
    """
    try:
        g = _get_client()
        repo = g.get_repo(repo_name)
        encoded = content.encode("utf-8")

        try:
            existing = repo.get_contents(file_path, ref=branch)
            result = repo.update_file(
                path=file_path,
                message=commit_message,
                content=encoded,
                sha=existing.sha,
                branch=branch,
            )
            action = "Updated"
        except GithubException:
            result = repo.create_file(
                path=file_path,
                message=commit_message,
                content=encoded,
                branch=branch,
            )
            action = "Created"

        sha = result["commit"].sha
        return f"{action} '{file_path}' on branch '{branch}'. Commit: {sha}"
    except GithubException as e:
        return f"GitHub error: {e.status} — {e.data.get('message', str(e))}"


async def create_pr(
    repo_name: str,
    title: str,
    body: str,
    head_branch: str,
    base_branch: str = "main",
) -> str:
    """
    Open a pull request in a GitHub repository.

    Args:
        repo_name: Full repo name in 'owner/repo' format
        title: Title of the pull request
        body: Description / body text of the pull request
        head_branch: Branch containing the changes to merge
        base_branch: Target branch to merge into (defaults to 'main')

    Returns:
        A confirmation string with the PR URL and number
    """
    try:
        g = _get_client()
        repo = g.get_repo(repo_name)
        pr = repo.create_pull(
            title=title,
            body=body,
            head=head_branch,
            base=base_branch,
        )
        return f"PR #{pr.number} created: {pr.html_url}"
    except GithubException as e:
        return f"GitHub error: {e.status} — {e.data.get('message', str(e))}"


async def list_issues(repo_name: str, state: str = "open") -> str:
    """
    List issues in a GitHub repository.

    Args:
        repo_name: Full repo name in 'owner/repo' format
        state: Filter by issue state — 'open', 'closed', or 'all' (defaults to 'open')

    Returns:
        A formatted string listing issues with their numbers, titles, and URLs
    """
    try:
        g = _get_client()
        repo = g.get_repo(repo_name)
        issues = repo.get_issues(state=state)

        results = [f"Issues in {repo_name} ({state}):\n"]
        count = 0
        for issue in issues:
            if issue.pull_request:
                continue  # skip PRs that appear in issues list
            results.append(f"#{issue.number} — {issue.title}\n  {issue.html_url}")
            count += 1

        if count == 0:
            return f"No {state} issues found in {repo_name}."

        return "\n".join(results)
    except GithubException as e:
        return f"GitHub error: {e.status} — {e.data.get('message', str(e))}"


async def create_issue(
    repo_name: str,
    title: str,
    body: str = "",
    labels: list = None,
) -> str:
    """
    Create a new issue in a GitHub repository.

    Args:
        repo_name: Full repo name in 'owner/repo' format
        title: Title of the issue
        body: Description / body text of the issue (optional)
        labels: List of label names to apply (optional)

    Returns:
        A confirmation string with the issue URL and number
    """
    try:
        g = _get_client()
        repo = g.get_repo(repo_name)

        kwargs = {"title": title, "body": body}
        if labels:
            kwargs["labels"] = labels

        issue = repo.create_issue(**kwargs)
        return f"Issue #{issue.number} created: {issue.html_url}"
    except GithubException as e:
        return f"GitHub error: {e.status} — {e.data.get('message', str(e))}"
