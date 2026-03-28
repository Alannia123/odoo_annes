/* @odoo-module */

import { Component, useState, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

class AttendanceDashboard extends Component {
    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
        this.root = useRef("attendance-dashboard");

        this.state = useState({
            filteredDurationDates: [],
            student_data: [],
            divisions: [],
            selected_division: "",
        });

        // Load divisions immediately
        this.loadDivisions();
    }

    // --------------------------------------------------
    // Load all divisions
    // --------------------------------------------------
    async loadDivisions() {
        try {
            const divisions = await this.orm.searchRead(
                "ala.education.class.division",   // Update to YOUR model if needed
                [],
                ["name"]
            );
            this.state.divisions = divisions || [];
        } catch (e) {
            console.error("Failed to load divisions", e);
        }
    }

    // --------------------------------------------------
    // When user selects a division
    // --------------------------------------------------
    onChangeDivision(ev) {
        this.state.selected_division = ev.target.value;
        ev.stopPropagation();
        const duration = this.state.filter_duration;
        const division_id = ev.target.value;
        if (!duration) {
            alert("Please select a Duration .");
            return;
        }
        this.onclick_this_filter(duration, division_id);

    }

    // --------------------------------------------------
    // Duration filter handler
    // --------------------------------------------------
    onChangeFilter(ev) {
        this.state.filter_duration = ev.target.value;
        ev.stopPropagation();
        const duration = ev.target.value;
        const division_id = this.state.selected_division;

        if (!division_id) {
            alert("Please select a division first.");
            return;
        }

        this.onclick_this_filter(duration, division_id);
    }

    // --------------------------------------------------
    // Fetch attendance data for that division + duration
    // --------------------------------------------------
    async onclick_this_filter(duration, division_id) {
        try {
            const result = await this.orm.call(
                "ala.education.student",
                "get_student_attendance_dashboard",
                [division_id, duration]
            );

            this.state.filteredDurationDates = result.filtered_duration_dates;
            this.state.student_data = result.student_data;
            console.log('DTATES------------',this.state.filteredDurationDates)
            console.log('DTATES------data------',this.state.student_data)
        } catch (e) {
            console.error("Error fetching attendance:", e);
        }
    }

    // --------------------------------------------------
    // Search student row in table
    // --------------------------------------------------
    _OnClickSearchEmployee(ev) {
        let searchbar = this.root.el.querySelector("#search-bar").value?.toLowerCase();
        let attendance_table_rows = this.root.el.querySelector("#attendance_table_nm").children[1];

        for (let tableRow of attendance_table_rows.children) {
            tableRow.style.display = tableRow.children[0]
                .getAttribute("data-name")
                .toLowerCase()
                .includes(searchbar)
                ? ""
                : "none";
        }
    }

    // --------------------------------------------------
    // Print PDF report
    // --------------------------------------------------
    _OnClickPdfReport(ev) {
        const table = this.root.el.querySelector("#attendance_table_nm");
        if (!table) {
            console.error("Attendance table not found");
            return;
        }

        const thead = table.querySelector("thead");
        const tbody = table.querySelector("tbody");

        const tHead = thead ? thead.innerHTML : "";
        const tBody = tbody ? tbody.innerHTML : "";

        return this.action.doAction({
            type: "ir.actions.report",
            report_type: "qweb-pdf",
            report_name: "ala_education_attendances.report_student_attendance",
            report_file: "ala_education_attendances.report_student_attendance",
            data: {
                tHead: tHead,
                tBody: tBody,
            },
        });
    }


    // --------------------------------------------------
    // Format date for header
    // --------------------------------------------------
    formatDate(inputDate) {
        const months = [
            "JAN","FEB","MAR","APR","MAY","JUN",
            "JUL","AUG","SEP","OCT","NOV","DEC"
        ];

        const [year, month, day] = inputDate.split("-");
        return `${day}-${months[parseInt(month, 10) - 1]}-${year}`;
    }
}

AttendanceDashboard.template = "AttendanceDashboard";
registry.category("actions").add("attendance_dashboard", AttendanceDashboard);
