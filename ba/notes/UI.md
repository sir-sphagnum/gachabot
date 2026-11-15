# Blue Archive UI notes

How Blue Archive menus behave, one section per menu: how to tell a menu's states apart and switch between them, and anything else learned while automating it. Templates live in `ba/templates/` (see the map skill for the scheme). `ba/CLAUDE.md` imports this file, so Claude Code loads it only in sessions that read files under `ba/`.

## start-screen (`ba/templates/start-screen/`)

The title screen: character art, "TOUCH TO START" in a bar at the bottom centre, Notice and Menu buttons bottom left.

- Identified by Notice (`info_start-screen_notice_42-862-116-52.png`) and Menu (`info_start-screen_menu_42-930-110-54.png`): 1.00 on the start screen, at most 0.15 elsewhere. Not by "TOUCH TO START", which pulses.
- Tapping the TOUCH TO START spot (`btn_start-screen_lobby_795-918-330-42.png`, centre (959, 940)) starts the game: 1.00 on its source, at most 0.31 elsewhere. As a match it's unreliable because of the pulse; tap it as a point.
- After the tap, "Now Loading . . ." screens show before the lobby: full-screen art that changes from load to load, with "Now Loading . . ." and a rabbit icon bottom right. `ba/templates/common/loading/info_loading_now-loading_1388-968-292-52.png` is the words without the animated dots, alpha-masked to the pixels that were the same on two loads with different art (42% of the box): 0.96 and 1.00 on those two, no match on any other saved screen. Art not seen yet may need it remasked.
- Launch to start screen took ~20 s on four cold starts; start screen to lobby 8–23 s.
- Automated by `ba/routines/start_screen.py` (`python -m ba.bot start_screen`). It ends on the lobby, or returns False on a popup for the lobby routine to close.
- Each cold start grows BlueStacks' memory by ~4–5 GB (9.2 GB after a restart, 22.8 GB after three launches). At 55 GB, with 0.2 GB left free on the PC, the load after TOUCH TO START stalled into the network-unstable popup and the bot's own capture ran out of memory. Restart BlueStacks before a long session.

## lobby (`ba/templates/start-screen/lobby/`)

The home screen: player level top left, AP, credits and pyroxene top centre, shortcuts on the left (Notice, MomoTalk, Attendance, Tasks, Cash Shop), the bottom bar (Cafe to Recruit) and Campaign bottom right.

- Identified by Campaign (`info_lobby_campaign_1728-996-156-46.png`) alone. It scores 1.00 under both popups below too, because neither covers it, so popups are checked before trusting it (Rule 1).
- Not seen yet: whether the HUD hides when idle, and what Back does here (a quit prompt?). `BACK_KEY` is still the scaffold's Android Back, untested on a menu.
- Automated by `ba/routines/lobby.py` (`python -m ba.bot lobby`). After a load or a popup close it watches 4 s more before counting the lobby as reached, since news shows ~2 s after Campaign. Run from the news popup, it closed news and reached the lobby. On later launches, news closed with no new-products after it.
- Tested after a BlueStacks restart: two cold starts (`start start_screen`, then `lobby`) each ended in the lobby, 37 s and 34 s after launch; and `python -m ba.bot start lobby` alone waited out the launch (the "Now Loading" template also matches the launch loads), handed over at the start screen, closed news and reached the lobby 32 s after launch. Not tested yet: from a menu a few taps deep, and the first launch of a new day with its popups.

## news popup (`ba/templates/common/popups/news/`)

The news panel over the dimmed lobby: a sidebar of icons on the left, banners, and a "Main News" list. Showed on every launch so far (four on one day, not only the first), ~2 s after Campaign: a lobby seen right after the load isn't popup-free yet.

- Identified by "Main News" (`info_news_main-news-title_128-660-140-38.png`): 1.00 on the popup, at most 0.30 elsewhere.
- Closed by the X top right (`btn_news_close_1822-32-64-64.png`, centre (1853, 67)): at most 0.18 elsewhere. Closing it showed new-products.

## new-products popup (`ba/templates/common/popups/new-products/`)

"Notice" / "New products added." with paid packs, Confirm and Shortcut. Showed right after news closed.

- Identified by "New products added." (`info_new-products_message_768-670-384-50.png`): 1.00 on the popup, at most 0.21 elsewhere.
- Closed by the X top right (`btn_new-products_close_1380-120-50-50.png`, centre (1405, 144)): at most 0.22 elsewhere. Never tap Shortcut: it leads to a shop.

## network-unstable popup (`ba/templates/common/popups/network-unstable/`)

"Notice" / "The network connection is unstable. Tap the Confirm button to return to the title screen." with Confirm and Reconnect, over a dimmed loading screen. Seen during the load after TOUCH TO START, while the PC had 0.2 GB of memory free and BlueStacks used 55 GB, so it's likely memory pressure rather than the network. Cut by hand from the error screen, not via `tools.map`.

- Identified by its first line (`info_network-unstable_message_636-430-644-48.png`): 1.00 on the popup, no match on any other saved screen.
- Closed by Confirm (`btn_network-unstable_close_600-708-345-100.png`), which goes back to the start screen, where the routines carry on. Reconnect would retry the load. Not tapped yet. Its image also scores 0.98 on new-products' Confirm, but searched over the whole screen: that button sits outside this box.
- Android Back on the popup also seemed to leave it (black, a load, then the start screen).
