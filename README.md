# Світло — iOS-збірки для AltStore / SideStore

Віджет і застосунок з графіком відключень **Полтаваобленерго**: чи є світло зараз,
коли вимкнуть/увімкнуть, діаграма доби. Торкання віджета оновлює графік з poe.pl.ua.

Тут лише готові збірки (`ipa/`) і source для AltStore. Потрібен iOS 17+.

## Встановлення через AltStore

1. Один раз встановіть **AltStore** за інструкцією https://altstore.io (знадобиться Mac або Windows з AltServer
   і ваш Apple ID — безкоштовний підходить). Або **SideStore** (https://sidestore.io) — він оновлює підпис без комп'ютера.
2. В AltStore: **Browse → Sources → +** і вставте адресу:
   ```
   https://raw.githubusercontent.com/zamsh/Svitlo_releases/main/altstore-source.json
   ```
3. Знайдіть «Світло» і натисніть **Free / Install**.
4. Додайте віджет: утримання на головному екрані → **+** → «Світло», потім «Редагувати віджет» → оберіть свою підчергу.

**Оновлення:** коли виходить нова версія, вона з'являється у вкладці **Updates** — натисніть **Update**.
**Підпис** безкоштовного Apple ID діє 7 днів; AltStore продовжує його сам, якщо комп'ютер з AltServer
хоча б раз на тиждень у тій самій Wi-Fi мережі (SideStore — без комп'ютера).

Можна й без source: завантажте `.ipa` з папки [`ipa/`](ipa) і відкрийте його в AltStore / SideStore / Sideloadly.

## Зміст

- `altstore-source.json` — source для AltStore / SideStore (оновлюється автоматично при кожному релізі)
- `ipa/` — неподписані збірки (останні 5); AltStore підписує їх вашим Apple ID
- `icon.png` — іконка
