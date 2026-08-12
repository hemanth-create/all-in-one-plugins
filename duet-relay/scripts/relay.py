#!/usr/bin/env python3
"""Local Markdown message relay for Codex and Claude.

All paths resolve from this file so each repository owns its threads and state.
The implementation uses only the Python standard library.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import glob
import html
import os
import re
import sys
import time
import uuid


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))


def _resolve_base() -> str:
    """Base directory for relay state: $DUET_HOME when set, else this file's dir."""
    home = os.environ.get("DUET_HOME")
    return os.path.abspath(home) if home else HERE


BASE = _resolve_base()
THREADS = os.path.join(BASE, "AI-Threads")
STATE = os.path.join(BASE, ".duet")
OUTBOX = os.path.join(STATE, "outbox.md")
LOCK_FILE = os.path.join(STATE, "relay.lock")
DASHBOARD = os.path.join(THREADS, "index.html")

AGENTS = ("claude", "codex")
NEXT_ACTORS = ("user", "codex", "claude", "none")
STAGES = ("planning", "working", "completed")
ACTIVE_STAGES = ("planning", "working")
MAX_BODY_BYTES = 256 * 1024
SUMMARY_CHARS = 120
ACTIVITY_LIMIT = 8
COMPLETED_LIMIT = 3
THREAD_NAME = re.compile(r"^[a-z0-9](?:[a-z0-9._-]{0,62}[a-z0-9_-])?$")
WINDOWS_RESERVED = {
    "con",
    "prn",
    "aux",
    "nul",
    *(f"com{number}" for number in range(1, 10)),
    *(f"lpt{number}" for number in range(1, 10)),
}
HEADER = re.compile(
    r"^\*\*(?P<who>claude|codex)\*\* \u00b7 "
    r"(?P<at>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z) \u00b7 "
    r"#(?P<id>[0-9a-f]{12})"
    r"(?: \u00b7 next:(?P<next>user|codex|claude|none))?\n"
    r"(?P<body>.*?)\n<!-- duet:end #(?P=id) -->",
    re.MULTILINE | re.DOTALL,
)


@dataclass(frozen=True)
class Message:
    sender: str
    timestamp: str
    message_id: str
    body: str
    next_actor: str


@dataclass(frozen=True)
class Thread:
    name: str
    stage: str
    path: str
    messages: tuple[Message, ...]


DASHBOARD_STYLE = """
:root {
  color-scheme: light;
  --canvas: #f7f7f4;
  --surface: #ffffff;
  --ink: #26251e;
  --body: #5a5852;
  --muted: #807d72;
  --hairline: #e6e5e0;
  --hairline-strong: #cfcdc4;
  --attention: #f54e00;
  --attention-soft: #fff0e8;
  --planning: #e8f0fa;
  --planning-border: #9fbbe0;
  --working: #eee8f6;
  --working-border: #c0a8dd;
  --completed: #e5f3ec;
  --completed-border: #1f8a65;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--canvas);
  color: var(--ink);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
  font-size: 14px;
  line-height: 1.5;
}
a { color: inherit; text-decoration-color: var(--hairline-strong); text-underline-offset: 3px; }
a:hover { text-decoration-color: var(--ink); }
a:focus-visible { outline: 2px solid var(--ink); outline-offset: 3px; }
.shell { width: min(1320px, calc(100% - 32px)); margin: 0 auto; padding: 28px 0 48px; }
.topbar, .section-head, .agent, .activity-row, .completed-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.topbar { margin-bottom: 20px; }
h1, h2, p { margin: 0; }
h1 { font-size: 24px; font-weight: 500; letter-spacing: -0.4px; }
h2 { font-size: 13px; font-weight: 650; letter-spacing: 0.06em; text-transform: uppercase; }
.meta, .secondary, time { color: var(--muted); font-size: 12px; }
.mono, time, .thread-name { font-family: ui-monospace, "SFMono-Regular", Consolas, monospace; }
.panel {
  background: var(--surface);
  border: 1px solid var(--hairline);
  border-radius: 12px;
  margin-bottom: 16px;
  overflow: hidden;
}
.panel-body { padding: 18px; }
.section-head { border-bottom: 1px solid var(--hairline); padding: 12px 16px; }
.attention { border-color: #f6b18d; background: var(--attention-soft); }
.attention .section-head { border-color: #f6b18d; color: #a93400; }
.attention-list, .completed-list, .activity-list { list-style: none; margin: 0; padding: 0; }
.attention-row { display: grid; grid-template-columns: minmax(160px, 0.35fr) 1fr auto; gap: 16px; padding: 12px 16px; border-top: 1px solid #f6c8b0; }
.attention-row:first-child { border-top: 0; }
.empty { color: var(--muted); padding: 14px 16px; }
.agent-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin-bottom: 16px; }
.agent { justify-content: flex-start; background: var(--surface); border: 1px solid var(--hairline); border-radius: 12px; padding: 14px 16px; min-width: 0; }
.agent-name { flex: 0 0 62px; font-weight: 650; }
.agent-status { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.badge { display: inline-flex; align-items: center; border: 1px solid var(--hairline-strong); border-radius: 999px; padding: 2px 8px; font-size: 11px; font-weight: 650; letter-spacing: 0.04em; text-transform: uppercase; white-space: nowrap; }
.badge-planning { background: var(--planning); border-color: var(--planning-border); }
.badge-working { background: var(--working); border-color: var(--working-border); }
.badge-completed { background: var(--completed); border-color: var(--completed-border); }
.badge-user { background: var(--attention-soft); border-color: #f6b18d; color: #a93400; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; table-layout: fixed; }
th { color: var(--muted); font-size: 11px; font-weight: 650; letter-spacing: 0.06em; padding: 10px 14px; text-align: left; text-transform: uppercase; }
td { border-top: 1px solid var(--hairline); padding: 12px 14px; vertical-align: top; }
th:nth-child(1) { width: 19%; }
th:nth-child(2) { width: 12%; }
th:nth-child(3) { width: 41%; }
th:nth-child(4) { width: 11%; }
th:nth-child(5) { width: 17%; }
.status-copy { color: var(--body); overflow-wrap: anywhere; }
.lower-grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(300px, 0.72fr); gap: 16px; }
.activity-row, .completed-row { align-items: flex-start; border-top: 1px solid var(--hairline); padding: 11px 16px; }
.activity-row:first-child, .completed-row:first-child { border-top: 0; }
.activity-copy { color: var(--body); flex: 1; min-width: 0; }
.activity-who { color: var(--ink); font-weight: 650; }
.count { color: var(--muted); font-size: 12px; font-weight: 500; letter-spacing: 0; text-transform: none; }
@media (max-width: 720px) {
  .shell { width: min(100% - 20px, 640px); padding-top: 18px; }
  .topbar, .section-head { align-items: flex-start; flex-direction: column; gap: 4px; }
  .agent-grid, .lower-grid { grid-template-columns: 1fr; }
  .attention-row { grid-template-columns: 1fr; gap: 4px; }
  table, tbody, tr, td { display: block; width: 100%; }
  thead { display: none; }
  tr { border-top: 1px solid var(--hairline); padding: 8px 0; }
  tr:first-child { border-top: 0; }
  td { border: 0; display: grid; grid-template-columns: 82px minmax(0, 1fr); gap: 10px; padding: 5px 14px; }
  td::before { color: var(--muted); content: attr(data-label); font-size: 11px; font-weight: 650; letter-spacing: 0.05em; text-transform: uppercase; }
  .agent { align-items: flex-start; }
  .agent-status { white-space: normal; }
}
""".strip()


def _validate_agent(value: str, command: str) -> None:
    if value not in AGENTS:
        raise SystemExit(f"{command}: agent must be one of: {', '.join(AGENTS)}")


def _other_agent(sender: str) -> str:
    return "claude" if sender == "codex" else "codex"


def _is_valid_thread_name(name: str) -> bool:
    reserved = name.split(".", 1)[0] in WINDOWS_RESERVED
    return bool(THREAD_NAME.fullmatch(name)) and not reserved


def _thread_name(raw_name: str, command: str) -> str:
    name = raw_name[:-3] if raw_name.endswith(".md") else raw_name
    if not _is_valid_thread_name(name):
        raise SystemExit(
            f"{command}: thread must be a portable 1-64 character lowercase name; "
            "paths, trailing dots, and Windows device names are not allowed"
        )
    return name


def _stage_path(stage: str, name: str) -> str:
    return os.path.join(THREADS, stage, f"{name}.md")


def _managed_path(path: str, command: str) -> str:
    root_input = os.path.abspath(THREADS)
    root = os.path.normcase(os.path.realpath(root_input))
    relative = os.path.relpath(os.path.abspath(path), root_input)
    expected = os.path.normcase(os.path.abspath(os.path.join(root, relative)))
    resolved = os.path.normcase(os.path.realpath(path))
    try:
        contained = os.path.commonpath((root, resolved)) == root
    except ValueError:
        contained = False
    if not contained or resolved != expected:
        raise SystemExit(
            f"{command}: path must be a direct file inside the relay thread directory: "
            f"{path}"
        )
    return path


def _thread_locations(name: str) -> list[tuple[str, str, bool]]:
    locations = [
        (stage, _stage_path(stage, name), False)
        for stage in STAGES
        if os.path.isfile(_stage_path(stage, name))
    ]
    legacy = os.path.join(THREADS, f"{name}.md")
    if os.path.isfile(legacy):
        locations.append(("planning", legacy, True))
    return locations


def _resolve_thread(
    name: str, command: str, *, required: bool = False
) -> tuple[str, str, bool] | None:
    locations = _thread_locations(name)
    if len(locations) > 1:
        paths = ", ".join(path for _, path, _ in locations)
        raise SystemExit(f"{command}: duplicate thread '{name}' exists at: {paths}")
    if not locations:
        if required:
            raise SystemExit(f"{command}: thread '{name}' does not exist")
        return None
    return locations[0]


def _parse_messages(content: str) -> tuple[Message, ...]:
    messages: list[Message] = []
    for match in HEADER.finditer(content):
        sender = match["who"]
        messages.append(
            Message(
                sender=sender,
                timestamp=match["at"],
                message_id=match["id"],
                body=match["body"].strip(),
                next_actor=match["next"] or _other_agent(sender),
            )
        )
    return tuple(messages)


def _read_messages(path: str) -> tuple[Message, ...]:
    with open(path, encoding="utf-8") as handle:
        return _parse_messages(handle.read())


def _summary(body: str) -> str:
    for line in body.splitlines():
        normalized = " ".join(line.split())
        if normalized:
            if len(normalized) > SUMMARY_CHARS:
                return normalized[: SUMMARY_CHARS - 1] + "\u2026"
            return normalized
    return "No message summary."


def _thread_files() -> list[tuple[str, str, str]]:
    files: list[tuple[str, str, str]] = []
    for path in glob.glob(os.path.join(THREADS, "*.md")):
        name = os.path.basename(path)[:-3]
        if os.path.isfile(path) and _is_valid_thread_name(name):
            files.append(("planning", name, path))
    for stage in STAGES:
        for path in glob.glob(os.path.join(THREADS, stage, "*.md")):
            name = os.path.basename(path)[:-3]
            if os.path.isfile(path) and _is_valid_thread_name(name):
                files.append((stage, name, path))
    return sorted(files, key=lambda item: (STAGES.index(item[0]), item[1], item[2]))


def _load_threads(command: str) -> list[Thread]:
    threads: list[Thread] = []
    names: dict[str, str] = {}
    for stage, name, path in _thread_files():
        _managed_path(path, command)
        if name in names:
            raise SystemExit(
                f"{command}: duplicate thread '{name}' exists at: {names[name]}, {path}"
            )
        names[name] = path
        messages = _read_messages(path)
        threads.append(Thread(name=name, stage=stage, path=path, messages=messages))
    return threads


def _latest(thread: Thread) -> Message | None:
    return thread.messages[-1] if thread.messages else None


def _updated(thread: Thread) -> str:
    latest = _latest(thread)
    if latest:
        return latest.timestamp
    modified = datetime.fromtimestamp(os.path.getmtime(thread.path), timezone.utc)
    return modified.strftime("%Y-%m-%dT%H:%M:%SZ")


def _next_actor(thread: Thread) -> str:
    if thread.stage == "completed":
        return "none"
    latest = _latest(thread)
    return latest.next_actor if latest else "none"


def _thread_summary(thread: Thread) -> str:
    latest = _latest(thread)
    return _summary(latest.body) if latest else "No complete relay messages."


def _display_time(timestamp: str) -> str:
    parsed = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    )
    return parsed.astimezone().strftime("%b %d, %Y %I:%M %p %Z")


def _thread_href(thread: Thread) -> str:
    return os.path.relpath(thread.path, THREADS).replace(os.sep, "/")


def _escaped(value: str) -> str:
    return html.escape(value, quote=True)


def _actor_label(actor: str) -> str:
    return {"user": "You", "codex": "Codex", "claude": "Claude", "none": "None"}[
        actor
    ]


def _thread_link(thread: Thread) -> str:
    return (
        f'<a class="thread-name" href="{_escaped(_thread_href(thread))}" '
        f'target="_blank" rel="noopener">{_escaped(thread.name)}</a>'
    )


def _events(
    threads: list[Thread], agent: str | None = None
) -> list[tuple[str, float, int, str, str, Thread, Message]]:
    events: list[tuple[str, float, int, str, str, Thread, Message]] = []
    for thread in threads:
        modified = os.path.getmtime(thread.path)
        for index, message in enumerate(thread.messages):
            if agent is None or message.sender == agent:
                events.append(
                    (
                        message.timestamp,
                        modified,
                        index,
                        thread.name,
                        message.message_id,
                        thread,
                        message,
                    )
                )
    return events


def _active_table(threads: list[Thread]) -> str:
    active = [thread for thread in threads if thread.stage in ACTIVE_STAGES]
    active.sort(
        key=lambda thread: (
            _next_actor(thread) == "user",
            thread.stage == "working",
            _updated(thread),
            thread.name,
        ),
        reverse=True,
    )
    if not active:
        rows = '<tr><td class="empty" colspan="5">No active threads.</td></tr>'
    else:
        rows = "".join(
            (
                f'<tr data-thread="{_escaped(thread.name)}">'
                f'<td data-label="Thread">{_thread_link(thread)}</td>'
                f'<td data-label="Stage"><span class="badge badge-{thread.stage}">'
                f'{_escaped(thread.stage)}</span></td>'
                f'<td class="status-copy" data-label="Status">'
                f'{_escaped(_thread_summary(thread))}</td>'
                f'<td data-label="Next"><span class="badge '
                f'{"badge-user" if _next_actor(thread) == "user" else ""}">'
                f'{_escaped(_actor_label(_next_actor(thread)))}</span></td>'
                f'<td data-label="Updated"><time datetime="{_escaped(_updated(thread))}">'
                f'{_escaped(_display_time(_updated(thread)))}</time></td>'
                "</tr>"
            )
            for thread in active
        )
    return (
        '<div class="panel"><div class="section-head"><h2>Active Threads</h2>'
        f'<span class="count">{len(active)} open</span></div>'
        '<div class="table-wrap"><table aria-label="Active relay threads"><thead><tr>'
        '<th scope="col">Thread</th><th scope="col">Stage</th>'
        '<th scope="col">Status</th><th scope="col">Next</th>'
        '<th scope="col">Updated</th></tr></thead>'
        f"<tbody>{rows}</tbody></table></div></div>"
    )


def _attention_panel(threads: list[Thread]) -> str:
    waiting = [
        thread
        for thread in threads
        if thread.stage in ACTIVE_STAGES and _next_actor(thread) == "user"
    ]
    waiting.sort(key=lambda thread: (_updated(thread), thread.name), reverse=True)
    if waiting:
        content = '<ul class="attention-list">' + "".join(
            (
                f'<li class="attention-row" data-attention-thread="{_escaped(thread.name)}">'
                f'{_thread_link(thread)}<span>{_escaped(_thread_summary(thread))}</span>'
                f'<time datetime="{_escaped(_updated(thread))}">'
                f'{_escaped(_display_time(_updated(thread)))}</time></li>'
            )
            for thread in waiting
        ) + "</ul>"
    else:
        content = '<p class="empty">Nothing is waiting on you.</p>'
    return (
        '<section class="panel attention"><div class="section-head">'
        '<h2>Needs Your Attention</h2>'
        f'<span class="count">{len(waiting)} item(s)</span></div>{content}</section>'
    )


def _agent_card(agent: str, threads: list[Thread]) -> str:
    reports = _events(
        [thread for thread in threads if thread.stage in ACTIVE_STAGES], agent
    )
    if not reports:
        status = '<span class="agent-status secondary">No active thread reported.</span>'
        detail = ""
    else:
        *_, thread, message = max(reports, key=lambda item: item[:5])
        status = (
            f'<span class="agent-status">{_escaped(_summary(message.body))}</span>'
        )
        detail = (
            f'<span class="secondary">{_thread_link(thread)} \u00b7 '
            f'{_escaped(_display_time(message.timestamp))}</span>'
        )
    return (
        f'<div class="agent" data-agent="{agent}"><span class="agent-name">'
        f'{agent.title()}</span>{status}{detail}</div>'
    )


def _completed_panel(threads: list[Thread]) -> str:
    completed = [thread for thread in threads if thread.stage == "completed"]
    completed.sort(key=lambda thread: (_updated(thread), thread.name), reverse=True)
    recent = completed[:COMPLETED_LIMIT]
    if recent:
        content = '<ul class="completed-list">' + "".join(
            (
                f'<li class="completed-row">{_thread_link(thread)}'
                f'<time datetime="{_escaped(_updated(thread))}">'
                f'{_escaped(_display_time(_updated(thread)))}</time></li>'
            )
            for thread in recent
        ) + "</ul>"
    else:
        content = '<p class="empty">No completed threads.</p>'
    return (
        '<section class="panel"><div class="section-head"><h2>Recently Completed</h2>'
        f'<span class="count">latest {min(len(completed), COMPLETED_LIMIT)} of '
        f'{len(completed)}</span></div>{content}</section>'
    )


def _activity_panel(threads: list[Thread]) -> str:
    events = _events(threads)
    events.sort(key=lambda item: item[:5], reverse=True)
    recent = events[:ACTIVITY_LIMIT]
    if recent:
        content = '<ol class="activity-list">' + "".join(
            (
                '<li class="activity-row">'
                f'<span class="activity-copy"><span class="activity-who">'
                f'{_escaped(message.sender.title())}</span> in {_thread_link(thread)}: '
                f'{_escaped(_summary(message.body))}</span>'
                f'<time datetime="{_escaped(message.timestamp)}">'
                f'{_escaped(_display_time(message.timestamp))}</time></li>'
            )
            for *_, thread, message in recent
        ) + "</ol>"
    else:
        content = '<p class="empty">No relay activity yet.</p>'
    return (
        '<section class="panel"><div class="section-head"><h2>Latest Activity</h2>'
        f'<span class="count">latest {len(recent)}</span></div>{content}</section>'
    )


def _dashboard_html(threads: list[Thread]) -> str:
    generated = datetime.now().astimezone()
    generated_iso = generated.isoformat(timespec="seconds")
    generated_text = generated.strftime("%b %d, %Y %I:%M %p %Z")
    return (
        "<!doctype html>\n<html lang=\"en\">\n<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<meta http-equiv="refresh" content="5">\n'
        '<meta http-equiv="Content-Security-Policy" '
        'content="default-src \'none\'; style-src \'unsafe-inline\'; base-uri \'none\'; '
        'form-action \'none\'">\n'
        "<title>Relay Dashboard</title>\n"
        f"<style>{DASHBOARD_STYLE}</style>\n</head>\n<body>\n"
        '<main class="shell"><header class="topbar"><div><h1>Relay Dashboard</h1>'
        '<p class="secondary">Codex and Claude local coordination</p></div>'
        f'<p class="meta">Last generated <time datetime="{_escaped(generated_iso)}">'
        f'{_escaped(generated_text)}</time> \u00b7 refreshes every 5 seconds</p></header>'
        f"{_attention_panel(threads)}"
        '<section class="agent-grid" aria-label="Agent status">'
        f'{_agent_card("codex", threads)}{_agent_card("claude", threads)}</section>'
        f"{_active_table(threads)}"
        '<div class="lower-grid">'
        f"{_completed_panel(threads)}{_activity_panel(threads)}</div>"
        "</main>\n</body>\n</html>\n"
    )


def _message_body(value: str | None) -> str:
    body = (value or "").strip()
    if not body:
        raise SystemExit("post: message body is empty")
    if len(body.encode("utf-8")) > MAX_BODY_BYTES:
        raise SystemExit(f"post: message body exceeds {MAX_BODY_BYTES} UTF-8 bytes")
    return body


def _read_outbox() -> str:
    expected = os.path.normcase(os.path.abspath(OUTBOX))
    resolved = os.path.normcase(os.path.realpath(OUTBOX))
    if resolved != expected or not os.path.isfile(OUTBOX):
        raise SystemExit(f"post: outbox must be a regular file at {OUTBOX}")
    with open(OUTBOX, encoding="utf-8") as handle:
        return handle.read()


def _clear_outbox() -> None:
    """Empty the single-slot outbox so stale content cannot be re-sent."""
    with open(OUTBOX, "w", encoding="utf-8", newline="\n") as handle:
        handle.flush()
        os.fsync(handle.fileno())


@contextmanager
def _relay_lock():
    """Serialize relay readers and writers across processes."""
    os.makedirs(STATE, exist_ok=True)
    with open(LOCK_FILE, "a+b") as handle:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"\0")
            handle.flush()
        handle.seek(0)

        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


@contextmanager
def _watch_lock(role: str):
    """Hold an exclusive, watcher-lifetime lock so only one watcher owns a role's cursor."""
    os.makedirs(STATE, exist_ok=True)
    lock_path = os.path.join(STATE, f"watch.{role}.lock")
    busy = f"watch: another {role} watcher is already running; stop it first"
    with open(lock_path, "a+b") as handle:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"\0")
            handle.flush()
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError:
                raise SystemExit(busy)
            try:
                yield
            finally:
                handle.seek(0)
                try:
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                except OSError:
                    pass
        else:
            import fcntl

            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                raise SystemExit(busy)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _durable_append(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())


def _atomic_write(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temporary = _managed_path(path + ".tmp", "dashboard")
    try:
        with open(temporary, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.remove(temporary)


def _render_dashboard() -> None:
    _atomic_write(
        _managed_path(DASHBOARD, "dashboard"),
        _dashboard_html(_load_threads("dashboard")),
    )


def _dashboard_warning(command: str) -> str | None:
    try:
        _render_dashboard()
    except (OSError, UnicodeError, SystemExit) as error:
        return (
            f"{command}: relay history was saved, but dashboard update failed: {error}; "
            "run `python relay.py dashboard` and do not repeat the completed operation"
        )
    return None


def _seen_file(agent: str) -> str:
    return os.path.join(STATE, f"seen.{agent}")


def _load_seen(agent: str) -> set[str]:
    path = _seen_file(agent)
    if not os.path.exists(path):
        return set()
    with open(path, encoding="utf-8") as handle:
        return set(handle.read().split())


def post(args: argparse.Namespace) -> None:
    _validate_agent(args.sender, "post")
    name = _thread_name(args.thread, "post")
    warning: str | None = None

    with _relay_lock():
        location = _resolve_thread(name, "post")
        if location is not None and location[0] == "completed":
            raise SystemExit(f"post: completed thread '{name}' is read-only")
        body = _message_body(_read_outbox() if args.outbox else args.body)
        if location is None:
            stage = "planning"
            thread_path = _managed_path(_stage_path(stage, name), "post")
        else:
            stage, thread_path, legacy = location
            _managed_path(thread_path, "post")
            if legacy:
                destination = _managed_path(_stage_path("planning", name), "post")
                os.makedirs(os.path.dirname(destination), exist_ok=True)
                os.replace(thread_path, destination)
                thread_path = destination

        next_actor = getattr(args, "next_actor", None) or _other_agent(args.sender)
        message_id = uuid.uuid4().hex[:12]
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        block = (
            f"\n**{args.sender}** \u00b7 {timestamp} \u00b7 #{message_id} "
            f"\u00b7 next:{next_actor}\n"
            f"{body}\n<!-- duet:end #{message_id} -->\n"
        )
        _durable_append(thread_path, block)
        if args.outbox:
            _clear_outbox()
        warning = _dashboard_warning("post")

    print(message_id, flush=True)
    if warning:
        print(warning, file=sys.stderr, flush=True)


def move(args: argparse.Namespace) -> None:
    name = _thread_name(args.thread, "move")
    warning: str | None = None

    with _relay_lock():
        stage, source, _ = _resolve_thread(name, "move", required=True)
        _managed_path(source, "move")
        target = args.target
        if stage != "completed" and target == "completed":
            messages = _read_messages(source)
            if not messages or messages[-1].next_actor != "none":
                raise SystemExit(
                    "move: post a final thread update with --next none before completing"
                )
        if stage == target:
            destination = source
        elif stage == "planning" and target in ("working", "completed"):
            destination = _managed_path(_stage_path(target, name), "move")
        elif stage == "working" and target == "completed":
            destination = _managed_path(_stage_path(target, name), "move")
        else:
            raise SystemExit(
                f"move: invalid transition for '{name}': {stage} -> {target}"
            )

        if os.path.normcase(os.path.abspath(source)) != os.path.normcase(
            os.path.abspath(destination)
        ):
            if os.path.exists(destination):
                raise SystemExit(f"move: destination already exists: {destination}")
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            os.replace(source, destination)
        warning = _dashboard_warning("move")

    print(f"{target}/{name}.md", flush=True)
    if warning:
        print(warning, file=sys.stderr, flush=True)


def threads(args: argparse.Namespace) -> None:
    del args
    with _relay_lock():
        found = _load_threads("threads")
        if not found:
            output = "No threads."
        else:
            lines = ["STAGE\tTHREAD\tNEXT\tUPDATED\tSUMMARY"]
            lines.extend(
                f"{thread.stage}\t{thread.name}\t{_next_actor(thread)}\t"
                f"{_updated(thread)}\t{_thread_summary(thread)}"
                for thread in found
            )
            output = "\n".join(lines)
    print(output, flush=True)


def dashboard(args: argparse.Namespace) -> None:
    del args
    with _relay_lock():
        try:
            _render_dashboard()
        except (OSError, UnicodeError) as error:
            raise SystemExit(f"dashboard: could not write {DASHBOARD}: {error}") from error
    print(DASHBOARD, flush=True)


def unseen(args: argparse.Namespace) -> None:
    _validate_agent(args.whoami, "unseen")

    with _relay_lock():
        seen = _load_seen(args.whoami)
        fresh: list[str] = []
        output: list[str] = []

        # ponytail: whole-file scans keep the local protocol simple; add indexed
        # storage only if real thread sizes make this measurably expensive.
        for thread in _load_threads("unseen"):
            channel = f"{thread.stage}/{thread.name}"
            for message in thread.messages:
                message_id = message.message_id
                if message.sender != args.whoami and message_id not in seen:
                    output.append(
                        f"### [{channel}] {message.sender} #{message_id} "
                        f"\u00b7 next:{message.next_actor}\n{message.body}"
                    )
                    fresh.append(message_id)

        if fresh:
            print("\n\n".join(output), flush=True)
            _durable_append(_seen_file(args.whoami), " ".join(fresh) + " ")


def watch(args: argparse.Namespace) -> None:
    _validate_agent(args.whoami, "watch")
    with _watch_lock(args.whoami):
        try:
            while True:
                try:
                    unseen(args)
                except SystemExit as error:
                    print(f"watch: skipped a cycle: {error}", file=sys.stderr, flush=True)
                except OSError as error:
                    print(f"watch: transient error: {error}", file=sys.stderr, flush=True)
                time.sleep(args.interval)
        except KeyboardInterrupt:
            return


def _interval(value: str) -> float:
    try:
        seconds = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("interval must be a number") from error
    if not 0.25 <= seconds <= 3600:
        raise argparse.ArgumentTypeError("interval must be between 0.25 and 3600 seconds")
    return seconds


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="local Markdown relay between Claude and Codex"
    )
    commands = parser.add_subparsers(dest="command", required=True)

    post_parser = commands.add_parser("post", help="append a message to a channel")
    post_parser.add_argument(
        "--thread",
        required=True,
        help="lowercase channel name, for example review",
    )
    post_parser.add_argument("--from", dest="sender", required=True, choices=AGENTS)
    post_parser.add_argument(
        "--next",
        dest="next_actor",
        choices=NEXT_ACTORS,
        help="next actor: user, codex, claude, or none (default: the other agent)",
    )
    body = post_parser.add_mutually_exclusive_group(required=True)
    body.add_argument("--body", help="message text")
    body.add_argument(
        "--outbox",
        action="store_true",
        help="read message text from the fixed .duet/outbox.md file",
    )
    post_parser.set_defaults(handler=post)

    unseen_parser = commands.add_parser(
        "unseen",
        help="print unread messages and advance one role's cursor",
    )
    unseen_parser.add_argument("--for", dest="whoami", required=True, choices=AGENTS)
    unseen_parser.set_defaults(handler=unseen)

    threads_parser = commands.add_parser(
        "threads",
        help="list thread lifecycle and latest baton state",
    )
    threads_parser.set_defaults(handler=threads)

    move_parser = commands.add_parser(
        "move",
        help="move a thread forward in its lifecycle",
    )
    move_parser.add_argument("--thread", required=True, help="thread name")
    move_parser.add_argument(
        "--to",
        dest="target",
        required=True,
        choices=("working", "completed"),
    )
    move_parser.set_defaults(handler=move)

    dashboard_parser = commands.add_parser(
        "dashboard",
        help="rebuild the local read-only HTML dashboard",
    )
    dashboard_parser.set_defaults(handler=dashboard)

    watch_parser = commands.add_parser(
        "watch",
        help="poll unread messages until interrupted",
    )
    watch_parser.add_argument("--for", dest="whoami", required=True, choices=AGENTS)
    watch_parser.add_argument(
        "--interval",
        type=_interval,
        default=5.0,
        help="poll interval in seconds (default: 5)",
    )
    watch_parser.set_defaults(handler=watch)

    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    args.handler(args)


if __name__ == "__main__":
    main()
