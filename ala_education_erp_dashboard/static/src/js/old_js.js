/** @odoo-module */
import { registry } from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
const { Component, onWillStart, onMounted } = owl;
import { jsonrpc } from "@web/core/network/rpc_service";
import { _t } from "@web/core/l10n/translation";
import { session } from "@web/session";
import { WebClient } from "@web/webclient/webclient";
import { useRef } from "@odoo/owl";

export class EducationalDashboard extends Component {

    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
        this.action = useService("action");
        onMounted(async () => {
            this.fetch_data();
        });

        onMounted(() => {
        // ✅ Fetch dashboard data ONCE
        this.fetch_data();

        // ✅ Delegate click for dynamic task rows
        $(document)
    .off("click", ".task-row")
    .on("click", ".task-row", (e) => {
        this.onclick_task(e);
    });

    });

    }

    // ✅ correct syntax for class method
    animateCount(element, targetValue, duration = 1000) {
        const el = $(element);
        let startValue = 0;
        const increment = targetValue / (duration / 16);
        el.addClass("updated");
        const timer = setInterval(() => {
            startValue += increment;
            if (startValue >= targetValue) {
                startValue = targetValue;
                clearInterval(timer);
                el.removeClass("updated");
            }
            el.text(Math.floor(startValue));
        }, 16);
    }


    /** Fetch dashboard data (counts for Students, Faculties, etc.) */
    fetch_data() {
        this.orm.call("ala.erp.dashboard", "erp_data", [])
        .then(function (result) {
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
                     style="${cardColor} border-radius:8px; padding:6px 8px; box-shadow:0 1px 3px rgba(0,0,0,0.08); font-size:13px; overflow:hidden;">
                    <h6 class="mb-0 text-center" style="font-weight:600; font-size:13px; color:#2c3e50;">
                        ${div.division}
                    </h6>
                    <p class="text-info mb-0 text-center" style="font-size:15px;">
                        🏠 Homeworks:
                        <span style="
                            font-size:15px;
                            padding: 2px 8px;
                            border-radius: 6px;
                            background: linear-gradient(48deg, #dee2e6, #ffffff);
                            font-weight: 600;
                            color: #212529;
                        ">
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

const taskBody = $('#teacher_task_body');
taskBody.empty();

if (result.teacher_tasks?.length) {
    result.teacher_tasks.forEach(t => {
        const stateClass =
            t.state === 'Completed' ? 'completed' :
            t.state === 'Pending' ? 'pending' : 'overdue';

        const row = `
            <tr class="text-center task-row"
                style="cursor:pointer;"
                data-id="${t.id}">
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

    /** Dropdown change handlers (simplified, no chart logic) */
    change_select_period(e) {
        e.preventDefault();
    }

    change_select_class(e) {
        e.preventDefault();
    }

    onclick_task(e) {
            e.preventDefault();

            // ✅ ALWAYS resolve the row explicitly
            const row = e.target.closest(".task-row");
            if (!row) {
                console.warn("Clicked element is not inside .task-row");
                return;
            }

            const taskId = row.getAttribute("data-id");
            if (!taskId) {
                console.warn("Task ID missing on row", row);
                return;
            }

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





    /** Click handlers for opening related records */
    async onclick_exam_list(e) {
        e.preventDefault();
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Exams",
            res_model: "ala.education.exam",
            views: [[false, 'list'], [false, 'form']],
            target: 'current',
        });
    }

    /** Click handlers for opening related records */
    async onclick_amenities_list(e) {
        e.preventDefault();
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Amenities",
            res_model: "ala.education.amenities",
            views: [[false, 'list'], [false, 'form']],
            target: 'current',
        });
    }

    onclick_student_list(e) {
        e.preventDefault();
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Students",
            res_model: "ala.education.student",
            views: [[false, 'list'], [false, 'form']],
            target: 'current',
        });
    }

    onclick_faculty_list(e) {
        e.preventDefault();
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Faculties",
            res_model: "ala.education.faculty",
            views: [[false, 'list'], [false, 'form']],
            target: 'current',
        });
    }

    onclick_amenity_list(e) {
        e.preventDefault();
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Amenities",
            res_model: "ala.education.amenities",
            views: [[false, 'list'], [false, 'form']],
            target: 'current',
        });
    }

    onclick_attendance_list(e) {
        e.preventDefault();
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Attendance",
            res_model: "ala.education.attendance",
            views: [[false, 'list'], [false, 'form']],
            target: 'current',
        });
    }

    onclick_exam_result(e) {
        e.preventDefault();
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Exam Result",
            res_model: "ala.education.exam",
            views: [[false, 'list'], [false, 'form']],
            target: 'current',
        });
    }

    onclick_timetable(e) {
        e.preventDefault();
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Timetable",
            res_model: "ala.education.timetable",
            views: [[false, 'list'], [false, 'form']],
            target: 'current',
        });
    }

    onclick_promotions(e) {
        e.preventDefault();
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Student Promotions",
            res_model: "ala.education.student.final.result",
            views: [[false, 'list'], [false, 'form']],
            target: 'current',
        });
    }

    /** Render filters (no chart filters now) */
    render_filters() {
        this.render_pie_chart_filter();
        this.render_doughnut_chart_filter();
    }

    render_pie_chart_filter() {
        this.orm.call("ala.erp.dashboard", "get_academic_year", [])
        .then(function (result) {
            $('#select_period').append('<option value="select">Total Result</option>');
            for (let key in result) {
                $('#select_period').append('<option value="' + key + '">' + result[key] + '</option>');
            }
        });
    }

    render_doughnut_chart_filter() {
        this.orm.call("ala.erp.dashboard", "get_classes", [])
        .then(function (result) {
            $('#select_class').append('<option value="select">Total Attendance</option>');
            for (let key in result) {
                $('#select_class').append('<option value="' + key + '">' + result[key] + '</option>');
            }
        });
    }
}

EducationalDashboard.template = "ala_education_erp_dashboard.EducationalDashboard";
registry.category("actions").add("ala_erp_dashboard_tag", EducationalDashboard);
