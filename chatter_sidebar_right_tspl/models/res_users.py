from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    chatter_sidebar_right_enabled = fields.Boolean(
        string="Lock Chatter on the Right",
        help=("Keep form chatter fixed on the right side for this user on medium "
            "and larger screens. Reload the web client after changing this preference."),)

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + ["chatter_sidebar_right_enabled"]

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + ["chatter_sidebar_right_enabled"]
