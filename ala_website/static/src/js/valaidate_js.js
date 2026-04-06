/** @odoo-module **/

document.addEventListener("DOMContentLoaded", () => {
    const numericIds = ["exact_age", "mobile_whats", "alternate_phone", "aahar_no"];

    const allowOnlyDigits = (evt) => {
        const code = evt.which || evt.keyCode;
        if (code > 31 && (code < 48 || code > 57)) {
            evt.preventDefault();
        }
    };

    numericIds.forEach((id) => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener("keypress", allowOnlyDigits);
        }
    });
});
