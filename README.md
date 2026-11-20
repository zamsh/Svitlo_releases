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
- `gpv-index/`, `roe-index/`, `khoe-index/` — address → sub-queue indexes for Poltava, Rivne and the Kharkiv
  region, which the apps download and search on the device: `index.json` (rows of the operator's
  document and the addresses parsed from them), `meta.json` (source document, its hash and validity),
  `report.json` (validation report of the last build)

The indexes are built elsewhere and committed here; nothing in this repo runs. Until version 1.12.0 the iOS app was also sideloaded
through AltStore from this repository; that channel is closed and its builds are removed (they stay in git
history).
