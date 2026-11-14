# Черга — public files

«Черга: графік відключень» shows the hourly power-outage schedule of your sub-queue for 17 Ukrainian grid
operators: home screen widgets, notifications before outages, several places, and the sub-queue found by
address. iOS 17+ and Android; the app UI is in Ukrainian. Source code is private.

- **iOS:** App Store (app id 6834474632; 1.12.0 submitted for review on 2026-11-14), TestFlight for testers.
- **Android:** Google Play closed testing — join at https://play.google.com/apps/testing/io.github.zamsh.svitlo
  (or the [testing page](https://zamsh.github.io/Svitlo_releases/join-testing.html)).

This repository holds what the apps and the store listings link to:

- `docs/` — served by GitHub Pages at https://zamsh.github.io/Svitlo_releases/: the
  [privacy policy](https://zamsh.github.io/Svitlo_releases/privacy), the
  [support page](https://zamsh.github.io/Svitlo_releases/support) and the Android testing page
- `gpv-index/` — Poltava address → sub-queue index the apps search on the device (rebuilt daily from
  Poltavaoblenergo's PDF)
- `roe-index/` — Rivne address → sub-queue index (rebuilt daily from Rivneoblenergo's two PDFs)
- `khoe-index/` — Kharkiv region address → sub-queue index (rebuilt daily from Kharkivoblenergo's
  "Адреси та черги" PDF)

The indexes are rebuilt by the workflows in `.github/workflows` on a self-hosted runner in Ukraine (label
`svitlo-ua`; poe.pl.ua drops connections from abroad). Until version 1.12.0 the iOS app was also sideloaded
through AltStore from this repository; that channel is closed and its builds are removed (they stay in git
history).
