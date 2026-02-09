"""GitHub data ingestor.

Handles:
- Commit messages and patterns
- Pull request descriptions and reviews
- Code review comments
- Issue discussions
"""

from datetime import datetime
from typing import Any

import structlog
from github import Github
from github.PullRequest import PullRequest
from github.Repository import Repository

from src.core.config import get_settings
from src.core.models import MessageType, Source

logger = structlog.get_logger()
settings = get_settings()


class GitHubIngestor:
    """Ingestor for GitHub activity."""

    def __init__(self):
        self.client = Github(settings.github_token) if settings.github_token else None

    async def ingest_commits(
        self, 
        repo_name: str, 
        author: str | None = None,
        limit: int = 100
    ) -> list[dict[str, Any]]:
        """
        Ingest commit messages from a repository.
        
        Useful for learning commit message patterns.
        """
        if not self.client:
            logger.error("GitHub client not configured")
            return []

        try:
            repo = self.client.get_repo(repo_name)
            commits = repo.get_commits(author=author)[:limit] if author else repo.get_commits()[:limit]
            
            messages = []
            for commit in commits:
                messages.append({
                    "source": Source.GITHUB,
                    "message_type": MessageType.COMMIT,
                    "content": commit.commit.message,
                    "author": commit.commit.author.name,
                    "timestamp": commit.commit.author.date,
                    "metadata": {
                        "sha": commit.sha[:7],
                        "repo": repo_name,
                        "additions": commit.stats.additions if commit.stats else 0,
                        "deletions": commit.stats.deletions if commit.stats else 0,
                        "files_changed": len(commit.files) if commit.files else 0,
                    },
                })
            
            logger.info("Ingested commits", repo=repo_name, count=len(messages))
            return messages

        except Exception as e:
            logger.error("GitHub API error", error=str(e))
            return []

    async def ingest_pr_reviews(
        self, 
        repo_name: str,
        author: str | None = None,
        limit: int = 50
    ) -> list[dict[str, Any]]:
        """
        Ingest pull request reviews.
        
        Captures code review patterns and feedback style.
        """
        if not self.client:
            logger.error("GitHub client not configured")
            return []

        try:
            repo = self.client.get_repo(repo_name)
            pulls = repo.get_pulls(state="all")[:limit]
            
            reviews = []
            for pr in pulls:
                for review in pr.get_reviews():
                    if author and review.user.login != author:
                        continue
                    
                    if not review.body:  # Skip empty reviews
                        continue
                    
                    reviews.append({
                        "source": Source.GITHUB,
                        "message_type": MessageType.PR_REVIEW,
                        "content": review.body,
                        "author": review.user.login,
                        "timestamp": review.submitted_at,
                        "metadata": {
                            "repo": repo_name,
                            "pr_number": pr.number,
                            "pr_title": pr.title,
                            "state": review.state,  # APPROVED, CHANGES_REQUESTED, etc.
                        },
                    })
            
            logger.info("Ingested PR reviews", repo=repo_name, count=len(reviews))
            return reviews

        except Exception as e:
            logger.error("GitHub API error", error=str(e))
            return []

    async def ingest_review_comments(
        self, 
        repo_name: str,
        author: str | None = None,
        limit: int = 100
    ) -> list[dict[str, Any]]:
        """
        Ingest inline code review comments.
        
        These are the specific line-by-line feedback comments.
        """
        if not self.client:
            logger.error("GitHub client not configured")
            return []

        try:
            repo = self.client.get_repo(repo_name)
            comments = repo.get_pulls_review_comments()[:limit]
            
            result = []
            for comment in comments:
                if author and comment.user.login != author:
                    continue
                
                result.append({
                    "source": Source.GITHUB,
                    "message_type": MessageType.PR_REVIEW,
                    "content": comment.body,
                    "author": comment.user.login,
                    "timestamp": comment.created_at,
                    "metadata": {
                        "repo": repo_name,
                        "path": comment.path,
                        "line": comment.line,
                        "diff_hunk": comment.diff_hunk[:200] if comment.diff_hunk else None,
                    },
                })
            
            logger.info("Ingested review comments", repo=repo_name, count=len(result))
            return result

        except Exception as e:
            logger.error("GitHub API error", error=str(e))
            return []

    async def ingest_all_activity(
        self, 
        username: str,
        repos: list[str] | None = None
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Ingest all GitHub activity for a user.
        
        Returns organized by type: commits, reviews, comments.
        """
        if not self.client:
            logger.error("GitHub client not configured")
            return {}

        # Get user's repos if not specified
        if not repos:
            user = self.client.get_user(username)
            repos = [r.full_name for r in user.get_repos()[:20]]  # Limit to 20 repos

        result = {
            "commits": [],
            "reviews": [],
            "comments": [],
        }

        for repo_name in repos:
            try:
                result["commits"].extend(await self.ingest_commits(repo_name, username, 50))
                result["reviews"].extend(await self.ingest_pr_reviews(repo_name, username, 20))
                result["comments"].extend(await self.ingest_review_comments(repo_name, username, 50))
            except Exception as e:
                logger.warning("Failed to ingest repo", repo=repo_name, error=str(e))

        logger.info(
            "Ingested all GitHub activity",
            user=username,
            commits=len(result["commits"]),
            reviews=len(result["reviews"]),
            comments=len(result["comments"]),
        )
        
        return result
