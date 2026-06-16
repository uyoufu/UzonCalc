# Session Log

Project-level memory entries for durable decisions, rejected approaches, and constraints. Keep entries short; use `state.md` only for active in-progress handoff.

## 2026-06-16 17:34 [saved]
Goal: Initialize project memory files.
Decisions:
- Use `project-map.md` as the root orientation map because session hooks search only the project root.
- Keep `session-log.md` for durable decisions only because transient progress belongs in `state.md`.
- Mark the map `dirty` because existing uncommitted work changes current structure.
Rejected:
- No `state.md` for setup-only work.
Open:
- Refresh map after current dirty work is committed.
