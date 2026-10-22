import { useState } from "react";
import { IssueList } from "./components/IssueList";
import { IssueDetail } from "./components/IssueDetail";
import { Issue } from "./api/client";

function App() {
  const [selectedIssue, setSelectedIssue] = useState<Issue | null>(null);

  return (
    <div className="app">
      <header>
        <h1>lumen-forge-ryan-vo</h1>
        <span>AI/ML Developer Tools — Rust Issue Tracker</span>
      </header>
      <main className="main-layout">
        <aside className="sidebar">
          <IssueList onIssueSelect={setSelectedIssue} />
        </aside>
        <section className="content">
          <IssueDetail issue={selectedIssue} />
        </section>
      </main>
      <footer>
        lumen-forge-ryan-vo &copy; 2025 Ryan Vo{" "}
        <span>{"ryandtvo@gmail.com"}</span>
      </footer>
    </div>
  );
}

export default App;