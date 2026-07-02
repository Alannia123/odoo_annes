/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onMounted, onWillStart } from "@odoo/owl";

export class EducationalDashboard extends Component {
    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
        this.dashboard_templates = ["MainSection"];

        onWillStart(async () => {
            if (this.props) {
                this.props.title = "Dashboard";
            }
            this.toggleElement(".academic_exam_result", false);
            this.toggleElement(".exam_result", true);
            this.toggleElement(".class_attendance_today", false);
            this.toggleElement(".total_attendance_today", true);
        });

        onMounted(async () => {
            await this.render_graphs();
            await this.fetch_data();
            await this.render_filters();
        });
    }

    qs(selector) {
        return document.querySelector(selector);
    }

    qsa(selector) {
        return Array.from(document.querySelectorAll(selector));
    }

    toggleElement(selector, show) {
        this.qsa(selector).forEach((el) => {
            el.style.display = show ? "" : "none";
        });
    }

    setHtml(selector, html) {
        const el = this.qs(selector);
        if (el) {
            el.innerHTML = html;
        }
    }

    async fetch_data() {
        const result = await this.orm.call("ala.erp.dashboard", "erp_data", []);
        this.setHtml("#all_applications", `<span>${result.applications || 0}</span>`);
        this.setHtml("#all_students", `<span>${result.students || 0}</span>`);
        this.setHtml("#all_faculties", `<span>${result.faculties || 0}</span>`);
        this.setHtml("#all_amenities", `<span>${result.amenities || 0}</span>`);
        this.setHtml("#all_exams", `<span>${result.exams || 0}</span>`);
    }

    change_select_period(e) {
        e.preventDefault();
        if (e.target.value === "select") {
            this.toggleElement(".academic_exam_result", false);
            this.toggleElement(".exam_result", true);
            this.render_exam_result_pie();
        } else {
            this.toggleElement(".exam_result", false);
            this.toggleElement(".academic_exam_result", true);
            this.get_academic_exam_result(e.target.value);
        }
    }

    change_select_class(e) {
        e.preventDefault();
        if (e.target.value === "select") {
            this.toggleElement(".class_attendance_today", false);
            this.toggleElement(".total_attendance_today", true);
            this.render_attendance_doughnut();
        } else {
            this.toggleElement(".total_attendance_today", false);
            this.toggleElement(".class_attendance_today", true);
            this.get_class_attendance(e.target.value);
        }
    }

    async openList(name, resModel) {
        return this.action.doAction({
            type: "ir.actions.act_window",
            name,
            res_model: resModel,
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    onclick_application_list(e) { e.preventDefault(); return this.openList("Applications", "ala.education.application"); }
    onclick_student_list(e) { e.preventDefault(); return this.openList("Students", "ala.education.student"); }
    onclick_faculty_list(e) { e.preventDefault(); return this.openList("Faculties", "ala.education.faculty"); }
    onclick_amenity_list(e) { e.preventDefault(); return this.openList("Amenities", "ala.education.amenities"); }
    onclick_attendance_list(e) { e.preventDefault(); return this.openList("Attendance", "ala.education.attendance"); }
    onclick_exam_result(e) { e.preventDefault(); return this.openList("Exam Result", "ala.education.exam"); }
    onclick_timetable(e) { e.preventDefault(); return this.openList("Timetable", "ala.education.timetable"); }
    onclick_promotions(e) { e.preventDefault(); return this.openList("Student Promotions", "ala.education.student.final.result"); }

    async render_graphs() {
        this.render_exam_result_pie();
        if (this.render_attendance_doughnut) this.render_attendance_doughnut();
        if (this.render_total_application_graph) this.render_total_application_graph();
        if (this.render_rejected_accepted_applications) this.render_rejected_accepted_applications();
        if (this.render_student_strength) this.render_student_strength();
        if (this.render_class_wise_average_marks) this.render_class_wise_average_marks();
    }

    async render_filters() {
        if (this.render_pie_chart_filter) this.render_pie_chart_filter();
        if (this.render_doughnut_chart_filter) this.render_doughnut_chart_filter();
    }

    async render_exam_result_pie() {
        const canvas = this.qs(".exam_result");
        if (!canvas || typeof Chart === "undefined") {
            return;
        }
        const ctx = canvas.getContext("2d");
        if (this.chart_total_result) {
            this.chart_total_result.destroy();
        }
        const result = await this.orm.call("ala.erp.dashboard", "get_exam_result", []);
        this.chart_total_result = new Chart(ctx, {
            type: "pie",
            data: {
                labels: Object.keys(result),
                datasets: [{
                    label: "Exam Result",
                    data: Object.values(result),
                    backgroundColor: ["#003f5c", "#dc143c"],
                    borderColor: ["#003f5c", "#dc143c"],
                    borderWidth: 1,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
            },
        });
    }

    async get_academic_exam_result(academicYear) {
        const canvas = this.qs(".academic_exam_result");
        if (!canvas || typeof Chart === "undefined") {
            return;
        }
        const ctx = canvas.getContext("2d");
        if (this.chart_academy_result) {
            this.chart_academy_result.destroy();
        }
        const result = await this.orm.call("ala.erp.dashboard", "get_academic_year_exam_result", [academicYear]);
        this.chart_academy_result = new Chart(ctx, {
            type: "pie",
            data: {
                labels: Object.keys(result),
                datasets: [{
                    label: "Academic Exam Result",
                    data: Object.values(result),
                    backgroundColor: ["#003f5c", "#dc143c"],
                    borderColor: ["#003f5c", "#dc143c"],
                    borderWidth: 1,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
            },
        });
    }
}

EducationalDashboard.template = "ala_student_portal.MainSection";
registry.category("actions").add("ala_student_portal.education_dashboard", EducationalDashboard);
