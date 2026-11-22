# Project Neural Cloud UI notes

How Project Neural Cloud menus behave, one section per menu: how to tell a menu's states apart and switch between them, and anything else learned while automating it. Templates live in `nc/templates/` (see the map skill for the scheme). `nc/CLAUDE.md` imports this file, so Claude Code loads it only in sessions that read files under `nc/`. Patterns Project Neural Cloud shares with other games are in `core/notes/UI.md`, cited here as "(common: <section>)".

Android Back closes menus (`BACK_KEY = "back"`); on the lobby it opens quit.

## Launch

Launch → launch load → `start-screen` → Connecting → System Self-Check load → lobby → login popups. On 2026-11-22: the start screen ~10 s after launch; the lobby ~4 s after the START tap; the announcement ~1 s after the lobby.

- **Launch load** (`common/loading/launch/`): sector art and lore that change between launches, over a progress bar. Identified by its status line "Loading resources... //" bottom left (90, 1000), not found on the start screen. The status reads "Initiating... //" for the first seconds, which nothing matches: the lobby spec's `launch` wait covers it. "PROJECT.NEURAL.CLOUD" and the version bottom left/right show on the start screen too.
- **System Self-Check** (`common/loading/self-check/`): a white checklist screen for ~2 s after START. Its "Prof.<number>" row is the account's ID (personal: never in a crop). Identified by "System Self-Check" (92, 880), at most 0.32 elsewhere. It shows the start screen's copyright line (0.94), so it must stay mapped: the lobby loop checks loads before the start screen.

## start-screen

Character art, GAME START (672, 862, 576×62), settings and account buttons top right. Identified by the copyright line "© Sunborn Inc. All rights reserved." (790, 1036, 340×36), at most 0.14 elsewhere apart from the self-check load. The art shows ~1 s before GAME START fades in, and the screen then stays as it is (no animation, nothing changed over 60 s). After a tap that took, "Connecting..." shows over it with GAME START still up for 1–2 s.

## lobby

Identified by the Explore tile's title (1316, 286, 214×72, at most 0.28 elsewhere) and the Achievement tile's label (1304, 780, 160×40, at most 0.41). The HUD stayed up for 1.5 min idle; the eye button (84, 786) hides it by hand only, so nothing needs waking. The secretary's speech line (140, 500) and a toast at the top left ("FACTORY Energizers Maxed at the Factory", common: Toasts) come and go. The top left shows the account's name and UID: never in a crop.

- **Keys** are the stamina (`core/notes/dailies.md`, Stamina sink): the big number on the Explore tile (1416, 500) over "Key /220". 220/220 on 2026-11-22.
- **quit** (state): Back on the lobby opens Android's "Attention / Are you sure you want to quit the game?" (568, 502, 432×38, at most 0.12 elsewhere). Closed by CANCEL (1174, 598); CONFIRM quits. Explore still matches under its dim.
- **Login popups** (first launch of the day, common: First of the day or week): announcement, then login-reward over monthly-signin (Popups, below).
- Reached by `nc/routines/lobby.py`, a `core.lobby` spec. On 2026-11-22: a cold start in 24 s (one START tap, no popups left that day), from the start screen in 10 s, from the quit dialog, from mail, and from Explore's Main Storyline map (not mapped: saved as unknown, one Back). Owed: the next day's first launch, where the spec must close announcement, login-reward and monthly-signin.

## mail

The envelope at the top right of the lobby (1698, 34, 72×54); it matches under every popup's dim (1.00), so it's tapped only once the lobby is known. Identified by "Only displays starred mails" (62, 134, 334×40), at most 0.34 elsewhere. Back top left. Empty on 2026-11-22 ("No New Mail", 0/500), so its Claim All and what an empty claim answers aren't seen yet.

## Popups

All in `common/popups/`, all first launch of the day.

- **announcement:** Event / System tabs over a news list. Identified by both tab labels (186, 132 and 686, 132), at most 0.28 elsewhere; closed by the X (1812, 122). The X is the same art as monthly-signin's (0.97).
- **login-reward:** "Login Reward" band with the day's item, over monthly-signin, opened by the announcement's close. Tap anywhere (common: Tap anywhere): title (834, 284) is both its `info_` and close, at most 0.35 elsewhere. Its "Tap on the screen to continue" fades in late and is left out (Rule 5).
- **monthly-signin:** the month's 30-day calendar, the day claimed on open. Identified by its "Monthly Sign-in" title (1534, 138), which matches under login-reward's dim (1.00), so the spec checks it last; closed by the X (1812, 122).
