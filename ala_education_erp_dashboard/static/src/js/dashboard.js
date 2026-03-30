/** @odoo-module */

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onMounted, useState, onWillStart } from "@odoo/owl";

export class EducationalDashboard extends Component {

    setup() {
        super.setup(...arguments);

        this.orm = useService("orm");
        this.user = useService("user");
        this.action = useService("action");

        this.state = useState({
                canViewFaculty: false,
                canViewStudents: false,
                canViewExams: false,
                canViewAmenities: false,
            });

        onWillStart(async () => {
                const isAdmin =
                await this.user.hasGroup("ala_education_core.group_education_principal") ||
                await this.user.hasGroup("ala_education_core.group_education_office_admin");

                this.state.canViewFaculty = isAdmin;
                this.state.canViewStudents = isAdmin;
                this.state.canViewExams = isAdmin;
                this.state.canViewAmenities = isAdmin;
            });

        onMounted(() => {
            // Fetch dashboard data once
            this.fetch_data();

            // Delegate click for dynamically added task rows
            $(document)
                .off("click", ".task-row")
                .on("click", ".task-row", (e) => {
                    this.onclick_task(e);
                });

                                // Delegate click for dynamically added valuation rows
                $(document)
                    .off("click", ".valuation-row")
                    .on("click", ".valuation-row", (e) => {
                        this.onclick_valuation(e);
                    });


                // 🔹 Division card click
            $(document)
                .off("click", ".division-card")
                .on("click", ".division-card", (e) => {
                    this.onclick_division_attendance(e);
                });

        });
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
            return; // 🔒 blocked
        }

        const actionMap = {
            faculties: {
                name: "Faculties",
                res_model: "ala.education.faculty",
            },
            students: {
                name: "Students",
                res_model: "ala.education.student",
            },
            exams: {
                name: "Exams",
                res_model: "ala.education.exam",
            },
            amenities: {
                name: "Amenities",
                res_model: "ala.education.amenities",
            },
        };

        const action = actionMap[actionType];
        if (!action) return;

        this.action.doAction({
            type: "ir.actions.act_window",
            name: action.name,
            res_model: action.res_model,
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    /* ------------------------------------------------------------
       FETCH DASHBOARD DATA
    ------------------------------------------------------------ */
    fetch_data() {
        this.orm.call("ala.erp.dashboard", "erp_data", [])
            .then((result) => {

                $('#all_students').append('<span>' + result.students + '</span>');
            $('#student_male').append('<span>' + result.male_student_count + '</span>');
            $('#student_female').append('<span>' + result.female_student_count + '</span>');
            $('#all_faculties').append('<span>' + result.faculties + '</span>');
            $('#faculty_male').append('<span>' + result.faculty_male + '</span>');
            $('#faculty_female').append('<span>' + result.faculty_female + '</span>');
            $('#all_amenities').append('<span>' + result.amenities + '</span>');
            $('#amenities_outdoor').append('<span>' + result.amenities_outdoor + '</span>');
            $('#amenities_indoor').append('<span>' + result.amenities_indoor + '</span>');
            $('#all_exams').append('<span>' + result.exams + '</span>');
            $('#exam_ongoing').append('<span>' + result.exam_ongoing + '</span>');
            $('#exam_closed').append('<span>' + result.exam_closed + '</span>');

            // Update table
            $('#total_students').text(result.total_students || result.students || '--');
            $('#today_present').text(result.today_present || '--');
            $('#today_homeworks').text(result.today_homeworks || '--');
            $('#today_absent').text(result.today_absent || '--');

            // ✅ Division update ratio
            const updatedDiv = result.updated_divisions || 0;
            const totalDiv = result.total_divisions || 0;
            const percent = totalDiv > 0 ? ((updatedDiv / totalDiv) * 100).toFixed(0) : 0;


                    // Update text
            $('#div_update_ratio').html(
              `<span>${updatedDiv}</span>/<span>${totalDiv}</span>
               <small style="font-size:12px;color:#6b7280;">(${percent}% Updated)</small>`
            );

            // Animate tiny progress bar
            $('#division_progress_bar').css('width', `${percent}%`);

                    // Division-wise table
                   const grid = $('#division_summary_grid');
            grid.empty();

            if (result.division_summary?.length) {
                result.division_summary.forEach(div => {
                    const isNotUpdated = div.status === 'Not Updated';
                    const cardColor = isNotUpdated
                        ? 'background: #fffbea; border: 1px solid #ffe58f;'
                        : 'background: #e9f7ef; border: 1px solid #b6e2c7;';

                    const cardContent = isNotUpdated
                        ? `<p class="mb-0" style="font-size:12px; color:#b8860b;">
                               <i class="fa fa-clock-o me-1" style="font-size:11px;"></i> Not updated yet
                           </p>`
                        : `<div class="stats d-flex justify-content-between mt-1" style="font-size:14px;">
                               <span class="total text-primary">👥 ${div.total}</span>
                               <span class="present text-success">✅ ${div.present}</span>
                               <span class="absent text-danger">❌ ${div.absent}</span>
                           </div>`;

                    const cardHtml = `
                        <div class="col-md-3 col-sm-6 col-12 p-1">
                            <div class="division-card ${isNotUpdated ? 'not-updated' : ''}"
                                 data-attendance-id="${div.id || ''}"
                                 data-division-id="${div.division_id || ''}"
                                 style="${cardColor} cursor:pointer;
                                        border-radius:8px; padding:6px 8px;
                                        box-shadow:0 1px 3px rgba(0,0,0,0.08); font-size:13px;">
                                <h6 class="mb-0 text-center" style="font-weight:600;">
                                    ${div.division}
                                </h6>

                                <p class="text-info mb-0 text-center">
                                    🏠 Homeworks:
                                    <span class="badge bg-light text-dark">
                                        ${div.div_homeworks}
                                    </span>
                                </p>

                                ${cardContent}
                            </div>
                        </div>
                    `;

                    grid.append(cardHtml.trim());
                });
            } else {
                grid.html('<div class="col-12 text-center text-muted">No divisions found</div>');
            }

            /* ---------------- VALUATION TABLE ---------------- */
            const valuationBody = $("#valuation_summary_body");
            valuationBody.empty();

            if (result.valuation_summary?.length) {
                result.valuation_summary.forEach(v => {

                    const stateClass =
                        v.state === "Completed" ? "completed" :
                        v.state === "Draft" ? "pending" : "cancelled";

                    const row = `
                        <tr class="valuation-row text-center"
                            data-id="${v.id}"
                            style="cursor:pointer;">
                            <td>${v.exam_name}</td>
                            <td>${v.subject_name}</td>
                            <td>${v.class_name} - ${v.division_name}</td>
                            <td>
                                <span class="task-status ${stateClass}">
                                    ${v.state}
                                </span>
                            </td>
                        </tr>
                    `;
                    valuationBody.append(row);
                });

            } else {
                valuationBody.html(`
                    <tr>
                        <td colspan="4" class="text-center text-muted py-2">
                            No valuations found
                        </td>
                    </tr>
                `);
            }



                /* ---------------- TASK TABLE ---------------- */
                const taskBody = $("#teacher_task_body");
                taskBody.empty();

                if (result.teacher_tasks?.length) {
                    result.teacher_tasks.forEach(t => {
                        const stateClass =
                            t.state === "Completed" ? "completed" :
                            t.state === "Pending" ? "pending" : "overdue";

                        const row = `
                            <tr class="task-row text-center"
                                data-id="${t.id}"
                                style="cursor:pointer;">
                                <td>${t.teacher_name}</td>
                                <td>${t.task_name}</td>
                                <td>${t.date}</td>
                                <td>
                                    <span class="task-status ${stateClass}">
                                        ${t.state}
                                    </span>
                                </td>
                            </tr>
                        `;
                        taskBody.append(row);
                    });
                } else {
                    taskBody.html(`
                        <tr>
                            <td colspan="4" class="text-center text-muted py-2">
                                No tasks found
                            </td>
                        </tr>
                    `);
                }
            });
    }

    /* ------------------------------------------------------------
       TASK ROW CLICK → OPEN FORM VIEW
    ------------------------------------------------------------ */
    onclick_task(e) {
        e.preventDefault();

        // Always resolve the row (important)
        const row = e.target.closest(".task-row");
        if (!row) return;

        const taskId = row.dataset.id;
        if (!taskId) return;

        console.log("TASK ID:", taskId);

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

        // Always resolve the row (important)
        const row = e.target.closest(".valuation-row");
        if (!row) return;

        const valuationId = row.dataset.id;
        if (!valuationId) return;

        console.log("VALUATION ID:", valuationId);

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

        const card = e.target.closest(".division-card");
        if (!card) return;

        const attendanceId = card.dataset.attendanceId;
        const divisionId = card.dataset.divisionId;

        // ✅ If attendance already exists → open FORM directly
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

        // 🟡 Fallback → open list filtered by division
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Attendance",
            res_model: "ala.education.attendance",
            views: [[false, "list"], [false, "form"]],
            domain: [
                ["division_id", "=", Number(divisionId)]
            ],
            context: {
                default_division_id: Number(divisionId),
            },
            target: "current",
        });
    }




    /* ------------------------------------------------------------
       OTHER DASHBOARD ACTIONS
    ------------------------------------------------------------ */
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
