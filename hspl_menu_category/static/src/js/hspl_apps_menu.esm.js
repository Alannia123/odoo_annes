/** @odoo-module **/

/* eslint-disable no-unused-vars */
/* eslint-disable no-undef */

import {AppsMenu} from "@web_responsive/components/apps_menu/apps_menu.esm";
import {patch} from "@web/core/utils/patch";
const {useEffect} = owl;

patch(AppsMenu.prototype, {
    setup() {
        super.setup();
        useEffect(
            (el) => {
                this.appendAppsCategorywise();
            },
            () => [document.querySelectorAll(".categ_ind")]
        );
    },

    appendAppsCategorywise() {
        const categoryElements = document.querySelectorAll(".categ_ind");
        categoryElements.forEach((ctgInd) => {
            const ctgId = ctgInd.querySelector("input")?.dataset.value;
            if (!ctgId) return;

            const appElements = document.querySelectorAll(".o-app-menu-item");
            appElements.forEach((menuInd) => {
                const menuId = menuInd.querySelector("input")?.dataset.value;
                if (menuId === ctgId) {
                    ctgInd.querySelectorAll(".o-app-menu-list")[0].appendChild(menuInd);
                }
            });
        });
    },
});
