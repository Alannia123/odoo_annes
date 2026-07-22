/** @odoo-module */

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart } from "@odoo/owl";

const { DateTime } = luxon;

export class EducationalDashboard extends Component {
    static template = "EducationalDashboard";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            loading: true,
            allowed: false,
            data: null,
            teacherSearch: "",
            facultySelf: null,
            announcements: [],
            tasks: { loading: false, loaded: false, rows: [] },
            valuations: { loading: false, loaded: false, rows: [] },
        });
        this.todayLabel = DateTime.local().toFormat("cccc, dd LLL yyyy");

        onWillStart(async () => {
            const result = await this.orm.call("ala.erp.dashboard", "erp_data", []);
            this.state.allowed = Boolean(result.allowed);
            this.state.data = result.allowed ? result : null;
            this.state.facultySelf = result.faculty_self || null;
            this.state.announcements = result.announcements || [];
            this.state.loading = false;
        });
    }

    // ------------------------------------------------------------------
    // Getters
    // ------------------------------------------------------------------
    get tickerDuration() {
        // ~18 chars/second reading speed, clamped so short and very
        // long announcement sets both stay comfortable.
        const chars = this.state.announcements.reduce(
            (n, a) => n + (a.name || "").length + (a.message || "").length + 8,
            0
        );
        return Math.min(Math.max(Math.round(chars / 18), 15), 120);
    }

    get divisionRatio() {
        const att = this.state.data && this.state.data.attendance;
        if (!att || !att.total_divisions) {
            return 0;
        }
        return Math.round((att.updated_divisions / att.total_divisions) * 100);
    }

    get filteredTeachers() {
        const block = this.state.data && this.state.data.faculty_attendance;
        if (!block) {
            return [];
        }
        const query = this.state.teacherSearch.trim().toLowerCase();
        if (!query) {
            return block.teachers;
        }
        return block.teachers.filter(
            (t) =>
                t.name.toLowerCase().includes(query) ||
                String(t.roll).includes(query)
        );
    }

    myStatusChipClass(status) {
        const map = {
            present: "edb_chip_teal",
            leave: "edb_chip_red",
            on_duty: "edb_chip_amber",
            med_leave: "edb_chip_muted",
        };
        return "edb_chip edb_chip_big " + (map[status] || "edb_chip_muted");
    }

    divisionStatusLabel(status) {
        return { updated: "Updated", not_updated: "Not Updated",
                 not_created: "Not Created" }[status] || status;
    }

    // ------------------------------------------------------------------
    // On-demand loads (Tasks / Exam Valuations only)
    // ------------------------------------------------------------------
    async loadTasks() {
        this.state.tasks.loading = true;
        try {
            this.state.tasks.rows = await this.orm.call(
                "ala.erp.dashboard", "erp_task_data", []);
            this.state.tasks.loaded = true;
        } finally {
            this.state.tasks.loading = false;
        }
    }

    async loadValuations() {
        this.state.valuations.loading = true;
        try {
            this.state.valuations.rows = await this.orm.call(
                "ala.erp.dashboard", "erp_valuation_data", []);
            this.state.valuations.loaded = true;
        } finally {
            this.state.valuations.loading = false;
        }
    }

    // ------------------------------------------------------------------
    // Faculty attendance actions
    // ------------------------------------------------------------------
    async openFacultyAttendanceEntry() {
        const action = await this.orm.call(
            "ala.erp.dashboard", "action_open_today_faculty_sheet", []);
        if (action) {
            this.action.doAction(action);
        }
    }

    openFacultyAttendanceDashboard() {
        this.action.doAction({
            type: "ir.actions.client",
            tag: "ala_faculty_attendance_dashboard",
            name: "Faculty Attendance Dashboard",
        });
    }

    openTeacher(teacher) {
        this.action.doAction({
            type: "ir.actions.client",
            tag: "ala_faculty_attendance_dashboard",
            name: `${teacher.name} — Attendance`,
            context: {
                mfa_employee_id: teacher.id,
                mfa_employee_name: teacher.name,
            },
        });
    }

    // ------------------------------------------------------------------
    // Record navigation
    // ------------------------------------------------------------------
    openCard(kind) {
        const yearId = this.state.data
            ? this.state.data.current_academic_year_id : false;
        const map = {
            faculties: { name: "Faculties", res_model: "ala.education.faculty",
                         domain: [] },
            students: {
                name: "Students", res_model: "ala.education.student",
                domain: [["tc_issued", "=", false], ["drop_out", "=", false],
                         ["active", "=", true]],
            },
            exams: {
                name: "Exams", res_model: "ala.education.exam",
                domain: yearId ? [["academic_year_id", "=", yearId]] : [],
            },
        };
        const cfg = map[kind];
        if (!cfg) {
            return;
        }
        this.action.doAction({
            type: "ir.actions.act_window",
            name: cfg.name,
            res_model: cfg.res_model,
            views: [[false, "list"], [false, "form"]],
            domain: cfg.domain,
            target: "current",
        });
    }

    openDivision(div) {
        if (div.attendance_id) {
            this.action.doAction({
                type: "ir.actions.act_window",
                name: "Attendance",
                res_model: "ala.education.attendance",
                res_id: div.attendance_id,
                views: [[false, "form"]],
                target: "current",
            });
            return;
        }
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Attendance",
            res_model: "ala.education.attendance",
            views: [[false, "list"], [false, "form"]],
            domain: [["division_id", "=", div.division_id]],
            context: { default_division_id: div.division_id },
            target: "current",
        });
    }

    openTask(task) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Task",
            res_model: "ala.task.management",
            res_id: task.id,
            views: [[false, "form"]],
            target: "current",
        });
    }

    openValuation(valuation) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Exam Valuation",
            res_model: "ala.education.exam.valuation",
            res_id: valuation.id,
            views: [[false, "form"]],
            target: "current",
        });
    }
}

registry.category("actions").add("ala_erp_dashboard_tag", EducationalDashboard);
