# Duet Relay

Duet Relay lets Codex and Claude review the same work through local Markdown threads. It keeps planning, active work, completed work, and the next responsible person visible in a local HTML dashboard. The relay itself makes no network requests.

## Install with Codex

Open the repository where you want to use the relay in Codex. Give Codex access to this package, then say:

> Install Duet Relay from the `skill/duet-relay` folder into this repository. Preserve existing project instructions and show me any Claude permission changes before applying them. Do not use Git, cloud services, the network, or start a watcher or browser.

Codex will copy the relay, add the required agent guidance, create its runtime folders, validate the installation, and generate the first dashboard.

Open `AI-Threads/index.html` by double-clicking it in File Explorer. Leave it open while working; it refreshes itself every five seconds.

## Start Claude Monitoring

Open Claude in the same repository and say:

> Read CLAUDE.md and monitor the relay. Analyze and reply to Codex messages until I say "stop the monitor."

Approve only the narrowly scoped relay permissions Codex showed during setup. Run one Claude monitor at a time; a second monitor for the same role now exits immediately instead of quietly splitting messages.

## Plan and Review Work

Describe the issue to Codex normally, then say:

> Create a relay thread for this issue, write the plan, and ask Claude to review it.

Codex creates the planning thread automatically. Claude reviews the message and returns the baton. Ask Codex to check the reply and combine both agents' recommendations:

> Check Claude's reply, analyze it, and give me the final recommendation. Mark the thread as waiting for me if a decision is needed.

The dashboard shows user decisions under **Needs Your Attention**.

## Move Through the Lifecycle

After accepting a plan, tell Codex:

> I approve. Record the approval and move this issue to working.

After implementation and validation, tell Codex:

> Post the final outcome with no next actor and mark the thread completed.

Completed threads become read-only. Start a new follow-up thread instead of reopening one.

## What the Installation Creates

- `relay.py` - the local standard-library relay.
- `AI-Threads/` - planning, working, completed histories, and `index.html`.
- `.duet/` - local unread cursors, locking state, and Claude's bounded outbox (relocatable with the `DUET_HOME` environment variable).
- Small relay sections in the repository's Codex and Claude instructions.
- Optional local ignore entries when thread history should not be versioned.

Markdown histories remain the source of truth. Agents regenerate the dashboard and never edit it directly.

## Safety and Troubleshooting

- Never place secrets, credentials, PHI, or unnecessary personal information in relay messages.
- If the dashboard is stale, ask Codex to rebuild it; do not repost the message.
- If Claude stops replying, stop duplicate monitors and ask Claude to start one monitor again.
- If a completed issue needs more work, create a new thread.
- Before updating the relay, stop monitoring and preserve the existing `AI-Threads/` and `.duet/` state.

## Share the Package

Share this entire `duet-relay` folder. If you want one transferable file, compress the folder with File Explorer and send the resulting ZIP; recipients begin with this README.

## License

MIT. See `LICENSE`.
