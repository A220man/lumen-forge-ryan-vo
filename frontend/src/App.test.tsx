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
    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("displays health data on successful fetch", async () => {
    const mockHealth = {
      status: "ok",
      service: "lumen-forge-ryan-vo",
      version: "1.0.0",
    };
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockHealth),
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("Status")).toBeInTheDocument();
      expect(screen.getByText("ok")).toBeInTheDocument();
      // Use getByLabelText or more specific query for service
      expect(screen.getByText("Version")).toBeInTheDocument();
      expect(screen.getByText("1.0.0")).toBeInTheDocument();
    });
  });

  it("displays error on failed fetch", async () => {
    mockFetch.mockRejectedValue(new Error("Network error"));

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/Error:/)).toBeInTheDocument();
      // Error message is split across text nodes, use regex
      expect(screen.getByText(/Network error/)).toBeInTheDocument();
    });
  });

  it("displays error on non-ok HTTP response", async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 500,
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/Error:/)).toBeInTheDocument();
      expect(screen.getByText(/HTTP 500/)).toBeInTheDocument();
    });
  });
});