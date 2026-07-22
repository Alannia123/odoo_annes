/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadBundle } from "@web/core/assets";
import {
    Component,
    useState,
    useRef,
    useEffect,
    onWillStart,
    onWillUnmount,
} from "@odoo/owl";

const { DateTime } = luxon;

const STATUS_META = {
    present: { label: "Present", color: "#0F766E" },
    leave: { label: "Leave", color: "#DC2626" },
    on_duty: { label: "On Duty", color: "#F59E0B" },
    med_leave: { label: "Med Leave", color: "#64748B" },
};
const LEAVE_STATUSES = ["leave", "med_leave"];

export class FacultyAttendanceDashboard extends Component {
    static template = "ala_faculty_attendance_daily.Dashboard";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        const ctx = (this.props.action && this.props.action.context) || {};
        this.state = useState({
            period: ctx.mfa_employee_id ? "month" : "day",
            tab: ctx.mfa_employee_id ? "employee" : "overview",
            refDate: DateTime.local().toISODate(),
            loading: true,
            search: "",
            data: null,
            employeeId: ctx.mfa_employee_id || false,
            employeeName: ctx.mfa_employee_name || "",
        });
        this.chartRef = useRef("chart");
        this.chart = null;

        onWillStart(async () => {
            await loadBundle("web.chartjs_lib");
            await this.loadData();
        });
        useEffect(
            () => this.renderChart(),
            () => [this.state.data, this.state.tab, this.state.loading]
        );
        onWillUnmount(() => this.chart && this.chart.destroy());
    }

    // ------------------------------------------------------------------
    // Data
    // ------------------------------------------------------------------
    async loadData() {
        this.state.loading = true;
        this.state.data = await this.orm.call(
            "ala.faculty.attendance.sheet",
            "get_dashboard_data",
            [],
            {
                period: this.state.period,
                ref_date: this.state.refDate,
                employee_id: this.state.employeeId || null,
            }
        );
        this.state.loading = false;
    }

    clearEmployeeFocus() {
        this.state.employeeId = false;
        this.state.employeeName = "";
        this.loadData();
    }

    setPeriod(period) {
        if (this.state.period === period) {
            return;
        }
        this.state.period = period;
        this.loadData();
    }

    setTab(tab) {
        this.state.tab = tab;
    }

    shift(direction) {
        const d = DateTime.fromISO(this.state.refDate);
        const delta =
            this.state.period === "day"
                ? { days: direction }
                : this.state.period === "week"
                ? { weeks: direction }
                : { months: direction };
        this.state.refDate = d.plus(delta).toISODate();
        this.loadData();
    }

    goToday() {
        this.state.refDate = DateTime.local().toISODate();
        this.loadData();
    }

    // ------------------------------------------------------------------
    // Getters
    // ------------------------------------------------------------------
    get statusMeta() {
        return STATUS_META;
    }

    get announcements() {
        return (this.state.data && this.state.data.announcements) || [];
    }

    get tickerDuration() {
        const chars = this.announcements.reduce(
            (n, a) => n + (a.name || "").length + (a.message || "").length + 8,
            0
        );
        return Math.min(Math.max(Math.round(chars / 18), 15), 120);
    }

    get filteredEmployees() {
        const data = this.state.data;
        if (!data) {
            return [];
        }
        const query = this.state.search.trim().toLowerCase();
        if (!query) {
            return data.employees;
        }
        return data.employees.filter(
            (e) =>
                e.name.toLowerCase().includes(query) ||
                String(e.roll).includes(query)
        );
    }

    get absentList() {
        const data = this.state.data;
        if (!data) {
            return [];
        }
        if (data.period === "day") {
            return data.employees.filter((e) =>
                LEAVE_STATUSES.includes(e.day_status));
        }
        return [...data.employees]
            .map((e) => ({ ...e, leaves: e.leave + e.med_leave }))
            .filter((e) => e.leaves > 0)
            .sort((a, b) => b.leaves - a.leaves)
            .slice(0, 8);
    }

    statusBadgeClass(status) {
        return `mfa_badge mfa_badge_${status || "none"}`;
    }

    statusLabel(status) {
        return status ? STATUS_META[status].label : "Not Marked";
    }

    openSheet() {
        const info = this.state.data && this.state.data.sheet_info;
        if (!info || !info.id) {
            return;
        }
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "ala.faculty.attendance.sheet",
            res_id: info.id,
            views: [[false, "form"]],
            target: "current",
        });
    }

    // ------------------------------------------------------------------
    // Chart
    // ------------------------------------------------------------------
    renderChart() {
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
        const el = this.chartRef.el;
        const data = this.state.data;
        if (!el || !data || this.state.loading || this.state.tab !== "overview") {
            return;
        }
        const statuses = Object.keys(STATUS_META);
        let config;
        if (data.period === "day") {
            config = {
                type: "doughnut",
                data: {
                    labels: statuses.map((s) => STATUS_META[s].label),
                    datasets: [
                        {
                            data: statuses.map((s) => data.kpi[s]),
                            backgroundColor: statuses.map(
                                (s) => STATUS_META[s].color
                            ),
                            borderWidth: 2,
                            borderColor: "#ffffff",
                        },
                    ],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: "62%",
                    plugins: {
                        legend: { position: "bottom" },
                    },
                },
            };
        } else {
            config = {
                type: "bar",
                data: {
                    labels: data.trend.labels,
                    datasets: statuses.map((s) => ({
                        label: STATUS_META[s].label,
                        data: data.trend[s],
                        backgroundColor: STATUS_META[s].color,
                        borderRadius: 4,
                        maxBarThickness: 26,
                    })),
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { stacked: true, grid: { display: false } },
                        y: {
                            stacked: true,
                            ticks: { precision: 0 },
                            grid: { color: "rgba(15, 118, 110, 0.08)" },
                        },
                    },
                    plugins: {
                        legend: { position: "bottom" },
                    },
                },
            };
        }
        this.chart = new Chart(el, config);
    }
}

registry
    .category("actions")
    .add("ala_faculty_attendance_dashboard", FacultyAttendanceDashboard);
