/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { onMounted } from "@odoo/owl";
import { Navbar } from "@web/webclient/navbar/navbar";

patch(Navbar.prototype, {
    setup() {
        super.setup();

        onMounted(() => {
            const isMobile = window.innerWidth <= 767;
            if (!isMobile) {
                return;
            }

            setTimeout(() => {
                // close bootstrap modal if opened
                document.querySelectorAll(".modal.show").forEach((el) => {
                    el.classList.remove("show");
                    el.style.display = "none";
                    el.setAttribute("aria-hidden", "true");
                });

                // close dropdowns / app drawers
                document.querySelectorAll(".show").forEach((el) => {
                    if (
                        el.classList.contains("o_apps_menu") ||
                        el.classList.contains("dropdown-menu") ||
                        el.classList.contains("o-overlay")
                    ) {
                        el.classList.remove("show");
                    }
                });

                // remove modal backdrops
                document.querySelectorAll(".modal-backdrop").forEach((el) => el.remove());

                document.body.classList.remove("modal-open", "overflow-hidden");
            }, 100);
        });
    },
});