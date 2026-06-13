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

        this.companyId = this.user.context.allowed_company_ids?.[0] || false;

        this.state = useState({
            canViewFaculty: false,
            canViewStudents: false,
            canViewExams: false,
            canViewAmenities: false,
            currentAcademicYearId: false,
        });

        onWillStart(async () => {
            const [isPrincipal, isOfficeAdmin] = await Promise.all([
                this.user.hasGroup("ala_education_core.group_education_principal"),
                this.user.hasGroup("ala_education_core.group_education_office_admin"),
            ]);
            const isAdmin = isPrincipal || isOfficeAdmin;
            this.state.canViewFaculty = isAdmin;
            this.state.canViewStudents = isAdmin;
            this.state.canViewExams = isAdmin;
            this.state.canViewAmenities = isAdmin;
        });

        onMounted(() => {
            this._showSkeleton();
            this._fetchCritical();
        });
    }

    // ─── Skeleton ────────────────────────────────────────────────────────────

    _showSkeleton() {
        const pulse = `<span class="skel-pulse" style="
            display:inline-block;width:48px;height:20px;
            background:linear-gradient(90deg,#e2e8f0 25%,#f1f5f9 50%,#e2e8f0 75%);
            background-size:200% 100%;animation:skelPulse 1.2s ease-in-out infinite;
            border-radius:4px;vertical-align:middle;"></span>`;

        const statIds = [
            "all_students","student_male","student_female",
            "all_faculties","faculty_male","faculty_female",
            "all_amenities","amenities_indoor","amenities_outdoor",
            "all_exams","exam_ongoing","exam_closed",
        ];
        statIds.forEach(id => this._setHTML(`#${id}`, pulse));

        ["total_students","today_present","today_absent","today_homeworks"].forEach(id => {
            this._setHTML(`#${id}`, pulse);
        });

        const grid = document.querySelector("#division_summary_grid");
        if (grid) {
            grid.innerHTML = Array.from({length: 8}, () =>
                `<div class="col-md-3 col-sm-6 col-12 p-1">
                    <div style="height:72px;background:#e2e8f0;border-radius:8px;
                         animation:skelPulse 1.2s ease-in-out infinite;"></div>
                </div>`
            ).join("");
        }

        ["teacher_task_body","valuation_summary_body"].forEach(id => {
            const el = document.querySelector(`#${id}`);
            if (el) el.innerHTML = `<tr><td colspan="4" class="text-center py-3">
                <span class="skel-pulse" style="display:inline-block;width:200px;height:16px;
                background:linear-gradient(90deg,#e2e8f0 25%,#f1f5f9 50%,#e2e8f0 75%);
                background-size:200% 100%;animation:skelPulse 1.2s ease-in-out infinite;
                border-radius:4px;"></span></td></tr>`;
        });
    }

    // ─── Two-phase fetch ──────────────────────────────────────────────────────────

    async _fetchCritical() {
        const result = await this.orm.call("ala.erp.dashboard", "erp_data", []);
        this._renderCritical(result);

        if ("requestIdleCallback" in window) {
            requestIdleCallback(() => this._fetchDeferred(result.students), { timeout: 2000 });
        } else {
            setTimeout(() => this._fetchDeferred(result.students), 300);
        }
    }

    async _fetchDeferred(totalStudents) {
        const result = await this.orm.call("ala.erp.dashboard", "erp_data_deferred", []);
        this._renderDeferred(result, totalStudents);
    }

    // ─── Render critical (counts only — no attendance, no divisions) ──────────────

    _renderCritical(result) {
        this._setHTML("#all_students",      `<span>${result.students || 0}</span>`);
        this._setHTML("#student_male",      `<span>${result.male_student_count || 0}</span>`);
        this._setHTML("#student_female",    `<span>${result.female_student_count || 0}</span>`);
        this._setHTML("#all_faculties",     `<span>${result.faculties || 0}</span>`);
        this._setHTML("#faculty_male",      `<span>${result.faculty_male || 0}</span>`);
        this._setHTML("#faculty_female",    `<span>${result.faculty_female || 0}</span>`);
        this._setHTML("#all_amenities",     `<span>${result.amenities || 0}</span>`);
        this._setHTML("#amenities_indoor",  `<span>${result.amenities_indoor || 0}</span>`);
        this._setHTML("#amenities_outdoor", `<span>${result.amenities_outdoor || 0}</span>`);
        this._setHTML("#all_exams",         `<span>${result.exams || 0}</span>`);
        this._setHTML("#exam_ongoing",      `<span>${result.exam_ongoing || 0}</span>`);
        this._setHTML("#exam_closed",       `<span>${result.exam_closed || 0}</span>`);

        this.state.currentAcademicYearId = result.current_academic_year_id || false;
        // attendance stats stay as skeleton until deferred resolves
    }

    // ─── Render deferred (attendance + divisions + tasks + valuations) ────────────

    _renderDeferred(result, totalStudents) {
        // Attendance summary row
        this._setText("#total_students",  totalStudents || "--");
        this._setText("#today_present",   result.today_present   || "--");
        this._setText("#today_absent",    result.today_absent    || "--");
        this._setText("#today_homeworks", result.today_homeworks || "--");

        // Division progress bar
        const updatedDiv = result.updated_divisions || 0;
        const totalDiv   = result.total_divisions   || 0;
        const percent    = totalDiv > 0 ? ((updatedDiv / totalDiv) * 100).toFixed(0) : 0;

        this._setHTML(
            "#div_update_ratio",
            `<span>${updatedDiv}</span>/<span>${totalDiv}</span>
             <small style="font-size:12px;color:#6b7280;">(${percent}% Updated)</small>`
        );
        this._setStyle("#division_progress_bar", "width", `${percent}%`);

        // Render all three deferred sections
        this.renderDivisionSummary(result.division_summary   || []);
        this.renderTeacherTasks(result.teacher_tasks         || []);
        this.renderValuationSummary(result.valuation_summary || []);
    }

    // ─── DOM helpers ─────────────────────────────────────────────────────────

    _setHTML(selector, value) {
        const el = document.querySelector(selector);
        if (el) el.innerHTML = value;
    }

    _setText(selector, value) {
        const el = document.querySelector(selector);
        if (el) el.textContent = value;
    }

    _setStyle(selector, property, value) {
        const el = document.querySelector(selector);
        if (el) el.style[property] = value;
    }

    // ─── Division summary (batched DOM write) ─────────────────────────────────

    renderDivisionSummary(divisions) {
        const grid = document.querySelector("#division_summary_grid");
        if (!grid) return;

        if (!divisions.length) {
            grid.innerHTML = `<div class="col-12 text-center text-muted">No divisions found</div>`;
            return;
        }

        // Build all nodes in a fragment — one reflow instead of N
        const frag = document.createDocumentFragment();

        divisions.forEach((div) => {
            const isNotUpdated = div.status === "Not Updated";
            const cardColor = isNotUpdated
                ? "background:#fffbea;border:1px solid #ffe58f;"
                : "background:#e9f7ef;border:1px solid #b6e2c7;";

            const cardContent = isNotUpdated
                ? `<p class="mb-0" style="font-size:12px;color:#b8860b;">
                       <i class="fa fa-clock-o me-1"></i>Not updated yet
                   </p>`
                : `<div class="stats d-flex justify-content-between mt-1" style="font-size:14px;">
                       <span class="text-primary">👥 ${div.total || 0}</span>
                       <span class="text-success">✅ ${div.present || 0}</span>
                       <span class="text-danger">❌ ${div.absent || 0}</span>
                   </div>`;

            const wrapper = document.createElement("div");
            wrapper.className = "col-md-3 col-sm-6 col-12 p-1";
            wrapper.innerHTML = `
                <div class="division-card${isNotUpdated ? " not-updated" : ""}"
                     data-attendance-id="${div.id || ""}"
                     data-division-id="${div.division_id || ""}"
                     style="${cardColor}cursor:pointer;border-radius:8px;padding:6px 8px;
                            box-shadow:0 1px 3px rgba(0,0,0,0.08);font-size:13px;">
                    <h6 class="mb-0 text-center" style="font-weight:600;">${div.division || ""}</h6>
                    <p class="text-info mb-0 text-center">
                        🏠 Homeworks:
                        <span class="badge bg-light text-dark">${div.div_homeworks || 0}</span>
                    </p>
                    ${cardContent}
                </div>`;

            wrapper.querySelector(".division-card")
                .addEventListener("click", (e) => this.onclick_division_attendance(e));

            frag.appendChild(wrapper);
        });

        grid.innerHTML = "";
        grid.appendChild(frag);   // single reflow
    }

    // ─── Task + valuation renders (same batching pattern) ────────────────────

    renderTeacherTasks(tasks) {
        const taskBody = document.querySelector("#teacher_task_body");
        if (!taskBody) return;

        if (!tasks.length) {
            taskBody.innerHTML = `<tr><td colspan="4" class="text-center text-muted py-2">No tasks found</td></tr>`;
            return;
        }

        const frag = document.createDocumentFragment();
        tasks.forEach((t) => {
            const stateClass =
                t.state === "Completed" ? "completed" :
                t.state === "Pending"   ? "pending"   : "overdue";

            const row = document.createElement("tr");
            row.className = "task-row text-center";
            row.dataset.id = t.id;
            row.style.cursor = "pointer";
            row.innerHTML = `
                <td>${t.teacher_name || ""}</td>
                <td>${t.task_name || ""}</td>
                <td>${t.date || ""}</td>
                <td><span class="task-status ${stateClass}">${t.state || ""}</span></td>`;
            row.addEventListener("click", (e) => this.onclick_task(e));
            frag.appendChild(row);
        });

        taskBody.innerHTML = "";
        taskBody.appendChild(frag);
    }

    renderValuationSummary(valuations) {
        const valuationBody = document.querySelector("#valuation_summary_body");
        if (!valuationBody) return;

        if (!valuations.length) {
            valuationBody.innerHTML = `<tr><td colspan="4" class="text-center text-muted py-2">No valuations found</td></tr>`;
            return;
        }

        const frag = document.createDocumentFragment();
        valuations.forEach((v) => {
            const stateClass = v.state === "Completed" ? "completed" :
                               v.state === "Draft"     ? "pending"   : "cancelled";
            const row = document.createElement("tr");
            row.className = "valuation-row text-center";
            row.dataset.id = v.id;
            row.style.cursor = "pointer";
            row.innerHTML = `
                <td>${v.exam_name || ""}</td>
                <td>${v.subject_name || ""}</td>
                <td>${v.class_name || ""} - ${v.division_name || ""}</td>
                <td><span class="task-status ${stateClass}">${v.state || ""}</span></td>`;
            row.addEventListener("click", (e) => this.onclick_valuation(e));
            frag.appendChild(row);
        });

        valuationBody.innerHTML = "";
        valuationBody.appendChild(frag);
    }

    // ─── Click handlers (unchanged) ──────────────────────────────────────────

    onDashboardCardClick(ev) {
        const card = ev.currentTarget;
        const actionType = card.dataset.action;
        const permissionMap = {
            faculties: this.state.canViewFaculty,
            students:  this.state.canViewStudents,
            exams:     this.state.canViewExams,
            amenities: this.state.canViewAmenities,
        };
        if (!permissionMap[actionType]) return;

        const currentAcademicYearId = this.state.currentAcademicYearId;
        const actionMap = {
            faculties: { name: "Faculties",  res_model: "ala.education.faculty" },
            students:  { name: "Students",   res_model: "ala.education.student",
                         domain: [["tc_issued","=",false],["drop_out","=",false],["active","=",true]] },
            exams:     { name: "Exams",      res_model: "ala.education.exam",
                         domain: currentAcademicYearId ? [["academic_year_id","=",currentAcademicYearId]] : [] },
            amenities: { name: "Amenities",  res_model: "ala.education.amenities" },
        };
        const action = actionMap[actionType];
        if (!action) return;

        this.action.doAction({
            type: "ir.actions.act_window",
            name: action.name,
            res_model: action.res_model,
            domain: action.domain || [],
            views: [[false,"list"],[false,"form"]],
            target: "current",
        });
    }

    onclick_task(e) {
        e.preventDefault();
        const row = e.currentTarget.closest(".task-row");
        if (!row?.dataset.id) return;
        this.action.doAction({
            type: "ir.actions.act_window", name: "Task",
            res_model: "ala.task.management", res_id: Number(row.dataset.id),
            views: [[false,"form"]], target: "current",
        });
    }

    onclick_valuation(e) {
        e.preventDefault();
        const row = e.currentTarget.closest(".valuation-row");
        if (!row?.dataset.id) return;
        this.action.doAction({
            type: "ir.actions.act_window", name: "Exam Valuation",
            res_model: "ala.education.exam.valuation", res_id: Number(row.dataset.id),
            views: [[false,"form"]], target: "current",
        });
    }

    onclick_division_attendance(e) {
        e.preventDefault();
        const card = e.currentTarget.closest(".division-card");
        if (!card) return;
        const attendanceId = card.dataset.attendanceId;
        const divisionId   = card.dataset.divisionId;

        if (attendanceId) {
            return this.action.doAction({
                type: "ir.actions.act_window", name: "Attendance",
                res_model: "ala.education.attendance", res_id: Number(attendanceId),
                views: [[false,"form"]], target: "current",
            });
        }
        this.action.doAction({
            type: "ir.actions.act_window", name: "Attendance",
            res_model: "ala.education.attendance",
            views: [[false,"list"],[false,"form"]],
            domain: [["division_id","=",Number(divisionId)]],
            context: { default_division_id: Number(divisionId) },
            target: "current",
        });
    }

    onclick_student_list(e)    { e.preventDefault(); this._openList("Students",   "ala.education.student"); }
    onclick_faculty_list(e)    { e.preventDefault(); this._openList("Faculties",  "ala.education.faculty"); }
    onclick_attendance_list(e) { e.preventDefault(); this._openList("Attendance", "ala.education.attendance"); }
    onclick_exam_list(e)       { e.preventDefault(); this._openList("Exams",      "ala.education.exam"); }
    onclick_amenities_list(e)  { e.preventDefault(); this._openList("Amenities",  "ala.education.amenities"); }

    _openList(name, res_model) {
        this.action.doAction({
            type: "ir.actions.act_window", name, res_model,
            views: [[false,"list"],[false,"form"]], target: "current",
        });
    }
}

EducationalDashboard.template = "ala_education_erp_dashboard.EducationalDashboard";
registry.category("actions").add("ala_erp_dashboard_tag", EducationalDashboard);