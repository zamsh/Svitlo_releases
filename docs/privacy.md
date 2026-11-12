# Світло — політика конфіденційності

_Чинна з 12 листопада 2026 року (оновлено: звіти про збої та статистика). Стосується застосунків «Світло» для iOS і Android._

**Коротко:** застосунок не має облікових записів і реклами й не збирає персональних даних. Щоб
знаходити помилки, він надсилає знеособлені звіти про збої та статистику використання (Firebase від
Google). Це можна вимкнути в налаштуваннях. Усе, що ви налаштовуєте, зберігається на вашому пристрої.

## Що зберігається на пристрої

- обраний регіон, підчерга, вигляд діаграми, налаштування сповіщень і віджетів;
- завантажені графіки відключень і довідники адрес (кеш, щоб віджет працював без мережі).

Ці дані не передаються розробнику. Вони зникають, коли ви видаляєте застосунок.

## Які запити робить застосунок

Застосунок сам завантажує графіки з офіційних джерел, без власного сервера посередника:

- **сайт або сервіс обленерго вашого регіону** (наприклад, poe.pl.ua, yasno.ua, dtek-…, loe.lviv.ua);
  запитується тільки джерело обраного регіону;
- **raw.githubusercontent.com**: довідники «адреса → підчерга» для деяких регіонів, які ми
  публікуємо на GitHub;
- **docs.google.com**: публічні таблиці адрес Запоріжжяобленерго (тільки для цього регіону).

Як і будь-який вебсервер, ці сервіси бачать IP-адресу вашого пристрою та час запиту. Їхню обробку даних
регулюють їхні власні політики.

## Пошук підчерги за адресою

Адресу, яку ви вводите, застосунок надсилає в довідник обленерго вашого регіону або шукає в
завантаженому довіднику прямо на пристрої. Адреса не зберігається після пошуку і не надсилається
розробнику.

## Геолокація

Доступ до геолокації запитується тільки тоді, коли ви натискаєте кнопку «Визначити за геопозицією» в пошуку підчерги.
Застосунок отримує одну позицію й перетворює її на адресу системним сервісом: Apple на iOS або
Geocoder від Google на Android. Координати не зберігаються і не передаються розробнику. Фоновий
доступ до геолокації застосунок не використовує.

## Сповіщення

Нагадування «через 10 хвилин відключення» та «змінився графік» плануються локально на пристрої.
Push-сервери не використовуються.

## Відгуки

Якщо ви натискаєте «Написати відгук», відкривається ваша поштова програма з листом. До листа
додаються версія застосунку, модель пристрою, версія системи, регіон і підчерга, щоб було легше
розібратися з проблемою. Ви бачите цей текст і можете змінити його до надсилання. Листи
використовуються тільки для відповіді вам і покращення застосунку.

## Звіти про збої та статистика

Застосунок використовує Firebase Crashlytics і Google Analytics for Firebase (Google LLC):

- **звіти про збої та помилки:** стан застосунку в момент збою, модель пристрою, версія системи й
  застосунку, обраний регіон і підчерга, а також помилки завантаження графіка (наприклад, «сайт
  обленерго не відповідає»);
- **статистика використання:** які функції відкривали (зміна регіону чи підчерги, вигляд діаграми,
  пошук підчерги — лише чи знайдено результат, сповіщення), версія системи й застосунку, приблизна
  країна за IP-адресою.

Ми **не надсилаємо** адрес, координат, введеного тексту, рекламного ідентифікатора (IDFA / AAID) чи
ідентифікатора постачальника (IDFV). Дані не пов'язані з вашою особою, не продаються й не
використовуються для реклами чи відстеження. Firebase зберігає звіти про збої до 90 днів, а
статистику — до 2 місяців.

Вимкнути все це можна в застосунку: **Налаштування → Про застосунок → Анонімна статистика**.

## Діти

Застосунок не призначений спеціально для дітей і свідомо не збирає їхніх даних.

## Зв'язок із джерелами даних

«Світло» — незалежний застосунок. Він не пов'язаний з обленерго, ДТЕК, YASNO чи органами влади й не
представляє їх. Графіки беруться з публічних сайтів операторів. Офіційне джерело — сайт вашого
обленерго.

## Зміни і контакти

Про зміни цієї політики ми повідомлятимемо оновленням цієї сторінки. Питання надсилайте на
[svitlo.app@icloud.com](mailto:svitlo.app@icloud.com).

---

# Svitlo — Privacy Policy

_Effective 12 November 2026. Applies to the Svitlo apps for iOS and Android._

**In short:** the app has no accounts or ads and collects no personal data. To find bugs it sends
anonymous crash reports and usage statistics (Google's Firebase), which you can turn off in Settings.
Everything you set up stays on your device.

**Stored on the device:** your region, sub-queue, chart style, notification and widget settings, and
downloaded schedules and address directories (a cache, so the widget works offline). It is never sent to
the developer and is removed when you delete the app.

**Network requests.** The app downloads schedules straight from official sources, with no server of
ours in between:
- the grid operator of your selected region (only that region's source);
- raw.githubusercontent.com, for the address → sub-queue directories we publish on GitHub;
- docs.google.com, for Zaporizhzhiaoblenergo's public address sheets (that region only).

Like any web server, these services see your device's IP address and the time of the request. Their own
policies govern what they do with it.

**Address lookup.** An address you type is sent to your region's operator directory or searched in a
downloaded directory on the device. It is not kept after the search and is never sent to the developer.

**Location** is requested only when you tap "Визначити за геопозицією" (find by location) in the sub-queue finder. The app takes a single
fix and turns it into an address with the system service (Apple on iOS, Google's Geocoder on Android).
Coordinates are not stored or sent to the developer. The app never uses background location.

**Notifications** ("power off in 10 minutes", "schedule changed") are scheduled locally on the device. No
push servers are involved.

**Feedback.** "Send feedback" opens your mail app with a draft that includes the app version, device
model, OS version, region and sub-queue. You can see and edit all of it before sending. Emails are used
only to reply to you and improve the app.

**Crash reports and statistics.** The app uses Firebase Crashlytics and Google Analytics for Firebase
(Google LLC). Crash and error reports contain the app state at the crash, device model, OS and app
version, the selected region and sub-queue, and schedule download errors. Usage statistics record
which features were used (region or sub-queue change, chart style, sub-queue finder with only whether
something was found, notifications), OS and app version and the approximate country from the IP
address. We never send addresses, coordinates, typed text, the advertising ID (IDFA / AAID) or IDFV.
The data is not linked to you, not sold and not used for ads or tracking. Firebase keeps crash reports
for up to 90 days and statistics for up to 2 months. Turn it off in **Settings → Про застосунок →
Анонімна статистика**.

**Children.** The app is not directed at children and does not knowingly collect their data.

**Data sources.** Svitlo is independent. It is not affiliated with, endorsed by or representing any grid
operator, DTEK, YASNO or government body. Schedules are taken from the operators' public websites. Your
operator's website is the official source.

**Changes and contact.** Changes to this policy will be published on this page. Questions:
[svitlo.app@icloud.com](mailto:svitlo.app@icloud.com).
