import { useEffect, useState } from 'react';
import { api, Issue, IssueListResponse } from '../api/client';

interface IssueListProps {
  onIssueSelect: (issue: Issue) => void;
}

export function IssueList({ onIssueSelect }: IssueListProps) {
  const [issues, setIssues] = useState<Issue[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [totalPages, setTotalPages] = useState(0);
  const [stateFilter, setStateFilter] = useState<'open' | 'closed' | ''>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [labelFilter, setLabelFilter] = useState('');

  const fetchIssues = async () => {
    setLoading(true);
    setError(null);
    try {
      const data: IssueListResponse = await api.issues.list({
        page,
        page_size: pageSize,
        state: stateFilter || undefined,
        search: searchQuery || undefined,
        label: labelFilter || undefined,
      });
      setIssues(data.items);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch issues');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIssues();
  }, [page, pageSize, stateFilter, searchQuery, labelFilter]);

  const handleSync = async () => {
    setLoading(true);
    setError(null);
    try {
      await api.issues.sync();
      await fetchIssues();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sync failed');
    } finally {
      setLoading(false);
    }
  };

  if (loading && issues.length === 0) {
    return <div className="loading">Loading issues...</div>;
  }

  return (
    <div className="issue-list">
      <div className="issue-list-header">
        <h2>Rust Tracking Issues</h2>
        <div className="issue-filters">
          <select
            value={stateFilter}
            onChange={(e) => setStateFilter(e.target.value as 'open' | 'closed' | '')}
            className="filter-select"
          >
            <option value="">All States</option>
            <option value="open">Open</option>
            <option value="closed">Closed</option>
          </select>
          <input
            type="text"
            placeholder="Search title/body..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="filter-input"
          />
          <input
            type="text"
            placeholder="Filter by label..."
            value={labelFilter}
            onChange={(e) => setLabelFilter(e.target.value)}
            className="filter-input"
          />
          <button onClick={handleSync} disabled={loading} className="sync-button">
            Sync from GitHub
          </button>
        </div>
      </div>

      {error && <div className="error-message">Error: {error}</div>}

      {issues.length === 0 && !loading && (
        <div className="empty-state">No issues found</div>
      )}

      <div className="issues-table-container">
        <table className="issues-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Title</th>
              <th>State</th>
              <th>Labels</th>
              <th>Comments</th>
              <th>Updated</th>
            </tr>
          </thead>
          <tbody>
            {issues.map((issue) => (
              <tr key={issue.id} onClick={() => onIssueSelect(issue)}>
                <td className="issue-number">#{issue.id}</td>
                <td className="issue-title">
                  <a href={issue.html_url} target="_blank" rel="noopener noreferrer" onClick={(e) => e.stopPropagation()}>
                    {issue.title}
                  </a>
                </td>
                <td>
                  <span className={`status-badge ${issue.state}`}>{issue.state}</span>
                </td>
                <td className="issue-labels">
                  {issue.labels.slice(0, 3).map((label) => (
                    <span key={label} className="label-badge">{label}</span>
                  ))}
                  {issue.labels.length > 3 && (
                    <span className="label-badge more">+{issue.labels.length - 3}</span>
                  )}
                </td>
                <td className="issue-comments">{issue.comments_count}</td>
                <td className="issue-updated">
                  {new Date(issue.updated_at).toLocaleDateString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="pagination">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
          >
            Previous
          </button>
          <span className="page-info">
            Page {page} of {totalPages} ({total} total)
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}