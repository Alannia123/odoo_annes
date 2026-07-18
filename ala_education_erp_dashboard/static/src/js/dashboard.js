/** @odoo-module */

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { user } from "@web/core/user";
import { Component, onWillStart, useState } from "@odoo/owl";

export class EducationalDashboard extends Component {
    static template = "EducationalDashboard";
    static props = { "*": true };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        this.state = useState({
            canViewFaculty: false,
            canViewStudents: false,
            canViewExams: false,
            canViewAmenities: false,
            currentAcademicYearId: false,

            summary: null,        // light data — loaded on page open
            details: null,        // heavy data — loaded on button click
            detailsLoading: false,

            todayLabel: new Date().toLocaleDateString("en-IN", {
                day: "2-digit", month: "short", year: "numeric",
            }),
        });

        onWillStart(async () => {
            const isAdmin =
                (await user.hasGroup("mis_education_core.group_education_principal")) ||
                (await user.hasGroup("mis_education_core.group_education_office_admin"));

            this.state.canViewFaculty = isAdmin;
            this.state.canViewStudents = isAdmin;
            this.state.canViewExams = isAdmin;
            this.state.canViewAmenities = isAdmin;

            // Light data only — 4 count queries, fast page open
            const result = await this.orm.call("erp.dashboard", "erp_data", []);
            this.state.summary = result;
            this.state.currentAcademicYearId = result.current_academic_year_id || false;
        });
    }

    /* ------------------------------------------------------------
       DERIVED VALUES
    ------------------------------------------------------------ */
    get updatePercent() {
        const d = this.state.details;
        if (!d || !d.total_divisions) {
            return 0;
        }
        return Math.round((d.updated_divisions / d.total_divisions) * 100);
    }

    /* ------------------------------------------------------------
       LOAD DETAILS BUTTON → fetch heavy data on demand
    ------------------------------------------------------------ */
    async loadDetails() {
        if (this.state.detailsLoading) {
            return;
        }
        this.state.detailsLoading = true;
        try {
            this.state.details = await this.orm.call(
                "erp.dashboard", "erp_detail_data", []
            );
        } catch (err) {
            console.error("Failed to load dashboard details:", err);
        } finally {
            this.state.detailsLoading = false;
        }
    }

    /* ------------------------------------------------------------
       SUMMARY CARD CLICK
    ------------------------------------------------------------ */
    onDashboardCardClick(actionType) {
        const permissionMap = {
            faculties: this.state.canViewFaculty,
            students: this.state.canViewStudents,
            exams: this.state.canViewExams,
            amenities: this.state.canViewAmenities,
        };

        if (!permissionMap[actionType]) {
            return;
        }

        const currentAcademicYearId = this.state.currentAcademicYearId;

        const actionMap = {
            faculties: {
                name: "Faculties",
                res_model: "education.faculty",
                domain: [],
            },
            students: {
                name: "Students",
                res_model: "education.student",
                domain: [
                    ["tc_issued", "=", false],
                    ["drop_out", "=", false],
                    ["active", "=", true],
                ],
            },
            exams: {
                name: "Exams",
                res_model: "education.exam",
                domain: currentAcademicYearId
                    ? [["academic_year_id", "=", currentAcademicYearId]]
                    : [],
            },
            amenities: {
                name: "Amenities",
                res_model: "education.amenities",
                domain: [],
            },
        };

        const action = actionMap[actionType];
        if (!action) {
            return;
        }

        this.action.doAction({
            type: "ir.actions.act_window",
            name: action.name,
            res_model: action.res_model,
            views: [[false, "list"], [false, "form"]],
            target: "current",
            domain: action.domain || [],
        });
    }

    /* ------------------------------------------------------------
       ROW / CARD CLICK HANDLERS
    ------------------------------------------------------------ */
    openTask(taskId) {
        if (!taskId) {
            return;
        }
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Task",
            res_model: "task.management",
            res_id: Number(taskId),
            views: [[false, "form"]],
            target: "current",
        });
    }

    openValuation(valuationId) {
        if (!valuationId) {
            return;
        }
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Exam Valuation",
            res_model: "education.exam.valuation",
            res_id: Number(valuationId),
            views: [[false, "form"]],
            target: "current",
        });
    }

    openDivisionAttendance(div) {
        // Attendance already exists → open form directly
        if (div.attendance_id) {
            this.action.doAction({
                type: "ir.actions.act_window",
                name: "Attendance",
                res_model: "education.attendance",
                res_id: Number(div.attendance_id),
                views: [[false, "form"]],
                target: "current",
            });
            return;
        }

        // Fallback → open list filtered by division
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Attendance",
            res_model: "education.attendance",
            views: [[false, "list"], [false, "form"]],
            domain: [["division_id", "=", Number(div.division_id)]],
            context: {
                default_division_id: Number(div.division_id),
            },
            target: "current",
        });
    }

    /* ------------------------------------------------------------
       STATE BADGE CLASSES
    ------------------------------------------------------------ */
    taskStateClass(state) {
        if (state === "Completed") {
            return "completed";
        }
        if (state === "Pending") {
            return "pending";
        }
        return "overdue";
    }

    valuationStateClass(state) {
        if (state === "Completed") {
            return "completed";
        }
        if (state === "Draft") {
            return "pending";
        }
        return "cancelled";
    }
}

registry.category("actions").add("ala_erp_dashboard_tag", EducationalDashboard);