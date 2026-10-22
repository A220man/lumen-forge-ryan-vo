from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from app.core.database import get_session
from app.services.github_sync import sync_issues, get_issues, get_issue
from app.services.ai_analysis import llm_client, LLMProviderError
from app.models.issue import IssueAnalysis


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
    
    # Store analysis
    stored = await IssueAnalysis.create_analysis(
        db=db,
        issue_id=issue_id,
        summary=analysis["summary"],
        key_points=analysis["key_points"],
        blockers=analysis["blockers"],
        unresolved_questions=analysis["unresolved_questions"],
        provider=llm_client.provider,
        model=llm_client.model,
        raw_response=json.dumps(analysis) if isinstance(analysis, dict) else None,
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


# Need to add these methods to IssueAnalysis class
import json
from app.models.issue import IssueAnalysis as IssueAnalysisModel

# Monkey-patch class methods
async def _create_analysis(
    db: AsyncSession,
    issue_id: int,
    summary: str,
    key_points: List[str],
    blockers: List[str],
    unresolved_questions: List[str],
    provider: str,
    model: str,
    raw_response: Optional[str] = None,
) -> IssueAnalysisModel:
    analysis = IssueAnalysisModel(
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


async def _get_analyses(db: AsyncSession, issue_id: int) -> List[Dict[str, Any]]:
    from sqlalchemy import select
    result = await db.execute(
        select(IssueAnalysisModel).where(IssueAnalysisModel.issue_id == issue_id).order_by(IssueAnalysisModel.created_at.desc())
    )
    analyses = result.scalars().all()
    return [a.to_dict() for a in analyses]


IssueAnalysis.create_analysis = staticmethod(_create_analysis)
IssueAnalysis.get_analyses = staticmethod(_get_analyses)