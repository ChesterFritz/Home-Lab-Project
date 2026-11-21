# 💸 Money Manager — Self-hosted

The iPhone app **Money Manager** (Realbyte) has a "PC Manager" mode: the phone runs a small web server on port 8888 and you edit your books from a browser. It only works while the app is open and the phone is on the same Wi-Fi.

This folder runs it on the Orange Pi instead, all the time, from a copy of the phone's database. The server is one Python file with no dependencies. It serves two front ends on the same data:

- **Pitaka** at `/`: a new phone-first UI (Svelte), described below.
- **Classic** at `/classic/`: the phone's original ExtJS page, unchanged.

**Open it:** `http://pitaka.local` at home (or `http://192.168.18.28:8888`), or `http://100.81.251.12:8888` over Tailscale.

---

## Pitaka, the new UI

| Screen | What's on it |
|---|---|
| **Overview** | The month as big figures (came in, went out, left over). A flow diagram of where the money went: income sources → the month → spending categories, plus what was left. 12-month chart with money in above the line and money out below (tap a month to open it), spending by category (tap one to see its transactions), net worth over a year, and the latest entries |
| **Transactions** | Grouped by day with daily totals. Search, type filters, account filter. Tap a row to edit or delete it |
| **Accounts** | What you have vs. what you owe, accounts by group, each account's 26-week balance line and recent activity. Add, rename, regroup, set balance, remove |
| **Settings** | Light/dark/auto theme, backup download, restore, CSV export, link to the classic view |

Adding is one sheet for expense, income or transfer. The amount field opens the number pad, and category and account are chips. Press **N** on a keyboard to open it.

Shortcuts for the iPhone home screen:
- `…/#/overview?add=expense` opens the add sheet straight away.
- `…/#/overview?m=2026-08` opens a specific month.

**Design ("glass"):** desktop first, then scaled down for iPad and iPhone.
- Frosted, translucent panels float over a softly drifting colour field. The field's colours follow the time of day (morning, day, evening, night), and light or dark mode follows the device setting.
- **Mac / iPad landscape:** a floating glass sidebar holds Add, the navigation and net worth. **iPad portrait:** the sidebar shrinks to an icon rail. **iPhone:** a floating glass tab bar with a round + Add button.
- The Overview opens with three stat cards: came in, went out and left over. Each compares with the previous month and carries a 12-month sparkline.
- "Where the money went" is a flow diagram on wide screens and a list of bars on narrow ones.
- Type is the Apple system font (SF Pro) on Apple devices, with Inter as the fallback elsewhere; both have ₱ and aligned digits.
- Money in, money out and transfers are blue, orange and green. All three passed the colourblind and contrast checks on both glass surfaces. Every chart has a **Table** button.


**Secret anime style.** Tap the Pitaka logo 7 times in a row (sidebar, or the phone header) to unlock it; 7 more taps seal it away. Once found, a Style switch also appears in Settings → Appearance. It follows light/dark: light is a black-and-white manga page (ink panels, narration-box titles, screentone, focus lines, ドン!/カチャ! sound effects); dark is chuunibyou (obsidian panels with gold sigils, a turning magic circle, embers, glitching Cinzel titles, pages renamed Grimoire/Chronicle/Vaults/Pact, and Piso as the Dark Coin Lord). Stored per device in localStorage (`pitaka-skin`).


**Motion:**
- **Navigation:** pages rise out of a soft blur. The active-tab pill glides between items with a slight spring, and its icon pops.
- **Glass:** on Mac, a light sheen follows the pointer across the glass, and summary cards lift on hover. The **+** icon spins a quarter-turn on hover.
- **Overview:** the stat cards float in once per visit, and their sparklines draw themselves each time the month changes. Lower panels rise into view as you scroll. Figures count to new values.
- **Lists and months:** transaction days cascade in, and account rows slide in. The month name slides in the direction you moved.
- **Add form:** the form springs open. On iPhone you can drag it down to dismiss.
- Reduced-motion settings turn all of this off.

Source is in `web/`. `./deploy.sh` builds it into `app/`, which isn't committed. For local development, run `npm run dev` with `MM_DEV_API=http://<server>:8888`.

### JSON API used by Pitaka

| Call | Returns / does |
|---|---|
| `GET /api/meta` | Currency, category tree, groups, accounts with balances, net worth |
| `GET /api/transactions?from&to[&account]` | Transactions, newest first |
| `GET /api/summary?from&to` | Totals, per-category sums, daily sums |
| `GET /api/trend?end=YYYY-MM&months=12` | Income and expense per month |
| `GET /api/networth?months=12` | Assets, debts and total at each month end |
| `GET /api/account-history?id&weeks=26` | Weekly balance of one account |
| `POST /api/transactions` | Create or update income, expense or transfer (JSON) |
| `DELETE /api/transactions/<id>` | Delete (both legs of a transfer) |
| `POST /api/accounts`, `DELETE /api/accounts/<id>` | Add or edit (balance edits become adjustments), remove |

## How it was built

I reverse-engineered the phone's web app with [REA](https://github.com/morluto/rea):

| Piece | Where it lives | What I found |
|---|---|---|
| Web UI | Realbyte's CDN (`pcmanager/v330`) | ExtJS 3 app, 8 scripts. The phone only serves `index.html` and `initVar.js` |
| API | The phone, under `/moneyBook/*` | 17 endpoints. JSON-ish replies, one XML grid feed, form posts |
| Data | `/moneyBook/money.sqlite` | The app's Core Data SQLite store, downloadable as-is |

`server.py` re-implements every endpoint on top of that SQLite file. I checked it against the phone's real responses. Init data, asset tree, summaries, per-account charts and the transaction feed all match exactly (the transaction feed byte-for-byte). The dashboard's chart totals, pie charts and summary match too. The one dashboard difference is listed under "Differences from the phone".

### Data model notes

| `ZDO_TYPE` | Meaning | Balance |
|:-:|---|:-:|
| 0 / 1 | Income / Expense | + / − |
| 3 / 4 | Transfer out / in. Paired legs share `ZTXUIDTRANS` | − / + |
| 7 / 8 | Balance edit ("Modified Bal." / "Difference") | + / − |

- Dates are Core Data seconds since 2001-01-01, plus a `ZTXDATESTR` day string.
- Deleted rows have `ZISDEL=1`. Live rows have `ZISDEL` NULL.
- New rows advance `Z_PRIMARYKEY.Z_MAX`, so the file can go back to the phone without key collisions.

---

## Install (on the Pi)

Turn on **PC Manager** in the app first, then:

```sh
sudo ./install.sh http://<phone-ip>:8888
```

This downloads the UI files and imports the phone's database. It also installs the `money-manager` systemd service and opens port 8888 in UFW, for the LAN and Tailscale only.

To push updates later, from your computer: `./deploy.sh`. It never touches the database.

### Optional password

```sh
echo 'MM_PASSWORD=choose-something' | sudo tee /etc/money-manager.env
sudo chmod 600 /etc/money-manager.env && sudo systemctl restart money-manager
```

The browser will ask for a login. Any username works with that password.

---

## Keeping the phone and the Pi in sync

There is no live sync. The two copies are independent once imported.

| Direction | How |
|---|---|
| **Phone → Pi** | Pi UI › Settings › *Recovery File Upload*, with a `money.sqlite` downloaded from the phone. Or re-run `python3 /opt/money-manager/server.py --import-from http://<phone-ip>:8888` |
| **Pi → Phone** | Pi UI › Settings › *Recovery File Download*, then upload that file on the phone's own PC Manager page. Then fully close and reopen the app |

Every import or upload first saves the current database as `money.sqlite.bak-<timestamp>` in `/var/lib/money-manager/`.

> Pick one place to make edits at a time. Uploading either copy over the other replaces it completely.

---

## Differences from the phone

- **Excel export** gives a UTF-8 `.csv` (opens in Excel) instead of the phone's file.
- **Dashboard** fills in the real `asset` / `debt` numbers. The phone always sends `0`, and the chart only plots the total anyway.
- **Credit cards:** add, edit and list work. "Unpaid amount" is shown as the card's balance. Statement-cycle math isn't reproduced, and there are no cards in the current data to check it against.
- The locale file the phone's page fails to load (`js/locale/ext-lang-en.js`) is served properly, so there's no "Failed to load locale file" popup.
- Realbyte's tracking iframe is removed.

## Accounts and sign-in

Pitaka asks you to sign in. Anyone who can reach the page can **create an account**, and each account gets its own private book (a separate SQLite file):

| What | Where (on the Pi) |
|---|---|
| Logins and sessions (scrypt-hashed passwords; only a hash of each session cookie is stored) | `/var/lib/money-manager/users.sqlite` |
| The **first** account's book: it took over the existing data | `/var/lib/money-manager/money.sqlite` |
| Every later account's book: a clean start with the default categories | `/var/lib/money-manager/books/u*.sqlite` |

- **Sessions:** last 60 days. Signing out ends the session on that device only. Changing your password (Settings → Account) signs out your other devices.
- **Wrong passwords:** after 5 in a row, sign-in pauses for 30 seconds.
- **Classic interface:** `/classic/` uses the same sign-in and shows the signed-in person's book.
- **Admin commands on the Pi:**
  - `python3 /opt/money-manager/server.py --list-users`
  - `python3 /opt/money-manager/server.py --reset-password NAME` (prints a new random password)

## Address: http://pitaka.local (and pitaka.home)

- **mDNS:** `pitaka.local` is announced on the LAN by Avahi (`pitaka-mdns.service` runs `avahi-publish -a -R pitaka.local 192.168.18.28` as `fritz`; Avahi is limited to `end0`, and UFW allows 5353/udp from the LAN). iPhones, iPads and Macs resolve it without any DNS setup, so this is the address to use.

- **DNS:** AdGuard Home (Docker on the Pi) answers `pitaka.home` and `adguard.home` with the Pi's IP. These entries are under Filters → DNS rewrites.
- **Proxy:** a Caddy container (`caddy`, host network, config in `~/caddy/Caddyfile`) listens on port 80. It sends `pitaka.home` to this server on :8888, and `adguard.home` (or the bare IP) to AdGuard's admin, which now runs on :3000.
- **Direct address:** `http://192.168.18.28:8888` still works.
- **Why pitaka.home is unreliable:** the router hands out `1.1.1.1` as a secondary DNS server, and devices that ask it get no answer for `.home`. Removing that from the router's DHCP settings would fix it; `pitaka.local` sidesteps it.
- **If pitaka.home doesn't load on an iPhone or Mac:** iCloud Private Relay or a custom DNS setting is bypassing AdGuard. Turn Private Relay off for your home Wi-Fi.

## Files

| File | Purpose |
|---|---|
| `server.py` | The whole backend. Env: `MM_PORT`, `MM_DB`, `MM_STATIC`, `MM_PASSWORD` |
| `web/` | Source of the Pitaka UI (Svelte 5, Tailwind 4, Motion, d3). Built into `app/` |
| `index.html`, `print.html` | The phone's pages for the classic view, pointed at local copies of the assets |
| `assets.txt`, `fetch-assets.sh` | List and downloader for the UI files (Realbyte's, so not committed) |
| `money-manager.service`, `install.sh`, `deploy.sh` | Same pattern as Pi Health |
| `sim-data.py` | Fake data for trying the UI. `python3 sim-data.py add` adds a year of entries tagged `[sim]`. `remove` deletes only those. Both back up the database first |
