# de-slop

A skill for removing AI writing tells from prose **and** technical writing — without stripping the
meaning underneath them.

Reworked from [stop-slop](https://github.com/hardikpandya/stop-slop) by
[Hardik Pandya](https://hvpandya.com), used under the MIT License.

## What this is

AI writing has patterns: predictable phrases, telegraphed structures, a metronomic rhythm. This
skill teaches Claude (or any LLM) to catch and remove them. It differs from a plain pattern-matcher
in two ways: it fixes **thin content before surface polish**, and it treats each pattern as a
**judgment call**, so it doesn't mangle legitimate writing.

## What's new vs stop-slop

- **Substance first.** Slop is usually empty content in fluent clothing. Stripping adverbs from a
  paragraph that says nothing just yields a tighter nothing. de-slop diagnoses substance and
  specificity before touching the surface.
- **Judgment calls, not absolute bans.** The original banned adverbs, em dashes, passive voice, and
  three-item lists outright. de-slop replaces each ban with a keep-when test, because every one of
  those has a legitimate, information-carrying form.
- **Technical writing coverage.** A new [`references/technical.md`](references/technical.md) handles
  code comments, docstrings, commit messages, ADRs, and PR descriptions — with a **"What not to
  strip"** section that protects load-bearing detail (rationale, calibrated hedges, precise units,
  exact values, issue links, caveats, rejected alternatives).
- **Re-weighted rubric.** Substance and specificity carry the most weight and act as a gate; surface
  polish weighs least.

## Skill structure

```
de-slop/
├── SKILL.md              # Core instructions
├── references/
│   ├── phrases.md        # Word/phrase tells, with keep-when notes
│   ├── structures.md     # Structural patterns, each with "when it's fine"
│   ├── technical.md      # Code comments, docstrings, commits, ADRs, PRs
│   └── examples.md       # Before/after, including restraint
├── README.md
├── CHANGELOG.md
└── LICENSE
```

## Quick start

- **Claude Code:** add this folder as a skill.
- **Claude Projects:** upload `SKILL.md` and the `references/` files to project knowledge.
- **Custom instructions:** copy the core rules from `SKILL.md`.
- **API calls:** include `SKILL.md` in your system prompt; the reference files load on demand.

## What it catches

- **Phrase-level tells** — throat-clearing openers, emphasis crutches, business jargon, empty
  intensifiers, meta-commentary, vague declaratives. See
  [`references/phrases.md`](references/phrases.md).
- **Structural clichés** — binary contrasts, negative listing, dramatic fragmentation, rhetorical
  setups, false agency, narrator-from-a-distance. See
  [`references/structures.md`](references/structures.md).
- **Judgment calls** — adverbs, em dashes, passive voice, and manufactured triads, each kept or cut
  by whether it carries information rather than by a blanket rule.
- **Technical slop** — restated comments, padded docstrings, empty commit subjects, filler PR
  openers — while protecting the detail that must survive. See
  [`references/technical.md`](references/technical.md).

## Scoring

Rate each dimension 1–10, multiply by its weight, total out of 100:

| Dimension | Weight | Question |
|-----------|:------:|----------|
| Substance | ×3 | Real, contestable claims backed by evidence, example, or mechanism? |
| Specificity | ×3 | Concrete and named, or abstract and swappable onto any topic? |
| Directness | ×2 | States the point, or announces and throat-clears? |
| Human voice | ×1 | Sounds like someone who knows the subject? |
| Rhythm & density | ×1 | Varied sentences, nothing cuttable? |

Revise below **70/100**. Gate: if substance or specificity scores under 5, fix those first — surface
polish cannot buy back empty content.

## Credit

Original skill: [stop-slop](https://github.com/hardikpandya/stop-slop) by
[Hardik Pandya](https://hvpandya.com). This rework keeps his high-value catches (throat-clearing,
binary contrast, false agency, overused intensifiers) and his phrase/structure catalogs.

## License

MIT. The original stop-slop copyright is preserved in [`LICENSE`](LICENSE). Use freely, share widely.
