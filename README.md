# Svitlo — iOS builds for AltStore / SideStore

A widget and app with the **Poltavaoblenergo** hourly power-outage schedule: whether the power is on
now, when it goes off or comes back, and the whole day on one chart. Tapping the widget reloads the
schedule from poe.pl.ua. Requires iOS 17+. The app UI is in Ukrainian.

This repository only holds ready-made builds (`ipa/`) and the AltStore source. Source code is private.

## Installing with AltStore

1. Install **AltStore** once following https://altstore.io (needs a Mac or Windows PC with AltServer
   and your Apple ID — a free one works). Or use **SideStore** (https://sidestore.io), which refreshes
   the signature without a computer.
2. In AltStore: **Browse → Sources → +** and paste:
   ```
   https://raw.githubusercontent.com/zamsh/Svitlo_releases/main/altstore-source.json
   ```
3. Find "Світло" and tap **Free / Install**.
4. Open the app — it walks you through choosing your sub-queue and adding the widget.

**Updates** show up in the **Updates** tab — tap **Update**.
**Signing** with a free Apple ID lasts 7 days; AltStore renews it automatically when the computer with
AltServer is on the same Wi-Fi at least once a week (SideStore does it without a computer).

Without the source: download an `.ipa` from [`ipa/`](ipa) and open it in AltStore / SideStore / Sideloadly.

## Contents

- `altstore-source.json` — AltStore / SideStore source (updated automatically on every release)
- `ipa/` — unsigned builds (last 5); AltStore signs them with your Apple ID
- `icon.png` — app icon
- `gpv-index/` — Poltava address → sub-queue index for the apps (rebuilt daily from Poltavaoblenergo's PDF)
- `roe-index/` — Rivne address → sub-queue index (rebuilt daily from Rivneoblenergo's two PDFs)
