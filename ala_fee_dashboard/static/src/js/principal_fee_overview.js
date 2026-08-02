/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart } from "@odoo/owl";

const PRESETS = [
    { key: "today", label: "Today" },
    { key: "yesterday", label: "Yesterday" },
    { key: "week", label: "This Week" },
    { key: "month", label: "This Month" },
    { key: "range", label: "Custom" },
];

export class PrincipalFeeOverview extends Component {
    static template = "ala_fee_dashboard.PrincipalFeeOverview";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.presets = PRESETS;

        const today = this._iso(new Date());
        this.state = useState({
            preset: "today",
            viewType: "summary",
            dateFrom: today,
            dateTo: today,
            paymentMode: "",
            divisionId: "",
            meta: {
                divisions: [],
                payment_modes: [],
                currency_symbol: "\u20B9",
                company_name: "",
            },
            lines: [],
            summaryRows: [],
            modeColumns: [],
            totals: {},
            loading: false,
        });

        this._money = new Intl.NumberFormat("en-IN", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
        this._short = new Intl.NumberFormat("en-IN", {
            maximumFractionDigits: 0,
        });

        onWillStart(async () => {
            this.state.meta = await this.orm.call(
                "ala.student.fee.line", "get_principal_overview_filters", []
            );
            this.applyPreset("today", false);
            await this.fetchData();
        });
    }

    // ---------------------------------------------------------------
    // Dates
    // ---------------------------------------------------------------
    _iso(date) {
        const mm = String(date.getMonth() + 1).padStart(2, "0");
        const dd = String(date.getDate()).padStart(2, "0");
        return `${date.getFullYear()}-${mm}-${dd}`;
    }

    applyPreset(preset, refetch = true) {
        this.state.preset = preset;
        const now = new Date();

        if (preset === "today") {
            this.state.dateFrom = this.state.dateTo = this._iso(now);
        } else if (preset === "yesterday") {
            const y = new Date(now);
            y.setDate(y.getDate() - 1);
            this.state.dateFrom = this.state.dateTo = this._iso(y);
        } else if (preset === "week") {
            // Week starts Monday; getDay() is 0 on Sunday.
            const start = new Date(now);
            const offset = (start.getDay() + 6) % 7;
            start.setDate(start.getDate() - offset);
            this.state.dateFrom = this._iso(start);
            this.state.dateTo = this._iso(now);
        } else if (preset === "month") {
            this.state.dateFrom = this._iso(
                new Date(now.getFullYear(), now.getMonth(), 1));
            this.state.dateTo = this._iso(now);
        }

        if (refetch && preset !== "range") {
            this.fetchData();
        }
    }

    onDateInput() {
        this.state.preset = "range";
    }

    setViewType(viewType) {
        if (this.state.viewType === viewType) {
            return;
        }
        this.state.viewType = viewType;
        this.fetchData();
    }

    get hasData() {
        return this.state.viewType === "summary"
            ? this.state.summaryRows.length > 0
            : this.state.lines.length > 0;
    }

    get rangeLabel() {
        if (this.state.dateFrom === this.state.dateTo) {
            return this.formatDate(this.state.dateFrom);
        }
        return `${this.formatDate(this.state.dateFrom)} \u2013 ${this.formatDate(this.state.dateTo)}`;
    }

    // ---------------------------------------------------------------
    // Data
    // ---------------------------------------------------------------
    async fetchData() {
        if (this.state.dateFrom && this.state.dateTo
            && this.state.dateFrom > this.state.dateTo) {
            this.notification.add("From date is after the To date.", {
                type: "warning",
            });
            return;
        }

        this.state.loading = true;
        try {
            const args = [
                this.state.dateFrom || false,
                this.state.dateTo || false,
                this.state.paymentMode || false,
                this.state.divisionId ? parseInt(this.state.divisionId) : false,
            ];
            const method = this.state.viewType === "summary"
                ? "get_principal_fee_summary"
                : "get_principal_fee_overview";
            const result = await this.orm.call(
                "ala.student.fee.line", method, args);

            this.state.modeColumns = result.mode_columns || [];
            this.state.totals = result.totals || {};
            if (this.state.viewType === "summary") {
                this.state.summaryRows = result.rows || [];
                this.state.lines = [];
            } else {
                this.state.lines = result.lines || [];
                this.state.summaryRows = [];
                if (result.totals && result.totals.truncated) {
                    this.notification.add(
                        "Showing the first 1000 receipts. Narrow the date range for the full list.",
                        { type: "warning" });
                }
            }
        } catch (error) {
            this.notification.add("Could not load the fee overview.", {
                type: "danger",
            });
            throw error;
        } finally {
            this.state.loading = false;
        }
    }

    onApply() {
        this.fetchData();
    }

    onReset() {
        this.state.paymentMode = "";
        this.state.divisionId = "";
        this.applyPreset("today");
    }

    // ---------------------------------------------------------------
    // Formatting
    // ---------------------------------------------------------------
    money(value) {
        return `${this.state.meta.currency_symbol}${this._money.format(value || 0)}`;
    }

    moneyShort(value) {
        const n = value || 0;
        if (Math.abs(n) >= 10000000) {
            return `${this.state.meta.currency_symbol}${(n / 10000000).toFixed(2)} Cr`;
        }
        if (Math.abs(n) >= 100000) {
            return `${this.state.meta.currency_symbol}${(n / 100000).toFixed(2)} L`;
        }
        return `${this.state.meta.currency_symbol}${this._short.format(n)}`;
    }

    formatDate(iso) {
        if (!iso) {
            return "";
        }
        const [y, m, d] = iso.split("-");
        return `${d}/${m}/${y}`;
    }

    dayName(iso) {
        if (!iso) {
            return "";
        }
        const [y, m, d] = iso.split("-").map(Number);
        return new Date(y, m - 1, d).toLocaleDateString("en-IN", {
            weekday: "short",
        });
    }

    /** Width of the inline bar in the summary grid, as a percentage. */
    barWidth(amount) {
        const rows = this.state.summaryRows;
        if (!rows.length) {
            return 0;
        }
        const peak = Math.max(...rows.map((r) => r.total));
        if (!peak) {
            return 0;
        }
        return Math.max(2, Math.round((amount / peak) * 100));
    }

    modeAmount(row, key) {
        return (row.modes && row.modes[key]) || 0;
    }

    // ---------------------------------------------------------------
    // Export
    // ---------------------------------------------------------------
    _warnIfEmpty() {
        if (!this.hasData) {
            this.notification.add("Nothing to export for the selected period.", {
                type: "warning",
            });
            return true;
        }
        return false;
    }

    onExportExcel() {
        if (this._warnIfEmpty()) {
            return;
        }
        const query = new URLSearchParams({
            date_from: this.state.dateFrom || "",
            date_to: this.state.dateTo || "",
            payment_mode: this.state.paymentMode || "",
            division_id: this.state.divisionId || "",
            view_type: this.state.viewType,
        }).toString();
        window.location.href =
            `/ala_fee_dashboard/principal_fee_overview/xlsx?${query}`;
    }

    async onExportPdf() {
        if (this._warnIfEmpty()) {
            return;
        }
        await this.action.doAction({
            type: "ir.actions.report",
            report_type: "qweb-pdf",
            report_name: "ala_fee_dashboard.report_principal_fee_overview",
            report_file: "ala_fee_dashboard.report_principal_fee_overview",
            // No active_ids: the report re-runs the same domain server-side,
            // so screen and PDF can never drift apart.
            data: {
                date_from: this.state.dateFrom,
                date_to: this.state.dateTo,
                payment_mode: this.state.paymentMode,
                division_id: this.state.divisionId,
                view_type: this.state.viewType,
            },
        });
    }
}

registry.category("actions").add(
    "ala_fee_dashboard.principal_fee_overview", PrincipalFeeOverview);
