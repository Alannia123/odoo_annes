/** @odoo-module **/

function closeMobileAppsPopup() {
    if (window.innerWidth > 768) {
        return;
    }

    setTimeout(() => {
        // close bootstrap / dialog / dropdown opened by default
        document.querySelectorAll(".modal.show, .dropdown-menu.show, .o-dropdown--menu.show").forEach((el) => {
            el.classList.remove("show");
            el.style.display = "none";
            el.setAttribute("aria-hidden", "true");
        });

        // remove backdrops
        document.querySelectorAll(".modal-backdrop").forEach((el) => el.remove());

        // cleanup body state
        document.body.classList.remove("modal-open", "overflow-hidden");
        document.body.style.removeProperty("padding-right");
    }, 200);
}

window.addEventListener("load", closeMobileAppsPopup);
document.addEventListener("DOMContentLoaded", closeMobileAppsPopup);