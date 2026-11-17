# Neural Cloud UI notes

How Neural Cloud menus behave, one section per menu: how to tell a menu's states apart and switch between them, and anything else learned while automating it. Templates live in `nc/templates/` (see the map skill for the scheme). `nc/CLAUDE.md` imports this file, so Claude Code loads it only in sessions that read files under `nc/`.

## start-screen

Title art with GAME START; ~12 s from launch, after one loading screen (`common/loading/`, identified by its "Loading resources..." label, 1.00 on its source; nothing on it answers Back, so `lobby` waits it out). Identified by the "(c) Sunborn Inc. All rights reserved." line (at most 0.21 elsewhere), not the PROJECT.NEURAL.CLOUD line, which the loading screen shows in the same place.

- The copyright line shows a moment before GAME START fades in, so `start_screen` waits for GAME START before tapping.
- GAME START stays ~2.1 s after a tap that took, then the screen dims for ~2.5 s (copyright still matching at 0.95) before the load. So the tap is given 5 s, and retapped only when GAME START is still there. The load to the lobby took 2–10 s.

## Popups (common/popups/)

Shown after GAME START, over the lobby. On the first launch of the day (2026-11-17), in order: notice, login-reward, monthly-signin. Later launches that day showed none.

- **notice**: news board with Event and System tabs; identified by both tab labels (at most 0.36 elsewhere). Closed by the X at the top right (1812, 124), the same art and spot as monthly-signin's X (0.97–1.00), so the X never identifies either.
- **login-reward**: "Login Reward" banner over the monthly-signin calendar, with "Tap on the screen to continue" (at most 0.48 elsewhere); that line is its close. Closing it uncovers monthly-signin.
- **monthly-signin**: the Monthly Sign-in calendar. Its title also shows above login-reward's band (1.00), so it's identified by the title and the "Monthly Pass Rewards" label together, which the band covers (at most 0.22 elsewhere). Its "Refreshes after" timer put the daily reset at 13:00 local time.

## lobby

Identified by the Explore title (1.00 on a fresh lobby; at most 0.41 elsewhere), which is HUD. The HUD stayed up through 25 s idle; the eye button at the left hides it by hand, and nothing in the routines taps it. The OS line at the bottom ("OASIS CLOUD OPERATING SYSTEM...") also matches 1.00 under every popup, so it never decides the lobby.

- **quit**: Android Back on the lobby opens "Are you sure you want to quit the game?" (at most 0.24 elsewhere), closed with CANCEL (1176, 598). CONFIRM quits.
- Android Back closes menus (`BACK_KEY = "back"`: tested from mail).
