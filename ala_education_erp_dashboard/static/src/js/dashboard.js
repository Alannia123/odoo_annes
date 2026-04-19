/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { user } from "@web/core/user";
import { Component, onMounted, onWillStart, useState } from "@odoo/owl";

export class EducationalDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.user = user;

        this.companyId = this.user.context.allowed_company_ids
            ? this.user.context.allowed_company_ids[0]
            : false;

        this.state = useState({
            canViewFaculty: false,
            canViewStudents: false,
            canViewExams: false,
            canViewAmenities: false,
            currentAcademicYearId: false,
        });

        onWillStart(async () => {
            const isPrincipal = await this.user.hasGroup("ala_education_core.group_education_principal");
            const isOfficeAdmin = await this.user.hasGroup("ala_education_core.group_education_office_admin");
            const isAdmin = isPrincipal || isOfficeAdmin;

            this.state.canViewFaculty = isAdmin;
            this.state.canViewStudents = isAdmin;
            this.state.canViewExams = isAdmin;
            this.state.canViewAmenities = isAdmin;
        });

        onMounted(() => {
            this.fetch_data();
        });
    }

    _setHTML(selector, value) {
        const el = document.querySelector(selector);
        if (el) {
            el.innerHTML = value;
        }
    }

    _setText(selector, value) {
        const el = document.querySelector(selector);
        if (el) {
            el.textContent = value;
        }
    }

    _setStyle(selector, property, value) {
        const el = document.querySelector(selector);
        if (el) {
            el.style[property] = value;
        }
    }

    onDashboardCardClick(ev) {
        const card = ev.currentTarget;
        const actionType = card.dataset.action;

        const permissionMap = {
            faculties: this.state.canViewFaculty,
            students: this.state.canViewStudents,
            exams: this.state.canViewExams,
            amenities: this.state.canViewAmenities,
        };

        if (!permissionMap[actionType]) {
            return;
        }

        const currentAcademicYearId = this.state.currentAcademicYearId; // make sure this is loaded in state

        const actionMap = {
            faculties: {
                name: "Faculties",
                res_model: "ala.education.faculty",
            },
            students: {
                name: "Students",
                res_model: "ala.education.student",
                domain: [
                    ["tc_issued", "=", false],
                    ["drop_out", "=", false],
                    ["active", "=", true],
                ],
            },
            exams: {
                name: "Exams",
                res_model: "ala.education.exam",
                domain: currentAcademicYearId
                    ? [["academic_year_id", "=", currentAcademicYearId]]
                    : [],
            },
            amenities: {
                name: "Amenities",
                res_model: "ala.education.amenities",
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
        });
    }

    async fetch_data() {
        const result = await this.orm.call("ala.erp.dashboard", "erp_data", []);

        this._setHTML("#all_students", `<span>${result.students || 0}</span>`);
        this._setHTML("#student_male", `<span>${result.male_student_count || 0}</span>`);
        this._setHTML("#student_female", `<span>${result.female_student_count || 0}</span>`);
        this._setHTML("#all_faculties", `<span>${result.faculties || 0}</span>`);
        this._setHTML("#faculty_male", `<span>${result.faculty_male || 0}</span>`);
        this._setHTML("#faculty_female", `<span>${result.faculty_female || 0}</span>`);
        this._setHTML("#all_amenities", `<span>${result.amenities || 0}</span>`);
        this._setHTML("#amenities_outdoor", `<span>${result.amenities_outdoor || 0}</span>`);
        this._setHTML("#amenities_indoor", `<span>${result.amenities_indoor || 0}</span>`);
        this._setHTML("#all_exams", `<span>${result.exams || 0}</span>`);
        this._setHTML("#exam_ongoing", `<span>${result.exam_ongoing || 0}</span>`);
        this._setHTML("#exam_closed", `<span>${result.exam_closed || 0}</span>`);

        this._setText("#total_students", result.total_students || result.students || "--");
        this._setText("#today_present", result.today_present || "--");
        this._setText("#today_homeworks", result.today_homeworks || "--");
        this._setText("#today_absent", result.today_absent || "--");

        this.state.currentAcademicYearId = result.current_academic_year_id || false;
        const updatedDiv = result.updated_divisions || 0;
        const totalDiv = result.total_divisions || 0;
        const percent = totalDiv > 0 ? ((updatedDiv / totalDiv) * 100).toFixed(0) : 0;

        this._setHTML(
            "#div_update_ratio",
            `<span>${updatedDiv}</span>/<span>${totalDiv}</span>
             <small style="font-size:12px;color:#6b7280;">(${percent}% Updated)</small>`
        );

        this._setStyle("#division_progress_bar", "width", `${percent}%`);

        this.renderDivisionSummary(result.division_summary || []);
        this.renderValuationSummary(result.valuation_summary || []);
        this.renderTeacherTasks(result.teacher_tasks || []);
    }

    renderDivisionSummary(divisions) {
        const grid = document.querySelector("#division_summary_grid");
        if (!grid) {
            return;
        }

        grid.innerHTML = "";

        if (!divisions.length) {
            grid.innerHTML = `<div class="col-12 text-center text-muted">No divisions found</div>`;
            return;
        }

        divisions.forEach((div) => {
            const isNotUpdated = div.status === "Not Updated";
            const cardColor = isNotUpdated
                ? "background: #fffbea; border: 1px solid #ffe58f;"
                : "background: #e9f7ef; border: 1px solid #b6e2c7;";

            const cardContent = isNotUpdated
                ? `<p class="mb-0" style="font-size:12px; color:#b8860b;">
                       <i class="fa fa-clock-o me-1" style="font-size:11px;"></i> Not updated yet
                   </p>`
                : `<div class="stats d-flex justify-content-between mt-1" style="font-size:14px;">
                       <span class="total text-primary">👥 ${div.total || 0}</span>
                       <span class="present text-success">✅ ${div.present || 0}</span>
                       <span class="absent text-danger">❌ ${div.absent || 0}</span>
                   </div>`;

            const wrapper = document.createElement("div");
            wrapper.className = "col-md-3 col-sm-6 col-12 p-1";
            wrapper.innerHTML = `
                <div class="division-card ${isNotUpdated ? "not-updated" : ""}"
                     data-attendance-id="${div.id || ""}"
                     data-division-id="${div.division_id || ""}"
                     style="${cardColor} cursor:pointer;
                            border-radius:8px; padding:6px 8px;
                            box-shadow:0 1px 3px rgba(0,0,0,0.08); font-size:13px;">
                    <h6 class="mb-0 text-center" style="font-weight:600;">
                        ${div.division || ""}
                    </h6>

                    <p class="text-info mb-0 text-center">
                        🏠 Homeworks:
                        <span class="badge bg-light text-dark">
                            ${div.div_homeworks || 0}
                        </span>
                    </p>

                    ${cardContent}
                </div>
            `;

            const card = wrapper.querySelector(".division-card");
            if (card) {
                card.addEventListener("click", (e) => this.onclick_division_attendance(e));
            }

            grid.appendChild(wrapper);
        });
    }

    renderValuationSummary(valuations) {
        const valuationBody = document.querySelector("#valuation_summary_body");
        if (!valuationBody) {
            return;
        }

        valuationBody.innerHTML = "";

        if (!valuations.length) {
            valuationBody.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center text-muted py-2">
                        No valuations found
                    </td>
                </tr>
            `;
            return;
        }

        valuations.forEach((v) => {
            const stateClass =
                v.state === "Completed" ? "completed" :
                v.state === "Draft" ? "pending" : "cancelled";

            const row = document.createElement("tr");
            row.className = "valuation-row text-center";
            row.dataset.id = v.id;
            row.style.cursor = "pointer";
            row.innerHTML = `
                <td>${v.exam_name || ""}</td>
                <td>${v.subject_name || ""}</td>
                <td>${v.class_name || ""} - ${v.division_name || ""}</td>
                <td>
                    <span class="task-status ${stateClass}">
                        ${v.state || ""}
                    </span>
                </td>
            `;
            row.addEventListener("click", (e) => this.onclick_valuation(e));
            valuationBody.appendChild(row);
        });
    }

    renderTeacherTasks(tasks) {
        const taskBody = document.querySelector("#teacher_task_body");
        if (!taskBody) {
            return;
        }

        taskBody.innerHTML = "";

        if (!tasks.length) {
            taskBody.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center text-muted py-2">
                        No tasks found
                    </td>
                </tr>
            `;
            return;
        }

        tasks.forEach((t) => {
            const stateClass =
                t.state === "Completed" ? "completed" :
                t.state === "Pending" ? "pending" : "overdue";

            const row = document.createElement("tr");
            row.className = "task-row text-center";
            row.dataset.id = t.id;
            row.style.cursor = "pointer";
            row.innerHTML = `
                <td>${t.teacher_name || ""}</td>
                <td>${t.task_name || ""}</td>
                <td>${t.date || ""}</td>
                <td>
                    <span class="task-status ${stateClass}">
                        ${t.state || ""}
                    </span>
                </td>
            `;
            row.addEventListener("click", (e) => this.onclick_task(e));
            taskBody.appendChild(row);
        });
    }

    onclick_task(e) {
        e.preventDefault();

        const row = e.currentTarget.closest(".task-row");
        if (!row) {
            return;
        }

        const taskId = row.dataset.id;
        if (!taskId) {
            return;
        }

        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Task",
            res_model: "ala.task.management",
            res_id: Number(taskId),
            views: [[false, "form"]],
            target: "current",
        });
    }

    onclick_valuation(e) {
        e.preventDefault();

        const row = e.currentTarget.closest(".valuation-row");
        if (!row) {
            return;
        }

        const valuationId = row.dataset.id;
        if (!valuationId) {
            return;
        }

        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Exam Valuation",
            res_model: "ala.education.exam.valuation",
            res_id: Number(valuationId),
            views: [[false, "form"]],
            target: "current",
        });
    }

    onclick_division_attendance(e) {
        e.preventDefault();

        const card = e.currentTarget.closest(".division-card");
        if (!card) {
            return;
        }

        const attendanceId = card.dataset.attendanceId;
        const divisionId = card.dataset.divisionId;

        if (attendanceId) {
            this.action.doAction({
                type: "ir.actions.act_window",
                name: "Attendance",
                res_model: "ala.education.attendance",
                res_id: Number(attendanceId),
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
            domain: [["division_id", "=", Number(divisionId)]],
            context: {
                default_division_id: Number(divisionId),
            },
            target: "current",
        });
    }

    onclick_student_list(e) {
        e.preventDefault();
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Students",
            res_model: "ala.education.student",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    onclick_faculty_list(e) {
        e.preventDefault();
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Faculties",
            res_model: "ala.education.faculty",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    onclick_attendance_list(e) {
        e.preventDefault();
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Attendance",
            res_model: "ala.education.attendance",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    onclick_exam_list(e) {
        e.preventDefault();
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Exams",
            res_model: "ala.education.exam",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    onclick_amenities_list(e) {
        e.preventDefault();
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Amenities",
            res_model: "ala.education.amenities",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }
}

EducationalDashboard.template = "ala_education_erp_dashboard.EducationalDashboard";
registry.category("actions").add("ala_erp_dashboard_tag", EducationalDashboard);