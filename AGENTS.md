# Agent Operating Guidelines & Autonomous Development Protocol (AGENTS.md)

This document defines the mandatory project management rules, Git/GitHub workflow, multi-agent orchestration architecture, Test-Driven Development (TDD) lifecycle, code-review standards, and operational invariants that all AI coding agents operating in this repository MUST follow.

The goal is to establish a **fully autonomous, issue-driven, worktree-isolated, TDD-first development workflow** where every unit of work is tracked on GitHub and implemented, tested, reviewed, and merged through a controlled multi-agent lifecycle.

---

# 1. Core Principles

All agents MUST adhere to these fundamental invariants:

1. **GitHub is the single source of truth for project work.**
2. Every feature, bug, enhancement, refactor, chore, UI change, documentation change, or other meaningful piece of work MUST have an associated GitHub Issue.
3. Never begin implementation work without an associated GitHub Issue.
4. Every issue MUST have a clearly defined scope, explicit acceptance criteria, and implementation expectations.
5. Each issue MUST be implemented in its own dedicated Git worktree.
6. Never allow multiple agents to modify the same Git worktree simultaneously.
7. Agents MUST strictly follow a Test-Driven Development (TDD) workflow.
8. Tests MUST fail for the expected reason before any production implementation begins.
9. Production code implementation happens ONLY after the failing test has been created, executed, and verified.
10. Every implementation MUST pass automated test suites and undergo an independent multi-lens code-review phase.
11. Every completed issue MUST result in a Pull Request (PR) unless explicitly designated as non-code work.
12. PRs MUST NOT be merged until the code reviewer agent approves them and all required CI status checks pass.
13. UI changes MUST be implemented as part of the same feature issue whenever the feature requires UI changes. Do not unnecessarily fragment frontend/UI work into separate issues.
14. **All Python project, dependency, environment, and test execution MUST use `uv`.**
15. Agents MUST operate with full autonomy whenever the required Git, GitHub CLI, `uv`, and runtime toolchains are available.

---

# 2. Toolchain Verification & GitHub CLI

The system MUST utilize the GitHub CLI (`gh`), Git, and Astral's `uv` for all repository operations.

### Verification Protocol
Before initiating any workflow, verify that the required toolchains are installed and authenticated:

```bash
gh --version
gh auth status
git --version
uv --version
```

### Authentication Failure Protocol
- If the GitHub CLI is not installed, provide the user with a clickable installation/documentation link.
- If GitHub authentication is missing or expired (`gh auth status` returns an error):
  1. The agent MUST NOT attempt to bypass authentication.
  2. The agent MUST output a clickable authentication URL or terminal instruction:
     ```bash
     gh auth login
     ```
  3. Clearly explain what user action is required.
  4. After the user completes authentication, verify again:
     ```bash
     gh auth status
     ```

### Authorized GitHub CLI Operations
Agents MUST use `gh` commands rather than scraping web pages or constructing manual URL modifications:
* Creating and viewing issues (`gh issue create`, `gh issue view`, `gh issue list`)
* Updating issues, labels, and assignees (`gh issue edit`, `gh issue develop`)
* Creating, viewing, and diffing pull requests (`gh pr create`, `gh pr view`, `gh pr diff`)
* Reviewing pull requests and adding comments (`gh pr review`, `gh pr comment`)
* Checking CI status checks (`gh pr checks`, `gh run list`, `gh run view`)
* Merging pull requests (`gh pr merge`)
* Inspecting repository metadata (`gh repo view`)

---

# 3. Python Project & Environment Management with `uv`

All Python dependencies, environments, script executions, and testing MUST be managed exclusively with **Astral `uv`**.

### 1. Tool Installation & PATH Verification
If `uv` is not found on `PATH`:
```bash
# Check default install path
export PATH="$HOME/.local/bin:$PATH" && uv --version

# If not installed, install via Astral official script
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Environment Synchronization (`uv sync`)
- Whenever entering the repository root or provisioning a new Git worktree, synchronize the virtual environment:
  ```bash
  uv sync
  ```
- To include development and test dependencies:
  ```bash
  uv sync --all-extras
  ```

### 3. Adding or Updating Dependencies
- **Strict Prohibition:** Never run bare `pip install` directly.
- **Adding runtime dependencies:**
  ```bash
  uv add <package-name>
  ```
- **Adding development / testing dependencies:**
  ```bash
  uv add --dev pytest pytest-asyncio ruff mypy
  ```
- Both `pyproject.toml` and `uv.lock` MUST be committed to Git whenever dependencies change.

### 4. Running Commands, Servers & Tests via `uv run`
All commands that invoke Python or installed CLI binaries MUST be executed via `uv run`:
* **Running the backend server:**
  ```bash
  uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
  ```
* **Running test suites:**
  ```bash
  uv run pytest backend/tests/
  uv run pytest backend/tests/unit/test_retriever.py -v
  ```
* **Running linting and formatting:**
  ```bash
  uv run ruff check .
  uv run ruff format --check .
  ```
* **Running type checking:**
  ```bash
  uv run mypy backend/app
  ```
* **Running evaluation benchmark scripts:**
  ```bash
  uv run python evaluation/run_eval.py
  ```

---

# 4. Project Management Workflow

Every task follows a strict end-to-end lifecycle:

```text
Incoming Request / Goal
         ↓
Analyze Requirements & Architecture
         ↓
Create / Identify GitHub Issue (`gh issue create` / `gh issue view`)
         ↓
Define Clear Acceptance Criteria
         ↓
Create Dedicated Git Worktree (`git worktree add ../worktrees/issue-<id>`)
         ↓
Sync Environment in Worktree (`uv sync`)
         ↓
Spawn Test Writer Agent
         ↓
Write Unit / Integration Tests
         ↓
Verify Tests Fail for the Correct Reason (`uv run pytest`) [Red Phase]
         ↓
Spawn Code Writer Agent
         ↓
Implement Minimal Code Until Tests Pass (`uv run pytest`) [Green Phase]
         ↓
Run Complete Test Suite & Static Analysis (`uv run ruff` / `uv run mypy`) [Refactor Phase]
         ↓
Create Focused Commit
         ↓
Push Branch (`git push -u origin <branch>`)
         ↓
Create Pull Request (`gh pr create`)
         ↓
Spawn Code Reviewer Agent (Multi-Lens Review)
         ↓
Resolve Any Review Findings / Fixes
         ↓
Verify All CI & Status Checks Pass (`gh pr checks`)
         ↓
Approve Pull Request (`gh pr review --approve`)
         ↓
Merge Pull Request (`gh pr merge`)
         ↓
Clean Up Git Worktree (`git worktree remove` + `git worktree prune`)
         ↓
Close / Update GitHub Issue (`gh issue close`)
```

Agents MUST NOT skip any lifecycle stage unless a task explicitly does not require that stage (e.g., pure documentation changes skipping unit tests).

---

# 5. Issue Management

Before starting any implementation work, determine whether an applicable GitHub Issue already exists.

### Existing Issues:
- Query existing issues via `gh issue list`.
- If an existing issue matches the scope, adopt it. Do NOT create duplicate issues.
- Verify that the acceptance criteria are comprehensive. If needed, update the issue via `gh issue edit`.

### New Issue Creation:
If no suitable issue exists, create one via the GitHub CLI:

```bash
gh issue create \
  --title "feat: <feature description>" \
  --body "<comprehensive requirements and acceptance criteria>" \
  --label "feature"
```

### Standard Issue Template Structure
Every issue MUST contain:
1. **Problem Statement:** What problem does this solve?
2. **Goal & Scope:** What is included in this unit of work?
3. **Out-of-Scope:** Explicit boundaries of what is excluded.
4. **Acceptance Criteria:** Checkable bullet points defining completion.
5. **Technical & Architectural Considerations:** Specific schemas, services, or APIs affected.
6. **Testing Requirements:** Specific tests and edge cases to implement.
7. **UI / UX Requirements:** Components, states (loading/error/empty), and interactions (if applicable).
8. **Definition of Done:** Final verification steps.

### Standard Issue Labels
* `feature` — New capabilities or end-to-end features
* `bug` — Bug fixes and defect remediation
* `enhancement` — Improvements to existing functionality
* `refactor` — Architectural or code cleanups without external behavior changes
* `chore` — Tooling, dependency updates, and maintenance
* `documentation` — PRD, AGENTS.md, README, or API docs
* `ui` — Frontend and visual interface work
* `testing` — Test framework and benchmark additions
* `security` — Security fixes and guardrail hardening
* `performance` — Latency, memory, and optimization improvements

---

# 6. Issue Decomposition

Large tasks and epic requests MUST be decomposed into smaller, independently deliverable GitHub issues before implementation begins.

```text
Epic / Parent Issue (e.g. #100: Grounded RAG Chat Engine)
├── Issue #101 — Backend ChromaDB Vector Retriever Service
├── Issue #102 — LangChain LCEL Grounded Prompt & Refusal Chain
├── Issue #103 — Frontend Conversational Chat UI & Citation Popover
└── Issue #104 — Groundedness Evaluation Benchmark Suite
```

### Decomposition Rules:
1. **True Independence:** Only split tasks when sub-issues can be developed and verified independently.
2. **Atomic UI Integration:** If a backend feature directly pairs with a user-facing component, keep the UI work attached to the same feature issue rather than arbitrarily splitting it into an orphaned UI ticket.
3. **Explicit Dependency Mapping:** Clearly declare dependencies in child issues (e.g., *"Blocked by #101"*).

---

# 7. Git Worktree Isolation

Every code implementation issue MUST be executed in its own isolated Git worktree.

**Never develop unrelated issues directly on the main working tree.**

### Directory Structure & Convention
```text
~/Projects/internship-intelligence-assistant/ # Main Repository Root
~/Projects/worktrees/                         # Isolated Worktrees Directory
├── issue-101/                               # Worktree for Issue #101
├── issue-102/                               # Worktree for Issue #102
└── issue-103/                               # Worktree for Issue #103
```

### Worktree Provisioning Commands
```bash
# Verify branch does not exist and working directory is clean
git status

# Create dedicated worktree and new branch
git worktree add ../worktrees/issue-101 -b feat/issue-101

# Synchronize virtual environment in the worktree directory
cd ../worktrees/issue-101 && uv sync
```

### Worktree Isolation Invariants:
1. **Strict 1:1 Mapping:** Exactly one worktree per active issue.
2. **Workspace Containment:** An agent assigned to Issue #101 MUST only read and modify files inside `../worktrees/issue-101`.
3. **No Concurrent Collisions:** Never allow multiple agents to modify the same worktree directory simultaneously.
4. **Clean Teardown:** Once the PR is merged, remove the worktree immediately:
   ```bash
   git worktree remove ../worktrees/issue-101
   git worktree prune
   ```

---

# 8. Multi-Agent Orchestration

When multiple independent issues exist, orchestrate parallel or sequential subagent pipelines.

```text
Issue #101 Pipeline                         Issue #102 Pipeline
────────────────────                         ────────────────────
Worktree: ../worktrees/issue-101            Worktree: ../worktrees/issue-102
     │                                           │
     ▼                                           ▼
Test Writer Agent #101                      Test Writer Agent #102
(Writes failing tests for #101)             (Writes failing tests for #102)
     │                                           │
     ▼                                           ▼
Code Writer Agent #101                      Code Writer Agent #102
(Implements code until green)               (Implements code until green)
     │                                           │
     ▼                                           ▼
Reviewer Agent #101                         Reviewer Agent #102
(Multi-lens review & approval)              (Multi-lens review & approval)
     │                                           │
     ▼                                           ▼
Merge #101 & Teardown                       Merge #102 & Teardown
```

### Orchestration Invariants:
- Independent issues execute concurrently in their respective worktrees.
- If Issue #102 depends on Issue #101, Workflow #102 MUST pause until Issue #101 is merged to `main` and rebased into `issue-102`.

---

# 9. Test-Driven Development (TDD) Workflow

All code modifications MUST follow the classic Red-Green-Refactor TDD cycle.

```
       ┌────────────────────────┐
       │   1. Read Issue & Spec │
       └───────────┬────────────┘
                   │
                   ▼
       ┌────────────────────────┐
       │ 2. Write Failing Test  │ ◄─── (Test Writer Agent)
       └───────────┬────────────┘
                   │
                   ▼
       ┌────────────────────────┐
       │ 3. Verify Failure (RED)│ (Must fail on missing behavior)
       └───────────┬────────────┘
                   │
                   ▼
       ┌────────────────────────┐
       │ 4. Implement Code      │ ◄─── (Code Writer Agent)
       └───────────┬────────────┘
                   │
                   ▼
       ┌────────────────────────┐
       │ 5. Pass Tests (GREEN)  │
       └───────────┬────────────┘
                   │
                   ▼
       ┌────────────────────────┐
       │ 6. Refactor & Lint     │
       └────────────────────────┘
```

## Phase 1 — Understand
The Test Writer Agent MUST:
1. Thoroughly read the GitHub Issue and acceptance criteria.
2. Inspect existing architectural patterns, fixtures, and conventions.
3. Identify the proper test file location (e.g., `backend/tests/unit/` or `backend/tests/integration/`).
4. Keep production code unmodified during this phase.

## Phase 2 — Write Failing Tests
The Test Writer Agent MUST:
1. Write deterministic, behavior-oriented unit and integration tests.
2. Cover all explicit acceptance criteria and edge cases (e.g., empty files, malformed JSON, quota errors).
3. Execute the test runner via `uv`:
   ```bash
   uv run pytest backend/tests/test_specific_feature.py
   ```
4. **Validate Expected Failure:** The test MUST fail specifically because the production feature is not yet implemented.
   - *Invalid Failure:* A failure caused by a syntax error, bad import, missing package, or broken fixture does NOT satisfy TDD.
5. Provide the handoff report: `FAILURE VERIFIED: YES`.

---

# 10. Code Writer Agent

The Code Writer Agent is spawned ONLY after failing tests have been verified.

### Responsibilities:
1. Read the issue requirements and inspect the failing tests.
2. Implement the cleanest, minimal production code that satisfies the tests.
3. Avoid speculative over-engineering or out-of-scope refactoring.
4. Run the test suite continuously via `uv` until all tests pass:
   ```bash
   uv run pytest backend/tests/
   ```
5. Run formatting, linting, and type checks:
   ```bash
   uv run ruff check .
   uv run mypy backend/app
   ```
6. Confirm the completion criteria:
   ```text
   New tests pass: YES
   Existing tests pass: YES
   Lint / Type checks pass: YES
   Build passes: YES
   ```

---

# 11. UI Requirements & Frontend Engineering

When an issue involves user interface functionality, the frontend implementation MUST be delivered within the same issue workflow.

### Frontend Quality Checklist:
* **Accessibility (a11y):** Semantic HTML elements, ARIA labels on icon buttons, keyboard navigable dialogs and drawers, high-contrast text.
* **State Management:** Explicit handling for `Loading` (skeleton/spinner), `Empty` (empty states), `Error` (actionable error banners), and `Success`.
* **Component Reuse:** Reuse existing UI components (`components/Navbar.tsx`, `components/SourceViewerModal.tsx`, etc.) rather than duplicating logic.
* **Responsive Design:** Functional and visually consistent across mobile, tablet, and desktop viewports.
* **Visual Verification:** Inspect and verify UI layout before committing and creating a PR.

---

# 12. Commit Rules & Conventional Commits

Commits must be focused, atomic, and directly tied to the issue being resolved.

### Format Convention
```text
<type>(#<issue-id>): <short imperative description>

[optional longer body explaining context and rationale]
```

### Standard Commit Types
* `feat(#101): add multi-page PDF citation extraction`
* `fix(#102): handle zero-division in skill matching formula`
* `test(#103): add integration tests for document deletion`
* `refactor(#104): simplify LCEL retriever chain formatting`
* `docs(#105): update AGENTS.md with worktree protocols`
* `chore(#106): update uv.lock dependencies`

### Pre-Commit Safeguards
Before creating a commit, always inspect:
```bash
git status
git diff
git diff --cached
```
**Strict Prohibition:** Never commit `.env` files, API keys, temporary artifacts, or unrelated changes.

---

# 13. Pull Request Creation

Once implementation and tests are verified in the worktree, push the branch and open a PR via `gh`:

```bash
git push -u origin feat/issue-101

gh pr create \
  --title "feat(#101): Grounded RAG Chat Engine with Citations" \
  --body "## Summary
- Implemented ChromaDB vector retrieval with LangChain LCEL
- Added strict XML-delimited prompt grounding and refusal rules
- Integrated slide-out citation preview drawer

## Related Issue
Closes #101

## Verification
- Unit & integration tests passing (\`uv run pytest\`)
- Manual UI verification of citation drawer performed" \
  --base main
```

Every PR MUST include the `Closes #<id>` keyword to enable automatic GitHub issue closure upon merge.

---

# 14. Code Review Agent (Multi-Lens Review)

Every Pull Request MUST undergo an independent, multi-perspective code review. The Reviewer Agent MUST NOT rubber-stamp approvals.

```text
                                  ┌────────────────────────┐
                                  │   Pull Request (PR)    │
                                  └───────────┬────────────┘
                                              │
         ┌────────────────────────────────────┼────────────────────────────────────┐
         ▼                                    ▼                                    ▼
┌──────────────────┐                 ┌──────────────────┐                 ┌──────────────────┐
│ 1. Correctness   │                 │ 2. Test Quality  │                 │ 3. Architecture  │
│ • Satisfies spec │                 │ • True TDD       │                 │ • Clean layers   │
│ • Edge cases     │                 │ • Deterministic  │                 │ • Minimal coupling│
└──────────────────┘                 └──────────────────┘                 └──────────────────┘
         │                                    │                                    │
         ├────────────────────────────────────┼────────────────────────────────────┤
         ▼                                    ▼                                    ▼
┌──────────────────┐                 ┌──────────────────┐                 ┌──────────────────┐
│ 4. Security      │                 │ 5. Performance   │                 │ 6. Maintainability│
│ • Zero secrets   │                 │ • Vector query ms│                 │ • Clear naming   │
│ • Prompt defense │                 │ • Memory leaks   │                 │ • Typed schemas  │
└──────────────────┘                 └──────────────────┘                 └──────────────────┘
                                              │
                                              ▼
                                     ┌──────────────────┐
                                     │ 7. UI / UX & A11y│
                                     │ • Empty / Loading│
                                     │ • Responsive     │
                                     └──────────────────┘
```

### Review Perspectives:
1. **Correctness:** Does the code fulfill all acceptance criteria without unintended side effects?
2. **Test Quality:** Did tests fail first? Are edge cases (null inputs, rate limits, malformed files) covered?
3. **Architecture:** Does the change respect FastAPI service layers and LangChain LCEL conventions?
4. **Security:** Are untrusted inputs sanitized? Is prompt injection defended against? Zero exposed secrets?
5. **Performance:** Efficient chunk querying? Zero unnecessary loops or database locking?
6. **Maintainability:** Clear naming, type hints, structured logging, no duplicate code?
7. **UI / UX:** Accessible labels, clean responsive layout, and proper error states?

---

# 15. Review Outcome Classification

The reviewer classifies all findings into four strict tiers:

| Severity | Definition | Action Required |
|---|---|---|
| **`BLOCKER`** | Critical security risk, data corruption, broken core functionality, or failing tests. | **Must fix before merge.** |
| **`MAJOR`** | Unmet acceptance criterion, missing critical test case, or serious design flaw. | **Must fix before merge.** |
| **`MINOR`** | Sub-optimal error message, minor code duplication, or non-critical edge case. | Fix or document justification. |
| **`NIT`** | Minor stylistic preference or non-essential comment tweak. | Optional; does not block PR. |

---

# 16. Review / Fix Loop

If any `BLOCKER` or `MAJOR` findings are raised:
1. The Reviewer Agent posts clear comments with file and line references via `gh pr comment` or `gh pr review`.
2. The Code Writer Agent implements fixes directly in the worktree.
3. Tests are re-executed (`uv run pytest`).
4. Fixes are committed and pushed (`git push`).
5. The Reviewer Agent performs a re-review until all blocking items are resolved.

---

# 17. CI and Required Status Checks

Before merging, verify all automated checks using GitHub CLI:

```bash
gh pr checks <PR_NUMBER>
```

### Status Checklist:
- Unit & integration tests passing (`uv run pytest`)
- Linter & static analysis passing (`uv run ruff check .`, `uv run mypy backend/app`)
- Build checks passing (`npm run build`, backend startup check)
- GitHub Actions CI status: `SUCCESS`

**Invariable Rule:** Never merge a Pull Request while required status checks or tests are failing.

---

# 18. Merge Rules

A Pull Request may only be merged when:
```text
[✓] All issue acceptance criteria satisfied
[✓] Failing test was created and verified prior to implementation
[✓] All unit & integration tests pass via uv run pytest
[✓] Linter, type checks, and builds pass
[✓] Code Reviewer Agent has approved the PR
[✓] Zero unresolved BLOCKER or MAJOR comments
[✓] All CI checks on GitHub are green
```

### Merge Execution:
```bash
gh pr merge <PR_NUMBER> --squash --delete-branch
```

---

# 19. Post-Merge Cleanup

Immediately following a successful merge:
1. Verify the PR is merged: `gh pr view <PR_NUMBER>`.
2. Confirm the associated GitHub Issue is closed: `gh issue view <ISSUE_ID>`.
3. Switch to the main branch in the main repo: `git checkout main && git pull origin main`.
4. Remove the issue worktree:
   ```bash
   git worktree remove ../worktrees/issue-101
   git worktree prune
   ```
5. Report completion to the team/orchestrator.

---

# 20. Failure Handling & Escalation Protocols

Agents MUST halt and report clear diagnostics when encountering:
* Missing GitHub CLI authentication (`gh auth login` required).
* Missing `uv` or runtime toolchain.
* Destructive operations that could cause unrecoverable data loss.
* Ambiguous requirements that cannot be resolved via PRD or codebase inspection.
* Missing external secrets/credentials (`GEMINI_API_KEY`).
* Merge conflicts requiring major product trade-offs.

### Blocked Report Format:
When escalating, the agent must output:
1. **What is blocked:** (e.g., GitHub CLI authentication required / `uv` missing)
2. **Why it is blocked:** (e.g., `gh auth status` returned 401 Unauthorized)
3. **Exact User Action:** (e.g., Run `gh auth login` in your local shell)
4. **Resumption Plan:** (e.g., Agent will verify auth and resume worktree creation)

---

# 21. Agent Handoff Contract

Every inter-agent communication MUST provide a complete contextual contract:

```text
Issue ID: #101
Worktree Path: ../worktrees/issue-101
Branch: feat/issue-101
Current Status: RED Phase Complete
Test Target: backend/tests/unit/test_retriever.py
Failing Command: uv run pytest backend/tests/unit/test_retriever.py
Verified Failure: AssertionError - ChromaRetriever not implemented
Acceptance Criteria: [List of criteria]
Next Assigned Agent: Code Writer Agent
```

---

# 22. Autonomous Execution Rules

Agents MUST maximize autonomy. Do not pause execution to ask for user confirmation for routine, authorized tasks including:
- Creating issues and worktrees.
- Syncing environments (`uv sync`).
- Writing tests and implementing code.
- Running tests, formatters, and linters (`uv run pytest`, `uv run ruff`, `uv run mypy`).
- Committing, pushing branches, and creating PRs.
- Performing code reviews and fixing review findings.
- Merging approved PRs and cleaning up worktrees.

**Ask the user ONLY when:**
- Credentials/API keys are missing.
- Severe requirement ambiguity cannot be resolved.
- Destructive non-reversible actions are required.

---

# 23. Definition of Done (Checklist)

An issue is considered **DONE** if and only if:
```text
[ ] GitHub Issue created with detailed acceptance criteria
[ ] Dedicated worktree provisioned (`../worktrees/issue-<id>`)
[ ] Worktree environment synchronized with `uv sync`
[ ] Failing tests written by Test Writer Agent
[ ] Tests verified failing for the expected missing behavior
[ ] Minimal code implemented by Code Writer Agent
[ ] All unit and integration tests passing (`uv run pytest`)
[ ] Static analysis, linting, and type checks passing (`uv run ruff`, `uv run mypy`)
[ ] Frontend UI verified (including loading, empty, and error states)
[ ] Changes committed with conventional commit format referencing issue
[ ] Branch pushed and PR created referencing `Closes #<id>`
[ ] Multi-lens code review conducted by Reviewer Agent
[ ] All BLOCKER and MAJOR findings resolved
[ ] GitHub Actions / CI checks verified green
[ ] PR approved and merged
[ ] GitHub Issue verified closed
[ ] Git worktree removed and pruned
```

---

# 24. Fundamental Operational Invariant

> **Never optimize for speed by skipping the workflow.**

The process:
$$\text{Issue} \longrightarrow \text{Worktree} \longrightarrow \text{uv sync} \longrightarrow \text{Failing Test} \longrightarrow \text{Implementation} \longrightarrow \text{Passing Tests} \longrightarrow \text{PR} \longrightarrow \text{Review} \longrightarrow \text{CI} \longrightarrow \text{Merge} \longrightarrow \text{Cleanup}$$

This sequence is the mandatory, non-negotiable operational protocol for all autonomous agents in this repository.
