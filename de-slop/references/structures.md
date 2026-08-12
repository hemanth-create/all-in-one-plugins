# Structures: sentence- and paragraph-level tells

Reworked from stop-slop's `structures.md`. Same high-value patterns, now with a **When it's fine**
note on each — because most of these structures have a legitimate form, and blanket bans produce
stilted writing.

## Binary contrasts

A telegraphed reversal that manufactures drama. Usually you can state the second half and drop the
negation.

| Pattern | Problem |
|---------|---------|
| "Not because X. Because Y." | Telegraphed reversal |
| "[X] isn't the problem. [Y] is." | Formulaic reframe |
| "The answer isn't X. It's Y." | Predictable pivot |
| "It feels like X. It's actually Y." | Setup/reveal cliché |
| "Not X. But Y." / "not X, it's Y" | Mechanical contrast |
| "stops being X and starts being Y" | False transformation arc |
| "not just X but also Y" | Additive hedge |

**Instead:** state Y directly. "The problem is Y." Drop the negation.

**When it's fine:** you are correcting a belief the reader actively holds and would otherwise act on.
"This isn't a memory leak; it's fragmentation" earns the contrast because it redirects a real
misdiagnosis. The tell is the reflexive, content-free version — contrast for rhythm, not correction.

## Negative listing

Listing what something is *not* before revealing what it *is*. A rhetorical striptease.

| Pattern | Problem |
|---------|---------|
| "Not a X… Not a Y… A Z." | Buildup through negation |
| "It wasn't X. It wasn't Y. It was Z." | Same, past tense |

**Instead:** state Z. The reader doesn't need the runway.

**When it's fine:** ruling out plausible-but-wrong options the reader is weighing is real content,
not striptease — common and correct in debugging notes and ADRs ("Not the DB, not the cache — it's
the connection pool"). See [technical.md](technical.md).

## Dramatic fragmentation

Sentence fragments deployed for emphasis, reading as manufactured profundity.

| Pattern | Problem |
|---------|---------|
| "[Noun]. That's it. That's the [thing]." | Performative simplicity |
| "X. And Y. And Z." | Staccato drama |
| "This unlocks something. [Word]." | Artificial revelation |

**Instead:** complete sentences. Trust the content over the presentation.

**When it's fine:** one deliberate fragment for genuine emphasis, used rarely, is a normal tool. The
tell is *stacking* them so every beat lands like a drumroll.

## Rhetorical setups

These announce insight instead of delivering it.

| Pattern | Problem |
|---------|---------|
| "What if [reframe]?" | Socratic posturing |
| "Here's what I mean:" | Redundant preview |
| "Think about it:" | Condescending prompt |
| "And that's okay." | Unnecessary permission |

**Instead:** make the point and let the reader draw the conclusion.

## False agency

Giving inanimate things human verbs. Complaints don't "become" fixes. Bets don't "live or die."
Decisions don't "emerge." A person acts to make those things happen. This pattern reads smooth
because it dodges naming the actor.

| Pattern | Problem |
|---------|---------|
| "a complaint becomes a fix" | The complaint did nothing. Someone fixed it. |
| "a bet lives or dies in days" | Someone kills the project or ships it. |
| "the decision emerges" | Someone decides. |
| "the culture shifts" | People change behavior. |
| "the data tells us" | Someone reads it and draws a conclusion. |
| "the market rewards" | Buyers pay for things. |

**Instead:** name the human. "The team shipped the fix that week" beats "the complaint becomes a
fix." If no specific person fits, use "you" to seat the reader.

**When it's fine:** the subject genuinely is the agent, or it's settled technical idiom — "the
scheduler preempts the task," "the compiler infers the type," "the GC reclaims the object." These
name a real actor (the system) doing a real thing.

## Narrator-from-a-distance

Floating above the scene instead of putting the reader in it.

| Pattern | Problem |
|---------|---------|
| "Nobody designed this." | Disembodied observation |
| "This happens because…" | Lecturer voice |
| "People tend to…" | Armchair sociologist |

**Instead:** put the reader in the room. "You don't sit down one day and decide to…" beats "Nobody
designed this."

## Passive voice — a judgment call

Passive becomes slop when it hides an actor the reader needs. It's correct when the object is the
topic and the actor is unknown, irrelevant, or obvious.

| Passive | Fix, or keep? |
|---------|---------------|
| "Mistakes were made." | Name who made them. |
| "It is believed that…" | Name who believes it. |
| "The decision was reached." | Name who decided. |
| "The endpoint was deprecated in v3." | **Keep** — the actor is irrelevant; the fact is the version. |
| "Users are notified by email." | **Keep** — the system is obvious; the object is the point. |

**The test:** does naming the actor add information? If yes, go active. If not, the passive stays.
This matters most in technical writing — see [technical.md](technical.md).

## Sentence starters — a crutch, not a crime

Wh- openers ("What makes this hard is…", "Why this matters is…") become a crutch when every other
sentence uses one to defer the subject. The fix is to lead with the subject or the specific thing:
"What makes this hard is the lock ordering" → "The lock ordering is the hard part." Not a ban — an
occasional Wh- opener is fine; a *habit* of them is the tell. Same for paragraphs that all open with
"So" or sentences that open with "Look,".

## Rhythm and the "two beats three" heuristic

Monotony is the real tell: three sentences of identical length, every paragraph ending on a
punchline, a metronomic beat.

| Pattern | Fix |
|---------|-----|
| Manufactured triads ("X. And Y. And Z.") | Cut the padding item; keep real threes. |
| Every paragraph ends punchily | Vary the endings. |
| Questions answered in the same breath | Let one breathe, or cut it. |
| Stacked short fragments | Rejoin into full sentences. |

**"Two beats three" is a rhythm nudge, not arithmetic.** If you genuinely have three items, list
three. If the third repeats the first two to sound authoritative, cut it. Reshape rhythm; don't
amputate content to hit a number.

## Em dashes — count them

The tell is *mechanical overuse*: an em dash in nearly every paragraph, or a dash faking a dramatic
pause where a colon or period belongs. A single em dash doing real syntactic work — a sharp
parenthetical or appositive, like this one — is fine. Count them across the piece; if they cluster,
thin them out. Don't outlaw the mark.

## Lazy extremes

| Pattern | Problem |
|---------|---------|
| "every", "always", "never", "everyone", "nobody" | False authority through sweep |

Usually a sign of thin substance: the sweeping claim replaces the specific one. Swap in the actual
scope ("in every test we ran", "none of the three vendors"). **Keep when** the absolute is literally
true and the precision matters ("this function never allocates").
