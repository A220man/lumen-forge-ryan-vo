import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import App from "./App";

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe("App", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("renders loading state initially", () => {
    const { promise: neverResolves } = Promise.withResolvers<never>();
    mockFetch.mockImplementation(() => neverResolves);

    render(<App />);
    expect(screen.getByText("Loading issues...")).toBeInTheDocument();
  });

  it("displays issue list on successful fetch", async () => {
    const mockIssues = {
      items: [
        {
          id: 31844,
          title: "Tracking issue for specialization",
          body: "This is a tracking issue...",
          html_url: "https://github.com/rust-lang/rust/issues/31844",
          state: "open",
          labels: ["tracking-issue", "F-specialization"],
          assignees: [],
          comments_count: 323,
          created_at: "2016-03-15T12:00:00Z",
          updated_at: "2024-01-15T12:00:00Z",
          closed_at: null,
          author_login: "aturon",
          author_html_url: "https://github.com/aturon",
          repository: "rust-lang/rust",
        },
      ],
      total: 1,
      page: 1,
      page_size: 20,
      total_pages: 1,
    };
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockIssues),
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("Rust Tracking Issues")).toBeInTheDocument();
      expect(screen.getByText("#31844")).toBeInTheDocument();
      expect(screen.getByText("Tracking issue for specialization")).toBeInTheDocument();
    });
  });

  it("displays error on failed fetch", async () => {
    mockFetch.mockRejectedValue(new Error("Network error"));

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/Error:/)).toBeInTheDocument();
      expect(screen.getByText(/Network error/)).toBeInTheDocument();
    });
  });

  it("displays error on non-ok HTTP response", async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 500,
      json: () => Promise.resolve({ detail: "Internal Server Error" }),
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/Error:/)).toBeInTheDocument();
      expect(screen.getByText(/Internal Server Error/)).toBeInTheDocument();
    });
  });
});