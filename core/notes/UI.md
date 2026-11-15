# Common UI notes

Menu behaviour that more than one game shows, and how the bot deals with it. Each game's `notes/UI.md` keeps what is specific to its menus (boxes, scores, which button, thresholds) and cites a section here as "(common: <section>)" instead of explaining it again. Every `<game>/CLAUDE.md` imports this file next to its own notes.

A pattern moves here once a second game shows it: one game alone can't tell a quirk of that game from a general one. How to cut images (`_anywhere`, `_white`, alpha masks) is in the map skill; this file says when a menu needs them. Rules the routines must follow are in `.claude/doc_policy.md` §4 (Rule 1: popups before indicators).

## Dims

A popup or dialog dims the screen but leaves what's underneath matching, often at 0.96–1.00: e7's barrel under the quit dialog, re1999's Crew under quit, ba's Campaign and Cafe titles under their popups. Rule 1 covers what to do. A game's notes record only the score under the dim.

## Shared buttons

Games reuse one button's art across dialogs: e7's "Tap to close" sits on five dialogs and its quit-dialog Cancel/Confirm on three more; ba's Confirm is the same on the cafe's invite and bounty's sweep, and its "Notice" title heads several dialogs. An image cut from one scores ~1.00 on the others. So:

- a shared `btn_` closes or confirms a dialog but never identifies it;
- it's tapped only right after the action that opens its dialog, or while that dialog's own `info_` (its question or a title no other dialog has) shows;
- the same goes for the back arrow and Home at the top of every ba menu.

A dialog's identifier is its unique text: the question line, or a title nothing else shares.

## Lit or grey

Matching ignores brightness, so a lit button and its greyed, claimed or used-up version score alike (0.86–0.98). Tell them apart by colour: the mean of one channel minus another over the button's box, red minus blue for yellow, orange, gold and red, green minus blue for green and blue. The threshold goes halfway between the lit and grey values the game's notes record. A dim pulls the value toward grey, so it's read only with dialogs closed. Each routine has its own `_lit`.

Seen on e7's Cultivate, secret-shop's Buy, arena's Challenge and lost rows, orbis-guide's chest badge and the HUD badge; ba's cafe Claim, Multi-Sweep and bounty's stars.

## Reading a zero

A counter is read as "zero or not" from a crop of its first digit only. Other digits score 0.42–0.84 against the 0 (rounded ones, 6, 8 and 9, come closest), so the routine asks for 0.90–0.95, not the usual 0.85. Counts that were never seen are unknown, so the notes list which were. Over a changing background the digit is matched white-only (`_white`). A bare digit can match a digit on another menu (e7: hunt-team's top bar scores 0.91 on arena's flags 0), so it's read only once the menu is known.

Seen on e7's arena flags and leif cost, ba's lesson and bounty tickets.

## Moving parts

- Text that pulses or has art moving across it is masked to its letters: re1999's START and loading line, ba's "Now Loading" (masked to the pixels two loads with different art shared).
- A pulsing button is tapped as a point rather than found by matching: ba's TOUCH TO START.
- Animated scenes never give two identical captures, so `tools.map` flags them "still changing" and settling is judged by a still element (a title, a list): e7's sanctuary and secret-shop.
- Crops keep the text and leave out what comes and goes: badges, orange dots, counts, sparkles, EVENT and "In Progress" tags, subtitles.

## Toasts

Chat and mission toasts slide over the top of the screen for a few seconds (e7's "entered channel" toast, ba's mission toasts over dialog titles). Identifiers are taken where toasts don't reach.

## Lists that move

Lists scroll on entry or reorder: e7's hunt list scrolls to the chosen card and the daily-shop grid moves bought products to the end; ba's lesson area list and bounty stage list scroll on entry. Entries are found with `_anywhere` images or tapped by position once the list has settled, never while it scrolls.

## Lobbies

- Back on the lobby opens a quit dialog (e7, re1999), so the lobby routine opens it whenever it presses Back once too often. It's closed with Cancel; Confirm quits the game.
- The lobby's HUD hides when idle (e7 after ~9 s, ba within minutes). The idle lobby needs an identifier from the scene (e7's barrel, ba's hanging sign), and the lobby routine wakes it before anything taps the HUD.
- Login-day dialogs (check-in calendars) are lobby states, not common popups, because only the lobby shows them (e7, re1999).

## BlueStacks memory

BlueStacks' memory grows with every capture and every cold start (e7: 9.6 → 22 GB in ~45 min of two processes capturing each second; ba: ~4–5 GB per cold start). Past ~22 GB screencaps came back empty; with 0.2 GB free on the PC, ba's load stalled into its network-unstable popup. `python -m core.device health` says when a restart is due; restart BlueStacks before a long session.
