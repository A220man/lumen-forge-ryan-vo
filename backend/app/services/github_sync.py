import json
import httpx
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.issue import Issue, IssueAnalysis
from app.core.config import settings


GITHUB_API_BASE = "https://api.github.com"
TRACKING_ISSUE_NUMBERS = [
    31844,  # specialization
    43467,  # extern types
    81513,  # pointer metadata
    130703,  # secure random
    63063,  # impl trait in type aliases
    110998,  # ascii::Char
    88581,  # int_roundings
    43122,  # coroutines
]


async def fetch_issue(issue_number: int, client: httpx.AsyncClient) -> Optional[Dict[str, Any]]:
    """Fetch a single issue from GitHub API."""
    url = f"{GITHUB_API_BASE}/repos/rust-lang/rust/issues/{issue_number}"
    response = await client.get(url)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


async def fetch_issue_comments(issue_number: int, client: httpx.AsyncClient) -> List[Dict[str, Any]]:
    """Fetch comments for an issue from GitHub API."""
    url = f"{GITHUB_API_BASE}/repos/rust-lang/rust/issues/{issue_number}/comments"
    all_comments = []
    page = 1
    while True:
        response = await client.get(url, params={"page": page, "per_page": 100})
        response.raise_for_status()
        comments = response.json()
        if not comments:
            break
        all_comments.extend(comments)
        page += 1
    return all_comments


async def sync_issues(db: AsyncSession) -> Dict[str, Any]:
    """Sync tracking issues from GitHub to local database."""
    stats = {"created": 0, "updated": 0, "errors": 0}
    
    async with httpx.AsyncClient(
        timeout=30.0,
        headers={"User-Agent": "lumen-forge-ryan-vo/1.0"}
    ) as client:
        for issue_number in TRACKING_ISSUE_NUMBERS:
            try:
                issue_data = await fetch_issue(issue_number, client)
                if not issue_data:
                    stats["errors"] += 1
                    continue
                
                comments = await fetch_issue_comments(issue_number, client)
                
                # Check if issue exists
                result = await db.execute(select(Issue).where(Issue.id == issue_number))
                existing = result.scalar_one_or_none()
                
                labels = json.dumps([label["name"] for label in issue_data.get("labels", [])])
                assignees = json.dumps([a["login"] for a in issue_data.get("assignees", [])])
                raw_data = json.dumps({"issue": issue_data, "comments": comments})
                
                if existing:
                    # Update existing
                    existing.title = issue_data["title"]
                    existing.body = issue_data.get("body")
                    existing.html_url = issue_data["html_url"]
                    existing.state = issue_data["state"]
                    existing.labels = labels
                    existing.assignees = assignees
                    existing.comments_count = len(comments)
                    existing.updated_at = datetime.fromisoformat(issue_data["updated_at"].replace("Z", "+00:00"))
                    existing.closed_at = datetime.fromisoformat(issue_data["closed_at"].replace("Z", "+00:00")) if issue_data.get("closed_at") else None
                    existing.author_login = issue_data["user"]["login"]
                    existing.author_html_url = issue_data["user"]["html_url"]
                    existing.raw_data = raw_data
                    existing.synced_at = datetime.utcnow()
                    stats["updated"] += 1
                else:
                    # Create new
                    new_issue = Issue(
                        id=issue_number,
                        title=issue_data["title"],
                        body=issue_data.get("body"),
                        html_url=issue_data["html_url"],
                        state=issue_data["state"],
                        labels=labels,
                        assignees=assignees,
                        comments_count=len(comments),
                        created_at=datetime.fromisoformat(issue_data["created_at"].replace("Z", "+00:00")),
                        updated_at=datetime.fromisoformat(issue_data["updated_at"].replace("Z", "+00:00")),
                        closed_at=datetime.fromisoformat(issue_data["closed_at"].replace("Z", "+00:00")) if issue_data.get("closed_at") else None,
                        author_login=issue_data["user"]["login"],
                        author_html_url=issue_data["user"]["html_url"],
                        raw_data=raw_data,
                    )
                    db.add(new_issue)
                    stats["created"] += 1
                    
            except Exception as e:
                stats["errors"] += 1
                # Log error in production
                continue
        
        await db.commit()
    
    return stats


async def get_issues(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    state: Optional[str] = None,
    search: Optional[str] = None,
    label: Optional[str] = None,
) -> Dict[str, Any]:
    """Get paginated, filtered list of issues."""
    query = select(Issue)
    
    if state:
        query = query.where(Issue.state == state)
    if search:
        query = query.where(Issue.title.ilike(f"%{search}%") | Issue.body.ilike(f"%{search}%"))
    if label:
        query = query.where(Issue.labels.ilike(f"%{label}%"))
    
    query = query.order_by(Issue.updated_at.desc())
    
    # Count total
    count_query = query.with_only_columns(Issue.id)
    total_result = await db.execute(count_query)
    total = len(total_result.scalars().all())
    
    # Paginate
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    issues = result.scalars().all()
    
    return {
        "items": [issue.to_dict() for issue in issues],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


async def get_issue(db: AsyncSession, issue_id: int) -> Optional[Dict[str, Any]]:
    """Get a single issue by ID with full details."""
    result = await db.execute(select(Issue).where(Issue.id == issue_id))
    issue = result.scalar_one_or_none()
    if not issue:
        return None
    
    data = issue.to_dict()
    # Include comments from raw_data
    if issue.raw_data:
        import json
        raw = json.loads(issue.raw_data)
        data["comments"] = raw.get("comments", [])
    return data


async def create_analysis(
    db: AsyncSession,
    issue_id: int,
    summary: str,
    key_points: List[str],
    blockers: List[str],
    unresolved_questions: List[str],
    provider: str,
    model: str,
    raw_response: Optional[str] = None,
) -> IssueAnalysis:
    """Store an AI analysis result."""
    analysis = IssueAnalysis(
        issue_id=issue_id,
        summary=summary,
        key_points=json.dumps(key_points),
        blockers=json.dumps(blockers),
        unresolved_questions=json.dumps(unresolved_questions),
        provider=provider,
        model=model,
        raw_response=raw_response,
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)
    return analysis


async def get_analyses(db: AsyncSession, issue_id: int) -> List[Dict[str, Any]]:
    """Get all analyses for an issue."""
    result = await db.execute(
        select(IssueAnalysis).where(IssueAnalysis.issue_id == issue_id).order_by(IssueAnalysis.created_at.desc())
    )
    analyses = result.scalars().all()
    return [a.to_dict() for a in analyses]