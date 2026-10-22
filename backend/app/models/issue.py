from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from app.core.database import Base


class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, autoincrement=False)  # GitHub issue number
    title = Column(String(500), nullable=False)
    body = Column(Text, nullable=True)
    html_url = Column(String(500), nullable=False)
    state = Column(String(20), nullable=False)  # open, closed
    labels = Column(Text, nullable=True)  # JSON array of label names
    assignees = Column(Text, nullable=True)  # JSON array of assignee logins
    comments_count = Column(Integer, default=0)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    closed_at = Column(DateTime, nullable=True)
    author_login = Column(String(100), nullable=False)
    author_html_url = Column(String(500), nullable=True)
    repository = Column(String(100), nullable=False, default="rust-lang/rust")
    raw_data = Column(Text, nullable=True)  # Full GitHub API response for flexibility
    synced_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_issues_state", "state"),
        Index("ix_issues_created_at", "created_at"),
        Index("ix_issues_labels", "labels"),
    )

    def to_dict(self) -> dict:
        import json
        return {
            "id": self.id,
            "title": self.title,
            "body": self.body,
            "html_url": self.html_url,
            "state": self.state,
            "labels": json.loads(self.labels) if self.labels else [],
            "assignees": json.loads(self.assignees) if self.assignees else [],
            "comments_count": self.comments_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "author_login": self.author_login,
            "author_html_url": self.author_html_url,
            "repository": self.repository,
        }


class IssueAnalysis(Base):
    __tablename__ = "issue_analyses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    issue_id = Column(Integer, nullable=False, index=True)
    summary = Column(Text, nullable=False)
    key_points = Column(Text, nullable=True)  # JSON array
    blockers = Column(Text, nullable=True)  # JSON array
    unresolved_questions = Column(Text, nullable=True)  # JSON array
    provider = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    raw_response = Column(Text, nullable=True)
    def to_dict(self) -> dict:
        import json
        return {
            "id": self.id,
            "issue_id": self.issue_id,
            "summary": self.summary,
            "key_points": json.loads(self.key_points) if self.key_points else [],
            "blockers": json.loads(self.blockers) if self.blockers else [],
            "unresolved_questions": json.loads(self.unresolved_questions) if self.unresolved_questions else [],
            "provider": self.provider,
            "model": self.model,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "raw_response": self.raw_response,
        }