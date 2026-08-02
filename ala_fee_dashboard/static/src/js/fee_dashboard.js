/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { download } from "@web/core/network/download";
import { Component, useState, onWillStart } from "@odoo/owl";

const EMPTY_FILTERS = () => ({
    search: "",
    roll_no: "",
    division_id: "",
    academic_year_id: "",
    payment_status: "",
    payment_mode: "",
    date_from: "",
    date_to: "",
});

export class FeeDashboard extends Component {
    static template = "ala_fee_dashboard.Dashboard";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");

        this.state = useState({
            loading: true,
            filters: EMPTY_FILTERS(),
            meta: {
                divisions: [],
                academic_years: [],
                payment_statuses: [],
                payment_modes: [],
                months: [],
                buckets: [],
                currency_symbol: "\u20B9",
                company_name: "",
            },
            students: [],
            kpi: {
                students: 0, payable: 0, paid: 0, balance: 0, overdue: 0,
                admission_paid: 0, admission_unpaid: 0,
            },
        });

        this._searchTimer = null;
        this._moneyFmt = new Intl.NumberFormat("en-IN", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
        this._shortFmt = new Intl.NumberFormat("en-IN", {
            maximumFractionDigits: 0,
        });

        onWillStart(async () => {
            this.state.meta = await this.orm.call(
                "ala.student.fee.line", "get_dashboard_filters", []
            );
            await this.loadData();
        });
    }

    // ------------------------------------------------------------------
    // Data
    // ------------------------------------------------------------------
    cleanFilters() {
        const f = {};
        for (const [k, v] of Object.entries(this.state.filters)) {
            if (v !== "" && v !== null && v !== undefined) {
                f[k] = v;
            }
        }
        return f;
    }

    async loadData() {
        this.state.loading = true;
        try {
            const payload = await this.orm.call(
                "ala.student.fee.line", "get_dashboard_data", [this.cleanFilters()]
            );
            this.state.students = payload.students || [];
            this.state.kpi = payload.kpi || this.state.kpi;
        } catch (e) {
            this.notification.add(e.message || "Failed to load fee data", {
                type: "danger",
            });
        } finally {
            this.state.loading = false;
        }
    }

    // ------------------------------------------------------------------
    // Filters
    // ------------------------------------------------------------------
    onDebouncedInput(field, ev) {
        this.state.filters[field] = ev.target.value;
        clearTimeout(this._searchTimer);
        this._searchTimer = setTimeout(() => this.loadData(), 450);
    }

    onFilterChange(field, ev) {
        this.state.filters[field] = ev.target.value;
        this.loadData();
    }

    resetFilters() {
        this.state.filters = EMPTY_FILTERS();
        this.loadData();
    }

    // ------------------------------------------------------------------
    // Exports
    // ------------------------------------------------------------------
    async exportXlsx() {
        try {
            await download({
                url: "/ala_fee_dashboard/export_xlsx",
                data: { filters: JSON.stringify(this.cleanFilters()) },
            });
        } catch (e) {
            this.notification.add(e.message || "Excel export failed", {
                type: "danger",
            });
        }
    }

    exportPdf() {
        this.action.doAction({
            type: "ir.actions.report",
            report_type: "qweb-pdf",
            report_name: "ala_fee_dashboard.report_fee_dashboard",
            report_file: "ala_fee_dashboard.report_fee_dashboard",
            name: "Fee Collection Dashboard",
            data: { filters: this.cleanFilters() },
        });
    }

    // ------------------------------------------------------------------
    // Template helpers (OWL templates cannot call JS globals)
    // ------------------------------------------------------------------
    money(value) {
        return this.state.meta.currency_symbol + this._moneyFmt.format(value || 0);
    }

    shortMoney(value) {
        if (!value) {
            return "\u2013";
        }
        return this.state.meta.currency_symbol + this._shortFmt.format(value);
    }

    cellClass(cell) {
        if (!cell || !cell.has) {
            return "mfd-c-none";
        }
        return {
            paid: "mfd-c-paid",
            unpaid: "mfd-c-unpaid",
            over_due: "mfd-c-overdue",
            upcoming: "mfd-c-upcoming",
        }[cell.status] || "mfd-c-upcoming";
    }

    cellLabel(cell) {
        if (!cell || !cell.has) {
            return "\u2013";
        }
        return cell.status_label || "\u2013";
    }

    cellTip(cell, label) {
        if (!cell || !cell.has) {
            return label + ": no fee line";
        }
        const parts = [label, cell.status_label, this.money(cell.amount)];
        if (cell.date) {
            parts.push("Paid on " + cell.date);
        } else if (cell.due) {
            parts.push("Due " + cell.due);
        }
        if (cell.mode_label && cell.status === "paid") {
            parts.push(cell.mode_label);
        }
        return parts.filter(Boolean).join(" \u2022 ");
    }
}

registry.category("actions").add("ala_fee_dashboard.dashboard", FeeDashboard);
