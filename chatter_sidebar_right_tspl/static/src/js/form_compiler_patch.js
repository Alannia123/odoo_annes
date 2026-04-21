import { SIZES } from "@web/core/ui/ui_service";
import { patch } from "@web/core/utils/patch";
import { setAttributes } from "@web/core/utils/xml";
import { session } from "@web/session";
import { FormCompiler } from "@web/views/form/form_compiler";

const isChatterSidebarRightEnabled = () => Boolean(session.tspl_chatter_sidebar_right_enabled);

patch(FormCompiler.prototype, {
    compileForm(node, params) {
        const form = super.compileForm(...arguments);
        if (!isChatterSidebarRightEnabled()) {
            return form;
        }

        form.classList.add("o_tspl_chatter_right_layout");
        if (form.classList.contains("o_form_nosheet")) {
            return form;
        }

        form.setAttribute(
            "t-attf-class",
            `{{__comp__.props.record.isInEdition ? 'o_form_editable' : 'o_form_readonly'}} d-flex d-print-block {{ __comp__.uiService.size < ${SIZES.MD} ? "flex-column" : "flex-nowrap h-100" }} {{ __comp__.props.record.dirty ? 'o_form_dirty' : !__comp__.props.record.isNew ? 'o_form_saved' : '' }}`
        );
        return form;
    },

    compile(node, params) {
        const res = super.compile(...arguments);
        if (!isChatterSidebarRightEnabled()) {
            return res;
        }

        const chatterContainer = res.querySelector(
            ".o-mail-Form-chatter:not(.o-isInFormSheetBg), .o-mail-ChatterContainer:not(.o-isInFormSheetBg)"
        );
        if (!chatterContainer) {
            return res;
        }

        const chatterComponent = chatterContainer.querySelector(
            "t[t-component='__comp__.mailComponents.Chatter']"
        );
        if (chatterComponent) {
            setAttributes(chatterComponent, {
                isInFormSheetBg: "false",
                isChatterAside: "true",
            });
        }

        // Force a single visible aside chatter container instead of letting
        // Odoo switch between side, combo, and bottom chatter variants.
        setAttributes(chatterContainer, {
            "t-if": "!__comp__.env.inDialog",
            "t-attf-class": "o-aside w-print-100",
        });

        for (const secondaryChatter of res.querySelectorAll(".o-isInFormSheetBg.o-mail-Form-chatter, .o-isInFormSheetBg.o-mail-ChatterContainer")) {
            setAttributes(secondaryChatter, {
                "t-if": "false",
            });
        }

        const attachmentPreview = res.querySelector(".o_attachment_preview");
        if (attachmentPreview) {
            setAttributes(attachmentPreview, {
                "t-if": "false",
            });
        }

        return res;
    },
});
