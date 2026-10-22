import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from app.main import app
from app.core.database import get_session, Base, engine
from app.models.issue import Issue, IssueAnalysis
from app.services.github_sync import sync_issues, get_issues, get_issue, create_analysis, get_analyses
from app.services.ai_analysis import LLMClient, LLMProviderError


@pytest.mark.asyncio
async def test_sync_issues_creates_new_issues(db_session: AsyncSession):
    """Test sync_issues creates new issues from GitHub data."""
    # Mock GitHub API response
    mock_issue_data = {
        "number": 31844,
        "title": "Tracking issue for specialization (RFC 1210)",
        "body": "This is a tracking issue...",
        "html_url": "https://github.com/rust-lang/rust/issues/31844",
        "state": "open",
        "labels": [{"name": "tracking-issue"}, {"name": "F-specialization"}],
        "assignees": [{"login": "rustbot"}],
        "comments": 323,
        "created_at": "2016-03-15T12:00:00Z",
        "updated_at": "2024-01-15T12:00:00Z",
        "closed_at": None,
        "user": {"login": "aturon", "html_url": "https://github.com/aturon"},
    }
    
    mock_comments = [
        {"user": {"login": "user1"}, "body": "Comment 1"},
        {"user": {"login": "user2"}, "body": "Comment 2"},
    ]
    
    with patch("app.services.github_sync.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Mock fetch_issue
        async def mock_fetch(issue_number, client):
            return mock_issue_data
        
        # Mock fetch_issue_comments
        async def mock_fetch_comments(issue_number, client):
            return mock_comments
        
        with patch("app.services.github_sync.fetch_issue", side_effect=mock_fetch):
            with patch("app.services.github_sync.fetch_issue_comments", side_effect=mock_fetch_comments):
                stats = await sync_issues(db_session)
    
    # sync_issues syncs all TRACKING_ISSUE_NUMBERS (8 issues)
    assert stats["created"] == 8
    assert stats["updated"] == 0
    assert stats["errors"] == 0
    
    # Verify issue was stored
    from sqlalchemy import text
    result = await db_session.execute(
        text("SELECT * FROM issues WHERE id = 31844")
    )
    issue = result.fetchone()
    assert issue is not None
    assert issue.title == "Tracking issue for specialization (RFC 1210)"
    assert issue.state == "open"
    assert issue.comments_count == 2


@pytest.mark.asyncio
async def test_get_issues_pagination(db_session: AsyncSession):
    """Test get_issues returns paginated results."""
    # Create test issues
    base_time = datetime(2024, 1, 1, 0, 0, 0)
    for i in range(25):
        issue = Issue(
            id=1000 + i,
            title=f"Test Issue {i}",
            body=f"Body {i}",
            html_url=f"https://github.com/test/issues/{1000+i}",
            state="open",
            labels='["test"]',
            assignees="[]",
            comments_count=0,
            created_at=base_time,
            updated_at=base_time,
            author_login="testuser",
        )
        db_session.add(issue)
    await db_session.commit()
    
    # Test page 1
    result = await get_issues(db_session, page=1, page_size=10)
    assert result["total"] == 25
    assert result["page"] == 1
    assert result["page_size"] == 10
    assert result["total_pages"] == 3
    assert len(result["items"]) == 10
    
    # Test page 2
    result = await get_issues(db_session, page=2, page_size=10)
    assert result["page"] == 2
    assert len(result["items"]) == 10
    
    # Test page 3
    result = await get_issues(db_session, page=3, page_size=10)
    assert result["page"] == 3
    assert len(result["items"]) == 5


@pytest.mark.asyncio
async def test_get_issues_filtering(db_session: AsyncSession):
    """Test get_issues filters by state, search, and label."""
    base_time = datetime(2024, 1, 1, 0, 0, 0)
    # Create test issues with different states and labels
    issue1 = Issue(
        id=2001,
        title="Open issue with rust label",
        body="Rust content",
        html_url="https://github.com/test/issues/2001",
        state="open",
        labels='["rust", "tracking"]',
        assignees="[]",
        comments_count=0,
        created_at=base_time,
        updated_at=base_time,
        author_login="user1",
    )
    issue2 = Issue(
        id=2002,
        title="Closed issue",
        body="Done",
        html_url="https://github.com/test/issues/2002",
        state="closed",
        labels='["rust"]',
        assignees="[]",
        comments_count=0,
        created_at=base_time,
        updated_at=base_time,
        author_login="user2",
    )
    issue3 = Issue(
        id=2003,
        title="Open issue without rust",
        body="Other content",
        html_url="https://github.com/test/issues/2003",
        state="open",
        labels='["other"]',
        assignees="[]",
        comments_count=0,
        created_at=base_time,
        updated_at=base_time,
        author_login="user3",
    )
    db_session.add_all([issue1, issue2, issue3])
    await db_session.commit()
    
    # Filter by state
    result = await get_issues(db_session, state="open")
    assert result["total"] == 2
    
    # Filter by search
    result = await get_issues(db_session, search="rust")
    assert result["total"] == 2  # Both issue1 and issue2 have "rust" in labels
    
    # Filter by label
    result = await get_issues(db_session, label="tracking")
    assert result["total"] == 1
    assert result["items"][0]["id"] == 2001


@pytest.mark.asyncio
async def test_get_issue_detail(db_session: AsyncSession):
    """Test get_issue returns full details including comments."""
    base_time = datetime(2024, 1, 1, 0, 0, 0)
    issue = Issue(
        id=3001,
        title="Test Issue",
        body="Test body",
        html_url="https://github.com/test/issues/3001",
        state="open",
        labels='["test"]',
        assignees="[]",
        comments_count=2,
        created_at=base_time,
        updated_at=base_time,
        author_login="testuser",
        raw_data='{"issue": {"number": 3001}, "comments": [{"user": {"login": "c1"}, "body": "Comment 1"}, {"user": {"login": "c2"}, "body": "Comment 2"}]}',
    )
    db_session.add(issue)
    await db_session.commit()
    
    result = await get_issue(db_session, 3001)
    assert result is not None
    assert result["id"] == 3001
    assert result["title"] == "Test Issue"
    assert "comments" in result
    assert len(result["comments"]) == 2


@pytest.mark.asyncio
async def test_create_and_get_analysis(db_session: AsyncSession):
    """Test creating and retrieving AI analyses."""
    # Create issue first
    base_time = datetime(2024, 1, 1, 0, 0, 0)
    issue = Issue(
        id=4001,
        title="Test Issue",
        body="Test body",
        html_url="https://github.com/test/issues/4001",
        state="open",
        labels='["test"]',
        assignees="[]",
        comments_count=0,
        created_at=base_time,
        updated_at=base_time,
        author_login="testuser",
    )
    db_session.add(issue)
    await db_session.commit()
    
    # Create analysis
    analysis = await create_analysis(
        db=db_session,
        issue_id=4001,
        summary="Test summary",
        key_points=["Point 1", "Point 2"],
        blockers=["Blocker 1"],
        unresolved_questions=["Question 1"],
        provider="openai-compatible",
        model="gpt-4o-mini",
    )
    
    assert analysis.id is not None
    assert analysis.issue_id == 4001
    assert analysis.summary == "Test summary"
    assert analysis.provider == "openai-compatible"
    
    # Retrieve analyses
    analyses = await get_analyses(db_session, 4001)
    assert len(analyses) == 1
    assert analyses[0]["summary"] == "Test summary"
    assert analyses[0]["key_points"] == ["Point 1", "Point 2"]
    assert analyses[0]["blockers"] == ["Blocker 1"]
    assert analyses[0]["unresolved_questions"] == ["Question 1"]


@pytest.mark.asyncio
async def test_llm_client_unavailable():
    """Test LLMClient.is_available returns False without API key."""
    with patch("app.services.ai_analysis.settings") as mock_settings:
        mock_settings.llm_api_key = None
        mock_settings.llm_provider = "openai-compatible"
        mock_settings.llm_model = "gpt-4o-mini"
        mock_settings.llm_base_url = None
        
        client = LLMClient()
        assert client.is_available() is False


@pytest.mark.asyncio
async def test_llm_client_available():
    """Test LLMClient.is_available returns True with API key."""
    with patch("app.services.ai_analysis.settings") as mock_settings:
        mock_settings.llm_api_key = "test-key"
        mock_settings.llm_provider = "openai-compatible"
        mock_settings.llm_model = "gpt-4o-mini"
        mock_settings.llm_base_url = None
        
        client = LLMClient()
        assert client.is_available() is True


@pytest.mark.asyncio
async def test_llm_client_provider_error_on_missing_key():
    """Test LLMClient raises LLMProviderError when no API key."""
    with patch("app.services.ai_analysis.settings") as mock_settings:
        mock_settings.llm_api_key = None
        mock_settings.llm_provider = "openai-compatible"
        mock_settings.llm_model = "gpt-4o-mini"
        mock_settings.llm_base_url = None
        
        client = LLMClient()
        with pytest.raises(LLMProviderError, match="LLM_API_KEY not configured"):
            await client.analyze_issue("title", "body", [])


@pytest.fixture
async def db_session():
    """Create a fresh database session for each test using in-memory SQLite."""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.core.database import Base
    from sqlalchemy.ext.asyncio import AsyncSession
    
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )
    test_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session = test_session_maker()
    try:
        yield session
    finally:
        await session.close()
        await test_engine.dispose()