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

## 2026-06-22 15:14 [saved]
Goal: Add core AGENTS guidance.
Decisions:
- Keep `src/core/uzoncalc/AGENTS.md` concise because detailed architecture already lives in `README.develop.md`.
- Document core/package/test boundaries because agents often mix root workspace and core package commands.
- Preserve Playwright/PDF verification rules because pagination correctness depends on real browser output.
Rejected:
- Do not duplicate the full core architecture walkthrough.
Open:
- Track `src/core/uzoncalc/AGENTS.md` when committing this change.

## 2026-06-23 13:26 [saved]
Goal: Update uzoncalc writer skill.
Decisions:
- Document alias `_` and `^` notation because `ScriptNotation` now handles both scripts.
- Prefer `ctx.save()` in the skill because no global `save()` helper exists.
- Mention ineffective equation toggles only as non-recommended APIs because current functions are no-ops.
Rejected:
- Do not revive `Subscripting` names.
Open:
- Commit `.agents/skills/uzoncalc-writer/SKILL.md` with this log entry.

## 2026-06-23 22:12 [saved]
Goal: Preserve skill/config session decisions.
Decisions:
- Keep writer-skill decisions in session log because hook reminders need durable rationale.
- Keep Nginx troubleshooting out of project memory because it was unrelated operational support.
Rejected:
- Do not replace existing writer-skill entry with a broader summary.
Open:
- Commit `.agents/skills/uzoncalc-writer/SKILL.md` with related changes.

## 2026-06-25 18:55 [saved]
Goal: Document writer-skill UI control boundary.
Decisions:
- Base UI guidance on Python `Field` because agents write calculation scripts, not Vue code.
- Explain `values` as current-window form state because visible/onChanged depend on it.
- Mark extra LowCodeForm props unsupported because Python Field does not expose them.
Rejected:
- Do not document frontend-only props as writer-skill APIs.
Open:
- Commit `.agents/skills/uzoncalc-writer/SKILL.md` with this log entry.
