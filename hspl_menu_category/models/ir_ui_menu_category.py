from odoo import api, fields, models


class IrUiMenuCategory(models.Model):
    _name = "ir.ui.menu.category"
    _description = "Menu Category"
    _order = "sequence asc, id asc"

    name = fields.Char(required=True)
    sequence = fields.Integer(
        help="Sequence used when displaying categories on the dashboard."
    )
    menu_id = fields.One2many("ir.ui.menu", "category_id", string="Menu Items")
    group_ids = fields.Many2many(
        "res.groups",
        "menu_allowed_group_rel",
        "category_id",
        "group_id",
        string="Allowed Groups",
        help="Only users belonging to at least one of these groups can see this menu category",
    )

    @api.model
    def get_category(self):
        user = self.env.user

        allowed_groups = self.env["res.groups"]
        group_xmlids = [
            "ala_education_core.group_education_principal",
            "ala_education_core.group_education_office_admin",
            "ala_education_core.group_education_faculty",
        ]

        for xmlid in group_xmlids:
            group = self.env.ref(xmlid, raise_if_not_found=False)
            if group:
                allowed_groups |= group

        domain = [("menu_id", "!=", False)]

        user_allowed_groups = user.group_ids & allowed_groups
        if user_allowed_groups:
            domain += [
                "|",
                ("group_ids", "=", False),
                ("group_ids", "in", user_allowed_groups.ids),
            ]
        else:
            domain += [("group_ids", "=", False)]

        return self.search_read(
            domain,
            fields=["name", "sequence", "menu_id", "group_ids"],
            order="sequence asc, id asc",
        )