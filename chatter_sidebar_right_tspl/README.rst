Chatter Sidebar Right
=====================

Overview
--------

``chatter_sidebar_right_tspl`` keeps the backend chatter on the right side of
Odoo form views. It is useful when users prefer a consistent sidebar reading
flow instead of having the chatter move under the form when the browser zoom or
viewport changes. In Odoo 19, the behavior is controlled per user with a
preference field on the user form and the "Change My Preferences" dialog.

The module uses a focused compiler-level frontend override so the form renderer
and chatter container keep a stable side layout on medium and larger screens
only when the current user has enabled the option.

Features
--------

- Keeps chatter rendered on the right side on medium and larger backend layouts.
- Adds a per-user boolean preference to enable or disable the layout.
- Passes the preference through session info so the frontend patch stays user-specific.
- Uses a compiler-level layout override instead of relying only on CSS.
- Removes the alternate chatter clone that can move chatter below the form.

How It Works
------------

When Odoo compiles a backend form view with chatter, this module adjusts the
generated form structure before it is rendered:

- the current user's preference is exposed in the web session
- the frontend patch only runs when that preference is enabled
- the form renderer keeps a row layout from medium screens and above
- the main chatter container is always treated as an aside panel
- the secondary in-sheet chatter clone is disabled
- attachment preview is hidden to avoid Odoo switching back to combo chatter layout

Technical Notes
---------------

- Built for Odoo 19 backend form views.
- Depends on ``mail`` and ``web`` only.
- Adds lightweight Python extensions on ``res.users`` and ``ir.http``.
- Implemented through ``web.assets_backend`` plus inherited user preference views.
- The effective logic lives in ``static/src/js/form_compiler_patch.js``.
- Styling is limited to ordering and sizing the form sheet and chatter columns.
- Users can manage the setting from both the full user form and their own
  preferences popup.

Installation
------------

1. Place the module in your custom addons path.
2. Restart the Odoo server.
3. Update the Apps list.
4. Install the module ``Chatter Sidebar Right``.
5. Enable ``Lock Chatter on the Right`` on the target user's preferences.
6. Reload the web client and open a form view with chatter on a large screen.

Usage
-----

1. Open ``Settings > Users`` or ``My Profile > Preferences``.
2. Enable ``Lock Chatter on the Right`` for the required user.
3. Reload the web client.
4. Open any mail-enabled form view in the backend on a medium or larger layout.
5. Confirm that the chatter stays on the right side of the form.

Limitations
-----------

- The module targets backend form chatter only.
- Below medium screen width, the form can still stack vertically.
- Attachment preview inside the form is intentionally disabled to keep chatter
  fixed on the right side.

Version History
---------------

**19.0.1.0.0**

- Initial Odoo 19 release
- Added a per-user chatter lock preference on user settings
- Passed the user preference to the web client session
- Enabled the right-side chatter override only for opted-in users
- Added compiler-level right-side chatter enforcement
- Removed alternate chatter placement paths that caused bottom chatter fallback
