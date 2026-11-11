# Documentation policy

What earns a code comment, a note, or a git commit; the test that decides whether text may be deleted; and how this project's own lessons become rules. Read before adding to any long-lived file.

**Why:** Adding text is cheap. Deleting it safely is expensive, because you first have to rebuild the reasoning that justified it. So text only grows. This policy keeps every piece of reasoning in one known place, so the rest can be cut.

**How to apply:** Adding text → route it by genre (§2), then check it passes the delete test (§1). Something went wrong → §4 decides whether it is a rule yet. Section numbers are stable identifiers: never renumber. Missing numbers (§3, §5 onward) are reserved for sections added once they are needed.

## 1. The delete test

> **Does this text let a future reader safely delete or change the thing it describes, using something they could not recover from the code, the templates, or `git log`?**

**Yes** → keep it; it carries reasoning.
**No** → it restates the code, or it is session narrative, which belongs in the commit message.

Don't soften prose just to shorten it. Text that reads like commentary but carries no reason is worse than none: it sits where a reader looks for the reason. Cut it down to the reason, or cut all of it.

## 2. Genre routing: one home each

| Genre | Question it answers | Home | Never in |
|---|---|---|---|
| Invariant / constraint | "What breaks if I change this?" | code comment | notes |
| Decision / rejected alternative / menu behaviour | "Why not the obvious way?" "How does this menu behave?" | `<game>/notes/*.md` | code comment |
| Event / narrative | "What changed, what did we try, why?" | git commit message | notes, comments |
| Orientation | "Where do I start?" | `.claude/CLAUDE.md`, `<game>/CLAUDE.md` | anywhere else |

Routing makes deletion safe only because every home is under version control. Claude's memory folder is outside the repo and unversioned, so it holds only how the user wants Claude to work, never project facts.

| tree | remote | visibility |
|---|---|---|
| repo root | `origin` on GitHub | **public**, and staying public |

The repo is public, so everything committed is world-readable. Never commit credentials, account details, absolute paths, or anything else personal. Game templates stay local (see `.gitignore`).

## 4. Rules earned here

*Empty on purpose.* Rules arrive only by the promotion rule below, never copied from another project: a borrowed rule has no incident behind it, so it fails §1.

**Promotion rule: a pattern becomes a rule on its second occurrence, not its first.**

- **First** time something goes wrong → the reasoning goes in the commit message. Nothing is added here.
- **Second** time → promote it to a numbered rule below, citing both commits.
- Every rule has a **scope line**: one sentence saying what it does *not* cover.

One incident can't tell a recurring cause from an accident, and a rule written from one instance gets the wrong scope.

**Finding repeats.** Do a promotion pass when the same correction comes up twice, or when a note passes ~200 lines: read `git log` since the last pass and look for a repeated *cause*, not a repeated symptom.

### Rule 1. Check for popups before trusting a state indicator

A popup or dialog that dims the screen leaves what's underneath matching, so an indicator showing is not proof the game is in that state. Before acting on an indicator match, check that none of the game's known popups, nor any dialog the current menu can have open, is open, and close any that is before looking again.

- `891ce78`: the quit dialog dims the lobby; the wall barrel still matched (0.96), so the routine took it for the lobby and tapped the candle, which did nothing.
- `8c73f0c`: the barrel matched through "Disconnected from server"; the routine handed over to `tap_until`, which closed the popup and kept tapping the main-menu spot on the start screen it led to.

**Scope:** this covers matches that decide what state the game is in. It doesn't cover a popup's or dialog's own `info_` images, or a wait whose result a popup-checking loop looks at again before acting.
