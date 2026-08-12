# Changelog

All notable changes to the de-slop skill are recorded here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/).

## 1.0.0 — 2026-08-12

Initial release. Reworked from [stop-slop](https://github.com/hardikpandya/stop-slop) by Hardik
Pandya (MIT).

### Added

- **Substance-first principle.** A new lead section and an explicit order of work (substance →
  structure → surface): diagnose whether content is real and specific before polishing sentences.
- **`references/technical.md`.** Coverage for code comments, docstrings, commit messages, ADRs, and
  PR descriptions, including a **"What not to strip"** section that protects rationale, calibrated
  hedges, precise qualifiers and units, actor-irrelevant passive voice, exact values, links, caveats,
  and rejected alternatives.
- **Re-weighted scoring rubric.** Substance (×3) and Specificity (×3) now outweigh Directness (×2),
  Human voice (×1), and Rhythm & density (×1); total out of 100, revise below 70, with a gate that
  forces a substance/specificity fix before any surface score counts.
- **New examples.** A substance-first transformation, a technical before/after paired with a
  "don't over-strip" counter-example, and a restraint example (adverbs, passive, triads, and an em
  dash that should be kept).
- **"When it's fine" / "Keep when" notes** throughout the phrase and structure references.

### Changed

- **Absolute bans converted to judgment calls.** Adverbs, em dashes, passive voice, and "two beats
  three" each now carry a keep-when test instead of a prohibition, so information-carrying uses
  survive.
- **Kept the high-value catches** from stop-slop — throat-clearing, binary contrast, false agency,
  and overused intensifiers — each annotated with its legitimate form.

### Fixed

- Corrected the dramatic-fragmentation example, whose original rewrite used an em dash while the
  source banned em dashes; it now uses a colon.

### Credit

Built on Hardik Pandya's stop-slop phrase and structure catalogs, used under the MIT License. The
original copyright is preserved in `LICENSE`.
