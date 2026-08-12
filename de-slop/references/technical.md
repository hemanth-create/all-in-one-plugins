# Technical writing: comments, docstrings, commits, ADRs, PRs

Prose rules misfire here. A reader of an essay wants voice and flow; a reader of a code comment or a
commit log is doing a task and wants precision. Some patterns that read as slop in prose — an
actor-less passive, a hedge, a qualifier, a roadmap — are correct and load-bearing in technical
writing. De-slop technical text by cutting *noise* (restatement, filler, ceremony) while protecting
*signal* (the why, the caveat, the exact value).

Read the **What not to strip** section at the bottom before editing any of these artifacts.

## Code comments

Cut comments that restate the code. Keep comments that explain what the code cannot say for itself.

- **Cut restatement.** `i++ // increment i`, `// constructor`, `// return the result`. The code
  already says this.
- **Cut stale narration.** Comments describing an old version of the code are worse than none.
- **Keep the *why*.** `// batch of 500 — the API rejects larger payloads`. The reason isn't in the
  code, and someone will "clean up" the magic number without it.
- **Keep non-obvious constraints and hazards.** `// must hold lock before calling`, `// not
  thread-safe`, `// O(n²); fine for n<100, revisit above that`.
- **Keep task markers with context.** `// TODO(2026-06): remove after clients migrate off v1
  (see #4821)` beats a bare `// TODO`.

## Docstrings

State what the function does and how to call it correctly. Cut ceremony, keep the contract.

- **Cut padding.** "This function is used to…" → "Returns…". "A helper that basically…" → describe
  the behavior.
- **Keep the full contract.** Parameters, return value, raised errors, units, and side effects. Do
  not trim parameter docs to look terse — an undocumented `timeout` (seconds? ms?) costs the reader
  a trip to the source.
- **Keep examples.** A short usage example is signal, not filler.
- **Keep behavioral caveats.** "Returns `None` if the cache is cold", "not reentrant", "mutates
  `items` in place".

## Commit messages

The log is read years later by someone bisecting a bug. Write for them.

- **Cut empty subjects.** "update files", "fix stuff", "changes", "wip", "misc".
- **Use the imperative subject.** "Add retry to the S3 client", not "Added" or "Adding".
- **Say what changed and why in the body.** The diff shows *what*; the message carries the *why* the
  diff can't: the bug it fixes, the constraint it satisfies, the approach rejected.
- **Keep references.** Issue and PR numbers, `Fixes #1234`, `Co-authored-by`, revert hashes.

## ADRs (Architecture Decision Records)

The entire value of an ADR is the reasoning and the roads not taken. Cut the throat-clearing and the
hedging-as-filler; keep the substance that a naive de-slopper would mistake for slop.

- **Cut** preamble ("This document aims to outline…"), and vague declaratives ("the tradeoffs are
  significant" — name them).
- **Keep Context, Alternatives, and Consequences.** The list of options you *rejected* looks like
  "negative listing," but it is the core content: it stops the team from relitigating the decision.
- **Keep the honest downsides.** "This raises write latency ~15ms" is why the record is trustworthy.

## PR descriptions

- **Cut filler openers.** "This PR aims to…", "In this PR, we…" → state what it does.
- **Keep the test plan.** How you verified it, what you ran, what you couldn't cover.
- **Keep breaking-change and migration notes**, rollback steps, and screenshots or numbers that
  prove the change works.
- If the repo has a PR template, fill its sections; don't strip them for brevity.

## What not to strip

The load-bearing detail that surface de-slopping tends to delete. When in doubt in a technical
context, keep these:

- **The "why," not just the "what."** Rationale, constraints, and the reason behind a magic number
  or an odd workaround.
- **Hedges that encode real uncertainty.** "*probably* thread-safe, but not verified under load" is a
  precise, honest signal. Flattening it to "thread-safe" is a lie. Keep calibrated hedges; cut only
  reflexive ones ("I think this is maybe kind of…").
- **Precise qualifiers and units.** "timeout in **milliseconds**", "**usually** O(n), **worst-case**
  O(n²)", "**up to** 500 items". These bound behavior; they are not padding.
- **Passive voice where the actor is irrelevant.** "The column was renamed in migration 0042",
  "The flag is read at startup." Forcing an actor in adds noise.
- **Exact values.** Numbers, version strings, error codes, config keys, flag names, file paths,
  function names. Never paraphrase these into vaguer words.
- **Links and references.** Issue/PR numbers, RFC and doc links, ticket IDs, commit hashes. They are
  the audit trail.
- **Warnings and caveats.** "here be dragons", "do not call from the render thread", "deprecated,
  remove after v4". These prevent outages.
- **Rejected alternatives and negative results.** In ADRs, PRs, and postmortems, "we tried X, it
  failed because Y" is the most valuable content, even though it looks like negative listing.
- **Reproduction and edge-case notes.** Steps to reproduce, boundary conditions, "fails only on
  ARM", "empty input returns `[]`, not an error".

The rule: in technical writing, cut what a competent reader already knows from the code or context,
and keep what they would have to rediscover the hard way.
