---
name: de-slop
description: Remove AI writing tells from prose and technical writing without cutting real meaning. Use when drafting, editing, or reviewing text — essays, docs, READMEs, code comments, docstrings, commit messages, ADRs, and PRs — or when asked to de-slop or humanize writing.
license: MIT
---

# de-slop

Cut AI writing tells without cutting the meaning underneath them.

Most "de-slopping" tools are surface pattern-matchers: ban a list of phrases, strip every adverb,
outlaw the em dash, and call the result human. That approach has two failure modes. It kills
legitimate writing (a meaningful adverb, a load-bearing passive, a genuinely three-item list), and
it leaves empty content untouched as long as the sentences sound clean. This skill fixes both by
working substance-first and treating every pattern as a judgment call, not a law.

## Substance first

Slop is usually not a phrasing problem. It is a *content* problem wearing fluent phrasing. Strip the
adverbs from a paragraph that says nothing and you get a tighter paragraph that says nothing — now
harder to spot because it reads well.

Before you touch a single sentence, check whether the writing has anything inside it:

- **Is there a claim, or a vibe?** "The implications are significant" names no implication. "Latency
  dropped from 800ms to 90ms" is a claim.
- **Is it specific, or swappable?** If you can drop in an unrelated subject and the sentence still
  "works," it says nothing. "In today's fast-moving landscape, teams must adapt" fits any topic, so
  it carries none.
- **Is there evidence?** An example, a number, a name, a mechanism — or only assertion?
- **Could a reader disagree?** If nobody could push back, you haven't said anything contestable.

Fix that first. Add the missing specific, cut the claim you can't support, replace the abstraction
with the concrete case. A paragraph that survives this check and reads slightly clunky beats a
frictionless paragraph that means nothing. Only after the substance is real do you polish the surface.

## Order of work

1. **Substance** — is the claim real, specific, and supported? Fix thin content here.
2. **Structure** — do the sentences hide the actor, telegraph fake drama, or announce instead of state?
3. **Surface** — word choice, rhythm, density. The cheapest pass, and the last.

Working top-down stops you from lavishing polish on paragraphs that should be deleted or rewritten.

## Principles

1. **State, don't announce.** Cut the run-up ("Here's the thing," "The uncomfortable truth is") and
   make the point. See [references/phrases.md](references/phrases.md).
2. **Name the specific thing.** Replace vague declaratives ("the reasons are structural") with the
   actual reason. Prefer the concrete case over the abstraction.
3. **Keep a human in the sentence.** When something happens, someone usually did it. Name them, or
   put the reader in the seat with "you." See [references/structures.md](references/structures.md).
4. **Vary the rhythm.** Monotony is a tell — three sentences of identical length, every paragraph
   ending on a punchline. Break the pattern. This is a reason to reshape, not to amputate content.
5. **Trust the reader.** Drop the softening, the permission-granting ("and that's okay"), and the
   meta-narration of your own structure ("in this section we'll…").

## High-value catches

These four are worth catching every time. Each also has a legitimate form, so check before you cut.

- **Throat-clearing** — "Here's the thing," "It turns out," "What's interesting is," "The truth is."
  Announcements that a point is coming, in place of the point. Cut to it.
  *Fine when:* a real transition orients the reader ("First, the numbers:").

- **Binary contrast** — "Not X. It's Y." / "The problem isn't X, it's Y." A telegraphed reversal that
  manufactures drama. Usually you can state Y and delete the negation.
  *Fine when:* you are correcting a belief the reader actively holds ("This isn't a rate limit; it's a
  deadlock" earns the contrast because the reader would otherwise misdiagnose it).

- **False agency** — inanimate things doing human work: "the complaint becomes a fix," "the data
  tells us," "the decision emerges." It reads smooth because it dodges naming who acted. Name the
  human, or use "you."
  *Fine when:* the subject really is the agent, or it's settled idiom ("the compiler infers the type,"
  "the market cleared").

- **Empty intensifiers** — "deeply," "truly," "fundamentally," "really," "just," "simply," "literally."
  Delete one and read the sentence back; if nothing was lost, it was propping up a weak claim.
  *Fine when:* the word carries information — "simply" meaning *in one step, no config*, or "literally"
  when you mean it.

## Judgment calls, not bans

The original stop-slop banned these outright. Absolute bans are easy to follow and often wrong. Use
the test instead of the prohibition.

- **Adverbs.** Most `-ly` words prop up a weak verb ("walked quickly" → "hurried") or hedge a claim
  you should make or drop. Cut those. But some carry information no other word supplies: "the test
  fails *intermittently*" is a precise fact; "*deliberately* vague" means something exact.
  **Test:** does the word add information the sentence loses without it? If yes, keep it.

- **Em dashes.** The tell is *mechanical overuse* — one in every paragraph as a rhythmic tic, or a
  dash faking a dramatic pause where a colon belongs. That is the fingerprint, not the character
  itself. A single em dash doing real syntactic work (a sharp aside, an appositive) is fine.
  **Test:** count them. If every paragraph has one, thin them out. If one is earning its place, leave it.

- **Passive voice.** Passive becomes slop when it hides an actor you should name ("mistakes were made"
  — by whom?). But it's correct when the object is the topic and the actor is unknown, irrelevant, or
  obvious: "the endpoint was deprecated in v3," "users are notified by email."
  **Test:** does naming the actor add information? If not, the passive stays.

- **"Two beats three."** A rhythm heuristic, not a counting rule. The tell is the *manufactured triad*
  — padding a list to three because three sounds authoritative, or the escalating "X. And Y. And Z."
  drumbeat. If you have three real things, list three. If the third repeats the first two, cut it.

## Technical writing

Prose rules misfire on code comments, docstrings, commit messages, ADRs, and PR descriptions, where
precision outranks voice and some "prose slop" (an actor-less passive, a hedge, a qualifier) is
exactly right. Before editing any of these, read
[references/technical.md](references/technical.md) — especially its **"What not to strip"** section,
which lists the load-bearing detail a naive de-slopper wrongly deletes.

## Scoring

Rate each dimension 1–10, multiply by its weight, and total out of 100. Substance and specificity
carry the most weight because clean prose over empty content is still slop.

| Dimension | Weight | Question |
|-----------|:------:|----------|
| Substance | ×3 | Real, contestable claims backed by evidence, example, or mechanism? |
| Specificity | ×3 | Concrete and named, or abstract and swappable onto any topic? |
| Directness | ×2 | States the point, or announces and throat-clears? |
| Human voice | ×1 | Sounds like someone who knows the subject? |
| Rhythm & density | ×1 | Varied sentences, nothing cuttable? |

**Revise below 70/100.** **Gate:** if Substance or Specificity scores under 5, fix those first and
rescore — a high surface score cannot buy back empty content. This is the whole point of scoring
substance-first: a metronomic paragraph full of real, specific claims beats a lyrical one that says
nothing.

## How to use

1. Read the draft for **substance** and **specificity** first. Fix thin or swappable content before
   anything else.
2. Pass for **structure**: throat-clearing, binary contrast, false agency, hidden actors.
3. Pass for **surface**: intensifiers, rhythm, density — applying the judgment tests, not bans.
4. For code comments, docstrings, commits, ADRs, or PRs, switch to
   [references/technical.md](references/technical.md).
5. Score with the weighted rubric. If it clears 70 and the substance gate, ship it.

Reference files, loaded as needed:

- [references/phrases.md](references/phrases.md) — word- and phrase-level tells, with keep-when notes.
- [references/structures.md](references/structures.md) — structural patterns, each with "when it's fine."
- [references/technical.md](references/technical.md) — technical writing and what not to strip.
- [references/examples.md](references/examples.md) — before/after transformations, including restraint.

## Credit and license

Reworked from [stop-slop](https://github.com/hardikpandya/stop-slop) by
[Hardik Pandya](https://hvpandya.com), used under the MIT License. This rework is MIT too. See
[LICENSE](LICENSE).
