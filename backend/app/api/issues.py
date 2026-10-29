from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from app.core.database import get_session
from app.services.github_sync import sync_issues, get_issues, get_issue, create_analysis, get_analyses
from app.services.ai_analysis import llm_client, LLMProviderError


router = APIRouter(prefix="/issues", tags=["issues"])


class IssueResponse(BaseModel):
    items: List[dict]
    total: int
    page: int
    page_size: int
    total_pages: int


class AnalysisRequest(BaseModel):
    pass  # No input needed, uses issue data


class AnalysisResponse(BaseModel):
    id: int
    issue_id: int
    summary: str
    key_points: List[str]
    blockers: List[str]
    unresolved_questions: List[str]
    provider: str
    model: str
    created_at: str
    raw_response: Optional[str] = None
    advisory: bool = True


@router.get("", response_model=IssueResponse)
async def list_issues(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    state: Optional[str] = Query(None, pattern="^(open|closed)$"),
    search: Optional[str] = Query(None),
    label: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_session),
):
    """List tracking issues with pagination and filtering."""
    result = await get_issues(db, page, page_size, state, search, label)
    return result


@router.get("/{issue_id}")
async def get_issue_detail(
    issue_id: int,
    db: AsyncSession = Depends(get_session),
):
    """Get detailed issue information including comments."""
    issue = await get_issue(db, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue


@router.post("/sync")
async def sync_github_issues(
    db: AsyncSession = Depends(get_session),
):
    """Sync tracking issues from GitHub."""
    stats = await sync_issues(db)
    return stats


@router.post("/{issue_id}/analyze", response_model=AnalysisResponse)
async def analyze_issue(
    issue_id: int,
    db: AsyncSession = Depends(get_session),
):
    """Generate AI analysis of an issue (opt-in, requires LLM_API_KEY)."""
    # Verify issue exists
    issue = await get_issue(db, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    if not llm_client.is_available():
        raise HTTPException(
            status_code=503,
            detail="LLM analysis not available. Configure LLM_API_KEY to enable.",
        )
    
    # Extract comments from issue data
    comments = issue.get("comments", [])
    
    try:
        analysis = await llm_client.analyze_issue(
            issue_title=issue["title"],
            issue_body=issue["body"] or "",
            comments=comments,
        )
    except LLMProviderError as e:
        raise HTTPException(status_code=502, detail=f"LLM provider error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    
    # Store analysis using service function
    stored = await create_analysis(
        db=db,
        issue_id=issue_id,
        summary=analysis["summary"],
        key_points=analysis["key_points"],
        blockers=analysis["blockers"],
        unresolved_questions=analysis["unresolved_questions"],
        provider=llm_client.provider,
        model=llm_client.model,
        raw_response=analysis.get("raw_response"),
    )
    
    result = stored.to_dict()
    result["advisory"] = True
    return result


@router.get("/{issue_id}/analyses")
async def list_analyses(
    issue_id: int,
    db: AsyncSession = Depends(get_session),
):
    """List all AI analyses for an issue."""
    # Verify issue exists
    issue = await get_issue(db, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    analyses = await get_analyses(db, issue_id)
    # Add advisory flag
    for a in analyses:
        a["advisory"] = True
    return analyses

