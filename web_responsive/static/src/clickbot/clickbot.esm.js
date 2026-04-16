/* Copyright 2025 Tecnativa - Carlos Roca
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl). */

// Do nothing on mobile/tablet widths
if (window.innerWidth > 768) {
    const checkCalledFromClickEverywhere = function () {
        const error = new Error();
        const stack = error.stack || "";
        return stack.includes("clickEverywhere");
    };

    const originalQuerySelector = document.querySelector;
    document.querySelector = function (selector) {
        if (checkCalledFromClickEverywhere()) {
            if (selector === ".o-dropdown--menu .o_app") {
                selector = ".o-app-menu-list .o_app";
            } else if (selector === ".o_navbar_apps_menu .dropdown-toggle") {
                selector = ".o_navbar_apps_menu .o_grid_apps_menu__button";
            } else if (
                selector.includes('.o-dropdown--menu .dropdown-item[data-menu-xmlid="')
            ) {
                selector = selector.replace(
                    ".o-dropdown--menu .dropdown-item",
                    ".o-app-menu-list .o_app"
                );
            }
        }
        return originalQuerySelector.call(this, selector);
    };

    const originalQuerySelectorAll = document.querySelectorAll;
    document.querySelectorAll = function (selector) {
        if (checkCalledFromClickEverywhere()) {
            if (selector === ".o-dropdown--menu .o_app") {
                selector = ".o-app-menu-list .o_app";
            }
        }
        return originalQuerySelectorAll.call(this, selector);
    };
}