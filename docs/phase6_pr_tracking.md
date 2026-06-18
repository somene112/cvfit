# Phase 6 PR Tracking — Logical Sequence vs Actual GitHub PRs

> **Date:** 2026-06-19
> **Purpose:** The logical PR sequence in [phase6_kickoff_plan.md](phase6_kickoff_plan.md) does
> not always match GitHub PR numbers. This file is the source of truth for what actually landed.

## Why numbers drift

PR #67 (Target Jobs backend) was opened **stacked** on the docs branch. Merging the docs PR with
`--delete-branch` removed that base branch, which **auto-closed #67**. The same commit was
re-opened against `main` and merged as **#68**. So "logical PR 67" physically merged as GitHub #68,
and the Learning Roadmap bundle (logical PR 68) shifts forward.

## Mapping

| Logical PR (plan) | Module | Actual GitHub PR | Status |
|-------------------|--------|------------------|--------|
| PR 66 | Phase 6 kickoff docs | **#66** | Merged |
| PR 67 | Target Jobs backend | **#68** (auto-closed #67 superseded) | Merged |
| PR 68 | Learning Roadmap + Interview v2 backend | **#69** | Merged |
| PR 69 | Help Assistant + Share Links backend | this PR | Open |
| PR 70+ | Usage shell, analytics/E2E closeout | TBD | Pending |

> **Note:** Backend bundles combine multiple logical modules per PR. Week 2 = Learning + Interview v2
> (#69). Week 3 = Help Assistant + Share Links (this PR). Usage shell and closeout remain out of scope
> here. Share Links ship behind `ENABLE_PHASE6_SHARE_LINKS=false` until privacy review passes.
