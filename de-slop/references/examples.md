# Before / after examples

The first five are reworked from stop-slop. The last three are new: they show the substance-first
pass, technical de-slopping (with a case where cutting would be *wrong*), and restraint — text that
looks like slop but should be kept.

## 1. Throat-clearing + binary contrast

**Before:**
> "Here's the thing: building products is hard. Not because the technology is complex. Because
> people are complex. Let that sink in."

**After:**
> "Building products is hard. The technology is manageable; the people aren't."

Removed the opener, the telegraphed contrast, and the emphasis crutch. Direct statements.

## 2. Filler + unnecessary reassurance

**Before:**
> "It turns out that most teams struggle with alignment. The uncomfortable truth is that nobody
> wants to admit they're confused. And that's okay."

**After:**
> "Most teams struggle with alignment because no one admits they're confused."

Cut the throat-clearing and the permission-granting ending, and turned two vague sentences into one
with a cause.

## 3. Business jargon stack

**Before:**
> "In today's fast-paced landscape, we need to lean into discomfort and navigate uncertainty with
> clarity. This matters because your competition isn't waiting."

**After:**
> "Move faster. Your competitors already are."

Cut the jargon. The claim survives in six words.

## 4. Dramatic fragmentation

**Before:**
> "Speed. Quality. Cost. You can only pick two. That's it. That's the tradeoff."

**After:**
> "Speed, quality, cost: pick two."

One sentence, no performative fragments. (The original stop-slop's rewrite used an em dash here while
its own rules banned em dashes — a colon avoids both the drama and the contradiction.)

## 5. Rhetorical setup

**Before:**
> "What if I told you that the best teams don't optimize for productivity? Here's what I mean: they
> optimize for learning. Think about it."

**After:**
> "The best teams optimize for learning, not productivity."

Direct claim, no rhetorical scaffolding.

## 6. Substance first (new)

Surface polish alone can't save empty content. This example shows why the substance pass comes first.

**Before (fluent, empty):**
> "Our new architecture fundamentally reimagines how data flows through the system, unlocking
> significant improvements and delivering real value to users at every level of the stack."

**Surface pass only (tighter, still empty):**
> "Our new architecture changes how data flows, improving the system for users."

Cleaner — and it still says nothing. No number, no mechanism, nothing a reader could check or dispute.

**Substance pass (the real fix):**
> "We moved from per-request database reads to a write-through cache. p99 read latency dropped from
> 800ms to 90ms, and the database load fell by half."

Same topic, now with a mechanism (write-through cache) and evidence (two numbers). This is the pass
that matters; do it before you polish.

## 7. Technical: de-slop, but don't over-strip (new)

**Slop-y docstring — before:**
```python
def get(k):
    """This is a helper function that is basically used to get the value for
    a key. It simply looks up the key and returns whatever it finds."""
    ...
```

**After:**
```python
def get(k):
    """Return the cached value for key `k`, or None if the key is cold.

    Does not populate the cache on a miss; call `warm(k)` first if you need
    a value. Raises KeyError only if `k` is unhashable.
    """
    ...
```

Cut the padding ("This is a helper… basically… simply"); kept the contract (return value, the
cold-cache behavior, the raise). Terser *and* more informative.

**Counter-example — a comment a naive de-slopper would wrongly delete:**
```python
# Retry up to 3 times with jitter. The upstream load balancer drops the first
# connection after an idle scale-down (see INFRA-2291), so a bare call fails
# ~1 in 20 at low traffic.
```
This looks like a long, hedge-filled comment. Leave it. It carries the *why* (a documented infra
quirk), an exact reference (INFRA-2291), and a real failure rate. Cutting it to `# retry 3x` deletes
the only reason anyone would keep the retry.

## 8. Restraint: looks like slop, keep it (new)

Not every flagged pattern is a defect. Each of these would survive de-slopping.

- **Meaningful adverb:** "The migration ran *partially* before the pod was killed, leaving 12 of 40
  tables converted." Cut "partially" and you lose the fact that the system is now in a half-migrated
  state. Keep it.
- **Necessary passive:** "The `legacy_id` column was dropped in release 2.7." No one cares *who*
  dropped it; the fact is the release. Forcing an actor ("The platform team dropped…") adds noise.
  Keep the passive.
- **A real three-item list:** "The endpoint validates the token, checks the rate limit, and writes
  the audit log." Three distinct steps, none padding. Don't cut one to satisfy "two beats three."
- **An earned em dash:** "The retry helped — latency dropped, but error rate didn't move." One dash,
  doing real syntactic work. Fine.
