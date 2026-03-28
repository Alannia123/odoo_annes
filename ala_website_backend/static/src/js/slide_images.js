/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ListController } from "@web/views/list/list_controller";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

patch(ListController.prototype, {
    async _onSelectedDocumentslide() {
        const selectedRecords = await this.getSelectedResIds();

        if (!selectedRecords.length) {
            this.dialogService.add(AlertDialog, {
                title: _t("Failed !!"),
                body: _t("Please select record."),
                confirmLabel: _t("Ok"),
            });
            return;
        }

        const input = document.createElement("input");
        input.type = "file";
        input.multiple = true;

        input.addEventListener("change", async (ev) => {
            const files = Array.from(ev.target.files || []);
            if (!files.length) {
                return;
            }

            try {
                const results = [];

                for (const file of files) {
                    const dataurl = await new Promise((resolve, reject) => {
                        const reader = new FileReader();
                        reader.onload = (e) => resolve(e.target.result);
                        reader.onerror = reject;
                        reader.readAsDataURL(file);
                    });

                    const result = await this.env.services.orm.call(
                        "ala.slide.multi.documents",
                        "document_file_slide_upload",
                        [dataurl, file.name, selectedRecords, this.props.resModel],
                        {}
                    );

                    if (result) {
                        results.push(result);
                    }
                }

                if (results.length) {
                    this.dialogService.add(AlertDialog, {
                        title: _t("Succeeded !!"),
                        body: _t("Updated successfully."),
                        confirmLabel: _t("Ok"),
                    });
                } else {
                    this.dialogService.add(AlertDialog, {
                        title: _t("Failed !!"),
                        body: _t("No documents were uploaded."),
                        confirmLabel: _t("Ok"),
                    });
                }

                await this.model.root.load();
                this.render(true);
            } catch (error) {
                console.error("Slide upload error:", error);
                this.dialogService.add(AlertDialog, {
                    title: _t("Failed !!"),
                    body: _t("Something went wrong while uploading documents."),
                    confirmLabel: _t("Ok"),
                });
            }
        });

        input.click();
    },
});