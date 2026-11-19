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
| Decision / rejected alternative / menu behaviour | "Why not the obvious way?" "How does this menu behave?" | `<game>/notes/*.md`, or `core/notes/UI.md` once two games show it | code comment |
| Procedure | "What do I do, in what order?" | `.claude/skills/*/SKILL.md` | notes |
| Event / narrative | "What changed, what did we try, why?" | git commit message | notes, comments |
| Orientation | "Where do I start?" | `.claude/CLAUDE.md`, `<game>/CLAUDE.md`, `core/CLAUDE.md` | anywhere else |

Routing makes deletion safe only because every home is under version control. Claude's memory folder is outside the repo and unversioned, so it holds only how the user wants Claude to work, never project facts.

| tree | remote | visibility |
|---|---|---|
| repo root | `origin` on GitHub | **public**, and staying public |

The repo is public, so everything committed is world-readable. Never commit credentials, account details, absolute paths, or anything else personal. Game templates stay local (see `.gitignore`).

## 4. How rules are earned

Rules arrive only by the promotion rule below, never copied from another project: a borrowed rule has no incident behind it, so it fails §1.

**Promotion rule: a pattern becomes a rule on its second occurrence, not its first.**

- **First** time something goes wrong → the reasoning goes in the commit message. No rule is written yet.
- **Second** time → promote it to a numbered rule, citing both commits, in the home its subject routes to (§2): `core/notes/UI.md`, Rules, for how routines read, tap and wait on the screen; this section, for rules about text. Numbers run across the project and are never reused or renumbered, since notes, code and skills cite them as "Rule N".
- Every rule has a **scope line**: one sentence saying what it does *not* cover.

One incident can't tell a recurring cause from an accident, and a rule written from one instance gets the wrong scope.

**Finding repeats.** Do a promotion pass when the same correction comes up twice, or when a note passes ~200 lines: read `git log` since the last pass and look for a repeated *cause*, not a repeated symptom.

### Rule 4. Write a fact once, in its subject's home; cite it everywhere else

Text goes to the home its subject routes to (§2), not to the file being edited. Before writing a fact (how a menu behaves, a number, a reason, a rule), search for it (`git grep` its key words). Found: cite it ("(common: <section>)", "`core/notes/dailies.md`, Mail", "Rule N") and add only what the citation doesn't say. Not found: write it in its home and cite it from where you are. A skill names the step and cites the reason; it doesn't carry the reason, the numbers or the examples. When fixing a repeat, search for every copy, not only the one in hand. A copy drifts: once one is fixed, the others go stale, and a reader can't tell which is current.

- `c1ba331`, `49be46f`: the skills restated the core notes. The copies drifted (where the mailbox is; whether stamina needs approval, still asked by dailies.md and the task skill after `61a20e7` stopped asking), and the first fix cut the 18/22 GB numbers from new-game only, leaving them in learn-dailies.
- `8fa7a77`, moved in `86af931`: rules about reading the screen were written into doc_policy, because §4 defined how rules are earned and said "below".

**Scope:** this covers facts, reasons and rules. It doesn't cover orientation (a `CLAUDE.md` saying what each file holds), the few words a citation uses to name what it cites, or commit messages, which narrate a change and may quote what moved.
