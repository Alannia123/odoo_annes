/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class FeeOverview extends Component {
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.action = useService("action");

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
        });

        onWillStart(async () => {
            await this.loadDivisions();
            await this.loadAcademicYears();
            await this.loadFees();
        });
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
                payment_date: this.state.payment_date,
                payment_mode: this.state.payment_mode,
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