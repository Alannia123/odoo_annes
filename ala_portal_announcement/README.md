# ala_portal_announcement

Popup announcements on the **website home page** (`/`) and the **portal home page**
(`/my`, `/my/home`) for Odoo 19 Community.

## Install

```bash
cp -r ala_portal_announcement /opt/odoo/custom-addons/
sudo systemctl restart odoo          # required: new routes are registered at boot
# then Apps > Update Apps List > install "Portal & Website Announcement Popup"
```

A **restart** is mandatory, not just `-u`. The routing table is built at boot, so
`/ala/announcement/active` will 404 after a plain module upgrade.

## Publish the Independence Day invitation

Menu **Announcements > Announcements > New**

| Field | Value |
|---|---|
| Internal Reference | Independence Day 2026 invitation |
| Show | Image only |
| Poster | upload the invitation JPEG |
| Show From | 2026-08-10 09:00:00 |
| Show Until | 2026-08-15 12:00:00 |
| Frequency | Once per visitor |
| Website Home Page | ✔ |
| Portal Home Page | ✔ |
| Audience | Everyone |

Save. The popup stops appearing by itself after **Show Until** — no cleanup job,
no manual unpublish.

## How "first time only" works

Each announcement carries a `token` derived from its `write_date`. The browser
stores `ala_ann:<id>:<token>` after the visitor closes the popup.

* **Once per visitor** → `localStorage`, never shown again.
* **Once per browser session** → `sessionStorage`, returns on the next app launch.
* **Once per day** → `localStorage` holding the date.
* **Every page load** → nothing stored.

Editing the record changes `write_date`, therefore the token, therefore the
storage key — so a corrected poster reaches everyone again automatically.

The "Do not show this again" checkbox writes a permanent mark regardless of the
frequency setting. It is hidden when frequency is already *Once per visitor*.

## Audience targeting

* **Everyone** — public visitors and logged-in users.
* **Public visitors only** — anonymous website traffic.
* **Logged-in users only** — anyone with a session (portal or internal).
* **Restrict to Groups** — narrow further, e.g. a *Student Portal* or *Faculty*
  group from your education modules. Public visitors never match a group filter.

## Architecture notes

* The mount point is injected into `web.frontend_layout`, which both the website
  and the portal extend, but `_popup_scope_for_request()` renders it only on the
  two home paths. Language prefixes (`/en/`, `/hi/`) are stripped before matching.
* Content is fetched at runtime from `/ala/announcement/active` rather than
  rendered into the page. Website home pages are cached; the JSON response is
  marked `no-store, private`, so no visitor ever gets someone else's popup.
* The poster is served by `/ala/announcement/<id>/image` under `sudo()`, with a
  404 for archived, expired or not-yet-started records — no public ACL is granted
  on the model itself, and the route never confirms that a hidden record exists.
* The image URL carries `?u=<token>` and is cached for 7 days; replacing the
  image changes the token and busts the cache.
* `_fetch_for_visitor()` lives on the model, not the controller, so the mobile
  REST layer can reuse it as-is for an in-app announcement screen.

## Android WebView

The popup needs DOM storage to remember dismissals:

```java
webView.getSettings().setDomStorageEnabled(true);
```

Without it nothing breaks — the popup simply reappears on every home-page visit.

## Risks / things to watch

* **Datetimes are stored in UTC.** The form shows your user timezone, so set
  *Show Until* as the school's local wall-clock time and let Odoo convert.
* **Large posters.** The `image` field resizes to 1920px max, but a 4 MB upload
  still costs bandwidth on 3G. Aim for ~300 KB.
* **Multiple live announcements** are queued and shown one after another. Use
  *Sequence* to control the order; keep two or three at most.
* **Website page cache / CDN**: only the JSON endpoint is user-specific and it is
  explicitly `no-store`. If you front Odoo with a CDN, exclude
  `/ala/announcement/active` from caching.
