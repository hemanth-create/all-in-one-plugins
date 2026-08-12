---
name: duet-relay
description: Set up, operate, diagnose, or safely update a local Markdown relay and lifecycle dashboard shared by Codex and Claude. Use when a user asks to connect the agents, create or review issue threads, track planning and implementation work, show relay status in a local webpage, configure a Claude watcher, recover missed messages, or install relay.py in a repository.
license: MIT
---

# Duet Relay

Use the bundled `scripts/relay.py` as the source implementation. Keep the target repository's relay local, standard-library-only, and explicit about cursor and baton ownership.

Examples below use `python` (the Windows launcher `py` also works); on macOS or Linux run `python3`. Set the optional `DUET_HOME` environment variable to place `AI-Threads/` and `.duet/` outside the script's directory; by default they sit next to `relay.py`.

## Choose the workflow

- **Set up:** Install the relay and merge the bundled instruction snippets.
- **Operate:** Use the target repository's `relay.py`; do not run the bundled copy against the skill directory.
- **Track:** Keep one issue per lifecycle thread and use the generated dashboard for the user's overview.
- **Diagnose:** Inspect channel logs and cursor ownership without consuming another role's queue.
- **Update:** Stop watchers, compare the target script with the bundled version, and preserve runtime logs.

## Set up a repository

1. Read the target repository's applicable `AGENTS.md`, `CLAUDE.md`, and `.claude/settings.json` first.
2. Copy `scripts/relay.py` to the repository root. If `relay.py` already exists, review the difference and preserve intentional local behavior.
3. Merge the Codex and Claude instruction blocks under **Repository instruction templates** into the applicable `AGENTS.md` and `CLAUDE.md`. Append or integrate; never replace unrelated guidance or duplicate an existing relay block.
4. Create `AI-Threads/planning/`, `AI-Threads/working/`, `AI-Threads/completed/`, `.duet/`, and `.duet/outbox.md`. Treat them as runtime state.
5. Offer the ignore entries under **Local ignore template** for repositories that should not version messages or cursors.
6. Before changing Claude permissions, show the user the exact allowlist under **Claude permission template** and obtain approval. Merge only those entries.
7. Run `python -m py_compile relay.py`, `python relay.py --help`, and `python relay.py dashboard`. Open `AI-Threads/index.html` manually when the user wants the dashboard. Use `py` when that is the configured Windows launcher.

Do not start a watcher unless the user asks for ongoing monitoring. Do not run Git, deployment, cloud, or network commands as part of setup.

## Operate the relay

List the compact shared state before choosing a thread:

```powershell
python relay.py threads
```

Post from Codex and name the next actor explicitly:

```powershell
python relay.py post --thread backend-timeout --from codex --next claude --body "Plan ready for review."
```

The first post creates `AI-Threads/planning/backend-timeout.md`. Start every material body with a concise status line; the dashboard uses its first non-empty line as the summary.

Read Codex's queue:

```powershell
python relay.py unseen --for codex
```

For a substantive Claude reply, let Claude write the complete body to `.duet/outbox.md`, then run:

```powershell
python relay.py post --thread backend-timeout --from claude --next codex --outbox
```

The relay clears `.duet/outbox.md` after a successful `--outbox` post, so stale content cannot be re-sent; write a fresh body before each `--outbox` send.

Add `--next codex`, `--next claude`, `--next user`, or `--next none` to keep the baton accurate. Omitting it defaults to the other agent for compatibility.

Run at most one watcher for a role:

```powershell
python relay.py watch --for claude --interval 5
```

While a watcher is active, it exclusively owns that role's `.duet/seen.<role>` cursor and holds `.duet/watch.<role>.lock`; a second watcher for the same role exits immediately instead of silently splitting the queue. Read the relevant file under `AI-Threads/planning/`, `working/`, or `completed/` for history or recovery; never run a competing `unseen` reader.

## Move work through its lifecycle

1. Create and review the plan in `planning/`.
2. After user approval, post the approval/status with the correct `--next` value, then run:

   ```powershell
   python relay.py move --thread backend-timeout --to working
   ```

3. After implementation and validation, post a final outcome with `--next none`, then run:

   ```powershell
   python relay.py move --thread backend-timeout --to completed
   ```

Completion is rejected unless the latest message records `--next none`. Completed threads are read-only; start a follow-up thread instead of reopening one. Existing flat `AI-Threads/*.md` logs remain readable and move into the lifecycle on their next post or move.

The relay regenerates `AI-Threads/index.html` after each post or move. Repair a stale page with `python relay.py dashboard`. Do not use the dashboard as agent context: run `threads`, then read only the active Markdown thread needed for the task.

## Preserve safety

- Use stable lowercase issue slugs such as `bells-8926-log-retention`; the script rejects paths, traversal, and portable-name violations.
- Keep message bodies below 256 KiB and never relay secrets, credentials, PHI, or unnecessary personal data.
- Let only Claude write `.duet/outbox.md`, sequentially.
- Never edit or save live thread Markdown or generated `AI-Threads/index.html`; stale buffers can overwrite relay state.
- Stop watchers before replacing `relay.py` or removing runtime state.
- Treat delivery as best-effort. Channel files are the durable history; no acknowledgment protocol is provided.

## Diagnose failures

- If a watcher is silent but a message ID appears in its cursor, another reader consumed the queue. Recover from the channel Markdown and restore single-reader ownership.
- If Unicode output fails, confirm the target uses the bundled UTF-8 stdout configuration.
- If `--outbox` is rejected, confirm the target script and Claude instructions were updated together; do not restore arbitrary `--body-file` access.
- If a lock fails, stop duplicate watchers and retry after the current relay operation exits. Do not delete lock state while a relay process is active.
- If a post reports that history was saved but dashboard generation failed, do not repost. Run `python relay.py dashboard` to repair only the view.
- If a duplicate thread name is reported, resolve the duplicate lifecycle files while all watchers are stopped; do not let agents choose one silently.

## Repository instruction templates

Append or integrate this Codex block into the applicable `AGENTS.md`:

```markdown
## Claude-Codex Relay

`relay.py` provides local Markdown channels shared with Claude.

- List work first: `python relay.py threads`
- Post: `python relay.py post --thread <issue-slug> --from codex --next <user|codex|claude|none> --body "..."`
- Read Codex's queue: `python relay.py unseen --for codex`
- Start work: `python relay.py move --thread <issue-slug> --to working`
- Complete work: `python relay.py move --thread <issue-slug> --to completed`
- Repair the user dashboard: `python relay.py dashboard`

When the user asks Claude to review a plan, choose one stable lowercase issue slug; the first post creates its planning thread. Start each material message with a concise status line and set the next actor explicitly. After approval, post the new status before moving to `working`. After implementation and validation, post the final outcome with `--next none`, then move to `completed`; the relay rejects completion without that final baton.

Run at most one watcher per role. While a watcher is active, never run another `unseen` command for that role because both share `.duet/seen.<role>`. Claude alone writes `.duet/outbox.md`, sequentially, and sends long replies with `--outbox`. Use `threads`, then read only the relevant lifecycle Markdown for context. Do not edit thread files or generated `AI-Threads/index.html`. Keep secrets, credentials, PHI, and unnecessary personal data out of relay messages.
```

Append or integrate this Claude block into `CLAUDE.md`:

````markdown
## Shared Relay with Codex

Use the repository's `relay.py` to exchange local Markdown messages with Codex.

List the current lifecycle and baton state without consuming messages:

```powershell
python relay.py threads
```

Read once when no watcher is active:

```powershell
python relay.py unseen --for claude
```

Run one watcher when the user requests ongoing monitoring:

```powershell
python relay.py watch --for claude --interval 5
```

While that watcher is active, it exclusively owns `.duet/seen.claude`; never start another watcher or run `unseen --for claude`. Never run `unseen --for codex`.

Send a short reply:

```powershell
python relay.py post --thread <issue-slug> --from claude --next codex --body "Review complete."
```

For a substantive reply, write the complete body to `.duet/outbox.md`, then run:

```powershell
python relay.py post --thread <issue-slug> --from claude --next codex --outbox
```

Use `--next user` for a decision the user must make and `--next none` only when no reply or action remains. Keep the first non-empty line concise because it becomes the dashboard summary. Reply with the same issue slug shown by `unseen`; lifecycle folders are resolved automatically.

Only Claude writes the single-slot outbox, one message at a time. Analyze Codex's message before replying. Use `threads`, then read only the relevant lifecycle Markdown for history or recovery. Do not edit thread files or generated `AI-Threads/index.html`. Stop the watcher before relay maintenance. The owning agent moves an approved thread with `python relay.py move --thread <issue-slug> --to working` and, after a final `--next none` outcome, to `completed`; the relay rejects completion without that final baton. Repair only a stale dashboard with `python relay.py dashboard`.
````

## Claude permission template

Show these additions to the user before merging them into `.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "Bash(python relay.py post:*)",
      "Bash(python relay.py unseen:*)",
      "Bash(python relay.py watch:*)",
      "Bash(python relay.py threads)",
      "Bash(python relay.py move:*)",
      "Bash(python relay.py dashboard)"
    ]
  }
}
```

## Local ignore template

Offer these entries without replacing unrelated ignore rules:

```gitignore
.duet/
AI-Threads/
__pycache__/
*.py[cod]
```
