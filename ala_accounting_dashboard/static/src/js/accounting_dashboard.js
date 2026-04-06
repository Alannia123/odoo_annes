/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onMounted, onWillStart, useRef, useState } from "@odoo/owl";

export class AccountDashboard extends Component {
    setup() {
        this.state = useState({
            data: {},
            top: {},
            income_chart: {},
            chart: [],
            payment_data: [],
            top_sale_cust: [],
            aged_payable: {},
            balance: [],
            IncomeExpense: "income",
            top_filter: "this_month",
            income: "income_this_month",
            aged_filter: "aged_receive",
            top_sale_cust_filter: "this_month",
            aged_payable_filter: "this_month",
            payment_data_filter: "this_month",
            payment_list_filter: "customer_payment",
        });

        this.All = useRef("All");
        this.AgedRecords = useRef("AgedRecords");
        this.Balance = useRef("Balance");

        this.orm = useService("orm");
        this.action = useService("action");

        onWillStart(async () => {
            await this.fetchData();
        });

        onMounted(() => {
            this.renderCharts();
        });
    }

    _destroyCharts() {
        if (Array.isArray(this.state.chart) && this.state.chart.length) {
            for (const chart of this.state.chart) {
                if (chart && typeof chart.destroy === "function") {
                    chart.destroy();
                }
            }
        }
        this.state.chart = [];
    }

    async downloadTodayReport() {
        const action = await this.orm.call("account.move", "action_download_today_invoice_report", []);
        if (action) {
            return this.action.doAction(action);
        }
    }

    async onPeriodChange() {
        this._destroyCharts();
        await this.fetchAndRender();
    }

    async fetchAndRender() {
        await this.fetchData();
        this.renderCharts();
    }

    async fetchData() {
        this.state.data = await this.orm.call("account.move", "get_datas", []);
        this.state.income_chart = await this.orm.call("account.move", "get_income_chart", [this.state.income]);
        this.state.payment_data = await this.orm.call("account.move", "get_payment_data", [this.state.payment_list_filter, this.state.payment_data_filter]);
        this.state.top = await this.orm.call("account.move", "get_top_datas", [this.state.top_filter]);
        this.state.aged_payable = await this.orm.call("account.move", "get_aged_payable", [this.state.aged_filter, this.state.aged_payable_filter]);
        this.state.top_sale_cust = await this.orm.call("account.move", "get_sale_revenue", [this.state.top_sale_cust_filter]);
        this.state.balance = await this.orm.call("account.move", "get_bank_balance", []);
    }

    renderCharts() {
        if (this.AgedRecords.el && this.state.aged_payable?.partner?.length) {
            this.agedChart(this.AgedRecords.el, "bar", this.state.aged_payable.partner, "Amount", this.state.aged_payable.amount || []);
        }

        if (!this.All.el) {
            return;
        }

        if (this.state.IncomeExpense === "income") {
            this.incomeChart(this.All.el, "bar", this.state.income_chart.date || [], this.state.income_chart.income || []);
        } else if (this.state.IncomeExpense === "expense") {
            this.expenseChart(this.All.el, "bar", this.state.income_chart.date || [], this.state.income_chart.expense || []);
        } else if (this.state.IncomeExpense === "profit") {
            this.profitChart(this.All.el, "line", this.state.income_chart.date || [], this.state.income_chart.profit || []);
        } else {
            this.allInOneChart(
                this.All.el,
                "bar",
                this.state.income_chart.date || [],
                this.state.income_chart.income || [],
                this.state.income_chart.expense || [],
                this.state.income_chart.profit || []
            );
        }
    }

    agedChart(canvas, type, labels, label, data) {
        this.state.chart.push(new Chart(canvas, {
            type,
            data: {
                labels,
                datasets: [{
                    label,
                    data,
                    borderRadius: 10,
                    backgroundColor: "rgba(39, 232, 232, 0.5)",
                    borderColor: "rgba(39, 232, 232, 1)",
                }],
            },
        }));
    }

    incomeChart(canvas, type, labels, data) {
        this.state.chart.push(new Chart(canvas, {
            type,
            data: {
                labels,
                datasets: [{
                    label: "Income",
                    data,
                    borderWidth: 2,
                    borderRadius: 10,
                    borderSkipped: false,
                    backgroundColor: "rgba(39, 232, 232, 0.5)",
                    borderColor: "rgba(39, 232, 232, 1)",
                }],
            },
        }));
    }

    expenseChart(canvas, type, labels, expense) {
        this.state.chart.push(new Chart(canvas, {
            type,
            data: {
                labels,
                datasets: [{
                    label: "Expense",
                    data: expense,
                    type: type === "bar" ? "polarArea" : "bar",
                }],
            },
        }));
    }

    profitChart(canvas, type, labels, profit) {
        this.state.chart.push(new Chart(canvas, {
            type,
            data: {
                labels,
                datasets: [{
                    label: "Profit/Loss",
                    data: profit,
                    fill: true,
                    borderColor: "rgba(245, 65, 10, 1)",
                }],
            },
        }));
    }

    allInOneChart(canvas, type, labels, income, expense, profit) {
        this.state.chart.push(new Chart(canvas, {
            type,
            data: {
                labels,
                datasets: [{
                    label: "Income",
                    data: income,
                    type: type === "line" ? "line" : "bar",
                    backgroundColor: "rgba(39, 232, 232, 0.5)",
                    borderColor: "rgba(39, 232, 232, 1)",
                }, {
                    label: "Expense",
                    data: expense,
                    type: type === "bar" ? "radar" : "bar",
                    backgroundColor: "rgba(0, 0, 0, 0.5)",
                    borderColor: "rgba(0, 0, 0, 1)",
                }, {
                    label: "Profit/Loss",
                    data: profit,
                    type: "line",
                    fill: false,
                    borderColor: "rgba(245, 65, 10, 1)",
                }],
            },
        }));
    }
}

AccountDashboard.template = "ala_accounting_dashboard.AccountDashboard";
registry.category("actions").add("ala_accounting_dashboard_tags", AccountDashboard);
