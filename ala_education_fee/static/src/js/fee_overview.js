/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

export class FeeOverview extends Component {
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.action = useService("action");
        this.dialog = useService("dialog");

        this.state = useState({
            search: "",
            roll_no: null,
            division_id: null,
            academic_year_id: null,
            academic_years: [],
            fees: [],
            divisions: [],
            selected_fee_ids: [],
            loading: false,
            payment_date: new Date().toISOString().split("T")[0],
            payment_mode: "cash",
            // per student values
            payment_dates: {},
            payment_modes: {},
        });

        onWillStart(async () => {
            await this.loadDivisions();
            await this.loadAcademicYears();
            await this.loadFees();
        });
    }

        resetFeePayment(ev) {
        const feeId = parseInt(ev.currentTarget.dataset.fee);
        if (!feeId) {
            return;
        }

        this.dialog.add(ConfirmationDialog, {
            title: "Reset Payment",
            body: "This cancels the related invoice and its payment, and moves the fee "
                + "back to unpaid. Monthly fees sharing the same invoice will also be reset. "
                + "This cannot be undone. Continue?",
            confirmLabel: "Reset",
            cancelLabel: "Keep as Paid",
            confirm: async () => {
                const result = await this.orm.call(
                    "ala.student.fee.line",
                    "reset_payment_to_draft",
                    [[feeId]]
                );

                let msg = `${result.reset_count} fee line(s) reset.`;
                if (result.invoices && result.invoices.length) {
                    msg += ` Invoice cancelled: ${result.invoices.join(", ")}.`;
                }
                if (result.skipped_payments) {
                    msg += ` ${result.skipped_payments} payment(s) left untouched `
                         + `(they also settle other invoices).`;
                }

                this.notification.add(msg, {
                    type: result.skipped_payments ? "warning" : "success",
                });

                this.state.selected_fee_ids = this.state.selected_fee_ids.filter(
                    (id) => id !== feeId
                );
                await this.loadFees();
            },
            cancel: () => {},
        });
    }

    onPaymentModeChange(ev) {
        const studentId = parseInt(ev.target.dataset.student);
        this.state.payment_modes[studentId] = ev.target.value;
    }

    onPaymentDateChange(ev) {
        const studentId = parseInt(ev.target.dataset.student);
        this.state.payment_dates[studentId] = ev.target.value;
    }

    openStudentFees(ev) {
        const recordId = parseInt(ev.currentTarget.dataset.id);

        if (!recordId) {
            return;
        }

        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "ala.student.fees",
            res_id: recordId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    async loadDivisions() {
        this.state.divisions = await this.orm.searchRead(
            "ala.education.class.division",
            [],
            ["name"]
        );
    }

    async loadAcademicYears() {
        this.state.academic_years = await this.orm.searchRead(
            "ala.education.academic.year",
            [],
            ["name"]
        );
    }

    async loadFees() {
        this.state.loading = true;
        try {
            this.state.fees = await this.orm.call(
                "ala.student.fee.line",
                "get_fee_lines",
                [],
                {
                    search: this.state.search,
                    roll_no: this.state.roll_no,
                    division_id: this.state.division_id,
                    academic_year_id: this.state.academic_year_id,
                }
            );
        } finally {
            this.state.loading = false;
        }
    }

    async onSearch(ev) {
        this.state.search = ev.target.value;
        await this.loadFees();
    }

    async onDivisionChange(ev) {
        this.state.division_id = ev.target.value ? parseInt(ev.target.value) : null;
        await this.loadFees();
    }

    async onYearChange(ev) {
        this.state.academic_year_id = ev.target.value ? parseInt(ev.target.value) : null;
        await this.loadFees();
    }

    async onRollSearch(ev) {
        const value = ev.target.value.trim();

        if (!value) {
            this.state.roll_no = null;
            await this.loadFees();
            return;
        }

        if (!this.state.division_id) {
            this.notification.add(
                "Please select division before searching by Roll No.",
                { type: "warning" }
            );
            ev.target.value = "";
            return;
        }

        this.state.roll_no = parseInt(value);
        await this.loadFees();
    }

    /**
     * Fees a cashier is allowed to tick. A settled line is never selectable —
     * it must go through resetFeePayment() first.
     *
     * To make "Select All" skip future months as well, add
     *   && f.payment_status !== "upcoming"
     * to the filter below. Everything else keeps working unchanged.
     */
    getSelectableFees(student) {
        return (student.fees || []).filter((f) => f.payment_status !== "paid");
    }

    getSelectableCount(student) {
        return this.getSelectableFees(student).length;
    }

    isAllSelected(student) {
        const selectable = this.getSelectableFees(student);
        return (
            selectable.length > 0 &&
            selectable.every((f) => this.state.selected_fee_ids.includes(f.id))
        );
    }

    /**
     * Per-student Select All / Clear. Scoped to one student on purpose:
     * action_pay_selected_fees() builds one invoice per student, so a
     * cross-student selection could never be paid in a single click anyway.
     */
    toggleSelectAll(ev) {
        const studentId = parseInt(ev.currentTarget.dataset.student);
        const student = this.state.fees.find((s) => s.id === studentId);

        if (!student) {
            return;
        }

        const selectable = this.getSelectableFees(student);

        if (!selectable.length) {
            this.notification.add("No pending fees to select for this student.", {
                type: "warning",
            });
            return;
        }

        const ids = selectable.map((f) => f.id);

        if (this.isAllSelected(student)) {
            this.state.selected_fee_ids = this.state.selected_fee_ids.filter(
                (id) => !ids.includes(id)
            );
        } else {
            // Set() keeps other students' selections intact and prevents
            // duplicate ids from partial manual ticking.
            this.state.selected_fee_ids = [
                ...new Set([...this.state.selected_fee_ids, ...ids]),
            ];
        }
    }

    toggleFee(ev) {
        const feeId = parseInt(ev.target.dataset.id);

        if (!feeId) {
            return;
        }

        if (ev.target.checked) {
            if (!this.state.selected_fee_ids.includes(feeId)) {
                this.state.selected_fee_ids.push(feeId);
            }
        } else {
            this.state.selected_fee_ids = this.state.selected_fee_ids.filter(
                (id) => id !== feeId
            );
        }
    }

    getSelectedTotal(student) {
        let total = 0;
        const fees = student.fees || [];

        for (const fee of fees) {
            if (this.state.selected_fee_ids.includes(fee.id)) {
                total += fee.amount || 0;
            }
        }
        return total;
    }

    getSelectedFine(student) {
        let total = 0;
        const fees = student.fees || [];

        for (const fee of fees) {
            if (this.state.selected_fee_ids.includes(fee.id)) {
                total += fee.fine_amount || 0;
            }
        }
        return total;
    }

    getSelectedConTotal(student) {
        let total = 0;
        const fees = student.fees || [];

        for (const fee of fees) {
            if (this.state.selected_fee_ids.includes(fee.id)) {
                total += fee.concession_amount || 0;
            }
        }
        return total;
    }

    viewStudentBill(ev) {
        const feeId = parseInt(ev.currentTarget.dataset.fee);

        if (!feeId) {
            this.notification.add("No bill found.", { type: "warning" });
            return;
        }

        const url = `/report/pdf/ala_education_fee.report_ala_fee_invoices/${feeId}`;
        window.open(url, "_blank");
    }

    async payStudentFees(ev) {
        const studentId = parseInt(ev.currentTarget.dataset.student);
        const student = this.state.fees.find((s) => s.id === studentId);

        if (!student) {
            return;
        }

        const studentFees = student.fees || [];
        const selectedFees = studentFees
            .filter((f) => this.state.selected_fee_ids.includes(f.id))
            .map((f) => f.id);

        if (!selectedFees.length) {
            this.notification.add("Please select at least one fee to pay.", {
                type: "warning",
            });
            return;
        }

        const result = await this.orm.call(
            "ala.student.fee.line",
            "action_pay_selected_fees",
            [selectedFees],
            {
                payment_date: this.state.payment_dates[studentId] || this.state.payment_date,
                payment_mode: this.state.payment_modes[studentId] || this.state.payment_mode,
            }
        );

        if (result && result.report_name && result.res_id) {
            const url = `/report/pdf/${result.report_name}/${result.res_id}`;
            window.open(url, "_blank");
        }

        this.notification.add("Selected fees processed successfully.", {
            type: "success",
        });

        this.state.selected_fee_ids = this.state.selected_fee_ids.filter(
            (id) => !selectedFees.includes(id)
        );

        await this.loadFees();
    }
}

FeeOverview.template = "ala_education_fee.FeeOverview";
registry.category("actions").add("erp_fee_overview_tag", FeeOverview);