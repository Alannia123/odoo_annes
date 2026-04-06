# -*- coding: utf-8 -*-

import calendar
from odoo import api, models, fields
from datetime import date


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def action_download_today_invoice_report(self):
        today = date.today()

        invoices = self.search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date', '=', today)
        ])

        print('INFFFFFFFFFFFFFF',invoices)

        return self.env.ref(
            'ala_accounting_dashboard.today_invoice_report_action'
        ).report_action(invoices)



    @api.model
    def get_datas(self):
        """ Getting datas for tiles in the dashboard like count of open invoice , paid invoice etc"""
        invoices = self.search([('move_type', '=', 'out_invoice')])
        fees_lines = self.env['ala.student.fee.line'].search([])
        open_fee_lines = fees_lines.filtered(lambda x: x.payment_status != 'paid')
        paid_fee_lines = fees_lines.filtered(lambda x: x.payment_status == 'paid')
        overdue_fee_lines = fees_lines.filtered(lambda x: x.payment_status == 'over_due')
        self.env.cr.execute("""
            SELECT COALESCE(SUM(amount_total), 0)
            FROM account_move
            WHERE move_type = 'out_invoice'
              AND state = 'posted'
              
        """)
        total_income_amount = self.env.cr.fetchone()[0]

        # Expense
        self._cr.execute("""
            SELECT SUM(debit) AS debit, SUM(credit) AS credit
            FROM account_account, account_move_line
            WHERE account_move_line.account_id = account_account.id
              AND account_account.account_type = 'expense'
        """)
        debit_credit_expense = self._cr.dictfetchall()
        expense = [i['debit'] - i['credit'] if (
                i['debit'] is not None and i['credit'] is not None) else 0
                   for i in debit_credit_expense]
        expense = expense[0]  # expense is usually debit, no need to invert

        qry_reconcile = """ select count(*) FROM account_move_line l,account_account a
                                      where L.account_id=a.id AND l.full_reconcile_id IS NULL 
                                      AND l.balance != 0 AND a.reconcile IS TRUE"""
        self._cr.execute(qry_reconcile)
        reconcile_count = [i['count'] for i in self._cr.dictfetchall()]
        journal_list = self.env['account.journal'].search([])
        journal_data = []
        for i in journal_list:
            journal_data.append({'id': i.id,
                                 'name': i.name,
                                 'type': i.type})

        self._cr.execute("""
            SELECT 
                COALESCE(SUM(r.amount), 0) AS total_amount
            FROM 
                ala_application_fee_receipt r
            JOIN 
                ala_education_academic_year y
                    ON r.academic_year_id = y.id
            WHERE 
                r.state = 'paid'
                AND y.next_academic_year = TRUE
        """)
        result = self._cr.dictfetchone()
        total_paid = result['total_amount']


        today = date.today()

        self.env.cr.execute("""
            SELECT 
                j.type,
                COALESCE(SUM(m.amount_total), 0) AS total_amount
            FROM 
                account_move m
            JOIN 
                account_journal j ON m.journal_id = j.id
            WHERE 
                m.move_type = 'out_invoice'
                AND m.state = 'posted'
                AND m.invoice_date = %s
            GROUP BY 
                j.type
        """, (today,))

        results = self.env.cr.dictfetchall()

        today_cash = 0
        today_bank = 0
        today_online = 0

        for rec in results:
            if rec['type'] == 'cash':
                today_cash = rec['total_amount']
            elif rec['type'] == 'bank':
                today_bank = rec['total_amount']
            else:
                today_online = rec['total_amount']

        today_total = today_cash + today_bank + today_online

        print('333333333333333333',total_paid)
        print('333333333333333333',total_income_amount)

        return {
            'total_fees_count': len(fees_lines),
            'open_invoice': len(open_fee_lines),
            'paid_invoice': len(paid_fee_lines),
            'income': total_income_amount,
            'expense': expense,
            'application_fees': total_paid,
            'currency_symbol': self.env.company.currency_id.symbol,
            'unreconcile_items': len(overdue_fee_lines),
            'journal_data': journal_data,
            # Today's Summary
            'today_cash': today_cash,
            'today_bank': today_bank,
            'today_online': today_online,
            'today_total': today_total,
        }

    @api.model
    def get_income_chart(self, income):
        """ Getting datas for income expense and profit chart based on current month and year """
        if income == 'income_this_month':
            query_income = """ select sum(debit)-sum(credit) as income ,cast(to_char(account_move_line.date, 'DD')as int)
                            as date , account_type from account_move_line , account_account
                            where account_move_line.account_id=account_account.id AND account_type='income' AND Extract(month FROM account_move_line.date) = Extract(month FROM DATE(NOW()))  
                            AND Extract(YEAR FROM account_move_line.date) = Extract(YEAR FROM DATE(NOW())) group by account_type,date """
            self._cr.execute(query_income)
            record = self._cr.dictfetchall()
            query_expense = """ select sum(debit)-sum(credit) as expense ,cast(to_char(account_move_line.date, 'DD')as int)
                            as date , account_type from account_move_line , account_account where  
                            account_move_line.account_id=account_account.id AND account_type='expense' AND Extract(month FROM account_move_line.date) = Extract(month FROM DATE(NOW()))  
                            AND Extract(YEAR FROM account_move_line.date) = Extract(YEAR FROM DATE(NOW())) group by account_type,date """
            self._cr.execute(query_expense)
            result = self._cr.dictfetchall()

            now = fields.Date.today()
            last_day = calendar.monthrange(now.year, now.month)[1]
            day_list = list(range(1, last_day + 1))
            records = []
            for date in day_list:
                last_month_inc = list(
                    filter(lambda m: m['date'] == date, record))
                last_month_exp = list(
                    filter(lambda m: m['date'] == date, result))
                if not last_month_inc and not last_month_exp:
                    records.append({
                        'date': date,
                        'income': 0.0,
                        'expense': 0.0,
                        'profit': 0.0
                    })
                elif (not last_month_inc) and last_month_exp:
                    last_month_exp[0].update({
                        'income': 0.0,
                        'expense': -1 * last_month_exp[0]['expense'] if
                        last_month_exp[0]['expense'] < 1 else
                        last_month_exp[0]['expense']
                    })
                    last_month_exp[0].update({
                        'profit': last_month_exp[0]['income'] -
                                  last_month_exp[0]['expense']
                    })
                    records.append(last_month_exp[0])
                elif (not last_month_exp) and last_month_inc:
                    last_month_inc[0].update({
                        'expense': 0.0,
                        'income': -1 * last_month_inc[0]['income'] if
                        last_month_inc[0]['income'] < 1 else
                        last_month_inc[0]['income']
                    })
                    last_month_inc[0].update({
                        'profit': last_month_inc[0]['income'] -
                                  last_month_inc[0]['expense']
                    })
                    records.append(last_month_inc[0])
                else:
                    last_month_inc[0].update({
                        'income': -1 * last_month_inc[0]['income'] if
                        last_month_inc[0]['income'] < 1 else
                        last_month_inc[0]['income'],
                        'expense': -1 * last_month_exp[0]['expense'] if
                        last_month_exp[0]['expense'] < 1 else
                        last_month_exp[0]['expense']
                    })
                    last_month_inc[0].update({
                        'profit': last_month_inc[0]['income'] -
                                  last_month_inc[0]['expense']
                    })
                    records.append(last_month_inc[0])
            income = []
            expense = []
            date = []
            profit = []
            for rec in records:
                income.append(rec['income'])
                expense.append(rec['expense'])
                date.append(rec['date'])
                profit.append(rec['profit'])
            return {
                'income': income,
                'expense': expense,
                'date': date,
                'profit': profit
            }
        elif income == 'income_this_year':
            query_income = """ select sum(debit)-sum(credit) as income ,to_char(account_move_line.date, 'Month')  as month ,
                            account_type from account_move_line ,account_account
                            where account_move_line.account_id=account_account.id AND account_type = 'income' 
                            AND to_char(DATE(NOW()), 'YY') = to_char(account_move_line.date, 'YY')
                            group by account_type,month """
            self._cr.execute(query_income)
            record = self._cr.dictfetchall()
            query_expense = """ select sum(debit)-sum(credit) as expense ,to_char(account_move_line.date, 'Month')  as month ,
                            account_type from account_move_line , account_account where 
                            account_move_line.account_id=account_account.id AND account_type = 'expense'
                            AND to_char(DATE(NOW()), 'YY') = to_char(account_move_line.date, 'YY')
                            group by account_type,month """
            self._cr.execute(query_expense)
            result = self._cr.dictfetchall()

            month_list = calendar.month_name[1:]
            records = []
            for month in month_list:
                last_month_inc = list(
                    filter(lambda m: m['month'].strip() == month, record))
                last_month_exp = list(
                    filter(lambda m: m['month'].strip() == month, result))
                if not last_month_inc and not last_month_exp:
                    records.append({
                        'month': month,
                        'income': 0.0,
                        'expense': 0.0,
                        'profit': 0.0,
                    })
                elif (not last_month_inc) and last_month_exp:
                    last_month_exp[0].update({
                        'income': 0.0,
                        'expense': -1 * last_month_exp[0]['expense'] if
                        last_month_exp[0]['expense'] < 1 else
                        last_month_exp[0]['expense']
                    })
                    last_month_exp[0].update({
                        'profit': last_month_exp[0]['income'] -
                                  last_month_exp[0]['expense']
                    })
                    records.append(last_month_exp[0])
                elif (not last_month_exp) and last_month_inc:
                    last_month_inc[0].update({
                        'expense': 0.0,
                        'income': -1 * last_month_inc[0]['income'] if
                        last_month_inc[0]['income'] < 1 else
                        last_month_inc[0]['income']
                    })
                    last_month_inc[0].update({
                        'profit': last_month_inc[0]['income'] -
                                  last_month_inc[0]['expense']
                    })
                    records.append(last_month_inc[0])
                else:
                    last_month_inc[0].update({
                        'income': -1 * last_month_inc[0]['income'] if
                        last_month_inc[0]['income'] < 1 else
                        last_month_inc[0]['income'],
                        'expense': -1 * last_month_exp[0]['expense'] if
                        last_month_exp[0]['expense'] < 1 else
                        last_month_exp[0]['expense']
                    })
                    last_month_inc[0].update({
                        'profit': last_month_inc[0]['income'] -
                                  last_month_inc[0]['expense']
                    })
                    records.append(last_month_inc[0])
            income = []
            expense = []
            month = []
            profit = []
            for rec in records:
                income.append(rec['income'])
                expense.append(rec['expense'])
                month.append(rec['month'])
                profit.append(rec['profit'])
            return {
                'income': income,
                'expense': expense,
                'date': month,
                'profit': profit,
            }

    @api.model
    def get_payment_data(self, payment_list_filter, payment_data_filter):
        """Getting datas for customer payment list and vendor payment list based on current year and month"""
        today = fields.Date.today()
        year = today.year
        month = today.month
        last_day = calendar.monthrange(year, month)[1]

        if payment_list_filter == 'customer_payment':
            if payment_data_filter == 'this_month':
                start_date = f"{year}-{month:02d}-01"
                end_date = f"{year}-{month:02d}-{last_day:02d}"
                invoices = self.search([
                    ('move_type', '=', 'out_invoice'),
                    ('payment_state', '=', 'paid'),
                    ('invoice_date', '>=', start_date),
                    ('invoice_date', '<=', end_date),
                ])
            else:
                start_date = f"{year}-01-01"
                end_date = f"{year}-12-31"
                invoices = self.search([
                    ('move_type', '=', 'out_invoice'),
                    ('payment_state', '=', 'paid'),
                    ('invoice_date', '>=', start_date),
                    ('invoice_date', '<=', end_date),
                ])

            result = []
            for i in invoices:
                result.append({
                    'id': i.id,
                    'partner': i.partner_id.name,
                    'amount': i.amount_total,
                    'date': str(i.invoice_date),
                })
            return result

        else:
            if payment_data_filter == 'this_month':
                start_date = f"{year}-{month:02d}-01"
                end_date = f"{year}-{month:02d}-{last_day:02d}"
                vendor_bills = self.search([
                    ('move_type', '=', 'in_invoice'),
                    ('payment_state', '=', 'paid'),
                    ('invoice_date', '>=', start_date),
                    ('invoice_date', '<=', end_date),
                ])
            else:
                start_date = f"{year}-01-01"
                end_date = f"{year}-12-31"
                vendor_bills = self.search([
                    ('move_type', '=', 'in_invoice'),
                    ('payment_state', '=', 'paid'),
                    ('invoice_date', '>=', start_date),
                    ('invoice_date', '<=', end_date),
                ])

            result = []
            for i in vendor_bills:
                result.append({
                    'id': i.id,
                    'partner': i.partner_id.name,
                    'amount': i.amount_total,
                    'date': str(i.invoice_date),
                })
            return result

    @api.model
    def get_top_datas(self, top_filter):
        """Getting datas for top customer and top vendors based on current month and current year"""
        today = fields.Date.today()
        year = today.year
        month = today.month
        last_day = calendar.monthrange(year, month)[1]

        if top_filter == 'this_month':
            start_date = f"{year}-{month:02d}-01"
            end_date = f"{year}-{month:02d}-{last_day:02d}"
            vendor_bills = self.search([
                ('move_type', '=', 'in_invoice'),
                ('invoice_date', '>=', start_date),
                ('invoice_date', '<=', end_date),
            ])
            customer_invoices = self.search([
                ('move_type', '=', 'out_invoice'),
                ('invoice_date', '>=', start_date),
                ('invoice_date', '<=', end_date),
            ])
        else:
            start_date = f"{year}-01-01"
            end_date = f"{year}-12-31"
            vendor_bills = self.search([
                ('move_type', '=', 'in_invoice'),
                ('invoice_date', '>=', start_date),
                ('invoice_date', '<=', end_date),
            ])
            customer_invoices = self.search([
                ('move_type', '=', 'out_invoice'),
                ('invoice_date', '>=', start_date),
                ('invoice_date', '<=', end_date),
            ])

        vendor_partners = vendor_bills.mapped('partner_id')
        top_vendors = []
        for vendor in vendor_partners:
            top_vendors.append({
                'id': vendor.id,
                'name': vendor.name,
            })

        customer_partners = customer_invoices.mapped('partner_id')
        top_customers = []
        for customer in customer_partners:
            top_customers.append({
                'id': customer.id,
                'name': customer.name,
            })

        return {
            'top_vendors': top_vendors,
            'top_customers': top_customers,
        }

    @api.model
    def get_aged_payable(self, aged_filter, aged_payable_filter):
        """ Getting Datas for aged payable and aged receivable chart based on current month and year"""
        if aged_filter == 'aged_receive':
            if aged_payable_filter == 'this_month':
                self._cr.execute(""" select to_char(account_move.date, 'Month') as month, res_partner.name as due_partner, account_move.partner_id as parent,
                                   sum(account_move.amount_total) as amount from account_move, res_partner where account_move.partner_id = res_partner.id
                                   AND account_move.move_type = 'out_invoice'
                                   AND payment_state = 'not_paid'
                                   AND Extract(month FROM account_move.invoice_date_due) = Extract(month FROM DATE(NOW()))
                                   AND Extract(YEAR FROM account_move.invoice_date_due) = Extract(YEAR FROM DATE(NOW()))
                                   AND account_move.partner_id = res_partner.commercial_partner_id
                                   group by parent, due_partner, month
                                   order by amount desc""")
            else:
                self._cr.execute("""select  res_partner.name as due_partner, account_move.partner_id as parent,
                                                sum(account_move.amount_total) as amount from account_move, res_partner where account_move.partner_id = res_partner.id
                                                AND account_move.move_type = 'out_invoice'
                                                AND payment_state = 'not_paid'
                                                AND Extract(YEAR FROM account_move.invoice_date_due) = Extract(YEAR FROM DATE(NOW()))
                                                AND account_move.partner_id = res_partner.commercial_partner_id
                                                group by parent, due_partner
                                                order by amount desc""")
            record = self._cr.dictfetchall()
            partner = [item['due_partner'] for item in record]
            amount = [item['amount'] for item in record]
            return {'partner': partner,
                    'amount': amount, }
        else:
            if aged_payable_filter == 'this_month':
                self._cr.execute("""select to_char(account_move.date, 'Month') as month, res_partner.name as bill_partner, account_move.partner_id as parent,
                                sum(account_move.amount_total) as amount from account_move, res_partner where account_move.partner_id = res_partner.id
                                AND account_move.move_type = 'in_invoice'
                                AND payment_state = 'not_paid'
                                AND Extract(month FROM account_move.invoice_date_due) = Extract(month FROM DATE(NOW()))
                                AND Extract(YEAR FROM account_move.invoice_date_due) = Extract(YEAR FROM DATE(NOW()))
                                AND account_move.partner_id = res_partner.commercial_partner_id
                                group by parent, bill_partner, month
                                order by amount desc""")
            else:
                self._cr.execute("""select to_char(account_move.date, 'Month') as month, res_partner.name as bill_partner, account_move.partner_id as parent,
                                sum(account_move.amount_total) as amount from account_move, res_partner where account_move.partner_id = res_partner.id
                                AND account_move.move_type = 'in_invoice'
                                AND payment_state = 'not_paid'
                                AND Extract(YEAR FROM account_move.invoice_date_due) = Extract(YEAR FROM DATE(NOW()))
                                AND account_move.partner_id = res_partner.commercial_partner_id
                                group by parent, bill_partner, month
                                order by amount desc""")
            record = self._cr.dictfetchall()
            partner = [item['bill_partner'] for item in record]
            amount = [item['amount'] for item in record]
            return {'partner': partner,
                    'amount': amount, }

    @api.model
    def get_sale_revenue(self, top_sale_cust_filter):
        """ Getting datas for top 10 sale revenue customer based on current month and year """
        query = """ SELECT partner_id as customer_id, MAX(res_partner.name) as customer , SUM(amount_total_signed) as total_amount
                    FROM account_move JOIN res_partner ON account_move.partner_id = res_partner.id
                    WHERE move_type = 'out_invoice' """
        if top_sale_cust_filter == 'this_month':
            query += """AND Extract(month FROM account_move.invoice_date) = Extract(month FROM DATE(NOW()))
                        AND Extract(YEAR FROM account_move.invoice_date) = Extract(YEAR FROM DATE(NOW()))
                        GROUP BY partner_id
                        ORDER BY total_amount DESC LIMIT 10 """
            self._cr.execute(query)
        else:
            query += """AND Extract(YEAR FROM account_move.invoice_date) = Extract(YEAR FROM DATE(NOW()))
                        GROUP BY partner_id
                        ORDER BY total_amount DESC LIMIT 10"""
            self._cr.execute(query)
        records = self._cr.dictfetchall()
        return records

    @api.model
    def get_bank_balance(self):
        """ Getting data for bank and cash balance """
        self._cr.execute("""select account_account.name as name, sum(balance) as balance,
                            min(account_account.id) as id from account_move_line left join
                            account_account on account_account.id = account_move_line.account_id where
                            account_account.account_type = 'asset_cash'
                            group by account_account.name""")
        records = self._cr.dictfetchall()
        return records
