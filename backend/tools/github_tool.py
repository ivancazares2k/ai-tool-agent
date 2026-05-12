import os
from github import Github
from dotenv import load_dotenv

load_dotenv()

def get_github_client():
    return Github(os.getenv("GITHUB_TOKEN"))

async def create_github_issue(repo_name: str, title: str, body: str) -> str:
    try:
        g = get_github_client()
        repo = g.get_repo(repo_name)
        issue = repo.create_issue(title=title, body=body)
        return f"Issue created: {issue.html_url}"
    except Exception as e:
        return f"Error creating issue: {e}"

async def get_github_repos() -> str:
    try:
        g = get_github_client()
        user = g.get_user()
        repos = list(user.get_repos())[:10]
        output = []
        for repo in repos:
            output.append(f"- {repo.full_name} — {repo.description or 'No description'}")
        return "\n".join(output)
    except Exception as e:
        return f"Error fetching repos: {e}"