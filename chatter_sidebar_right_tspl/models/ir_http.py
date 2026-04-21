from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        session_info = super().session_info()
        session_info["tspl_chatter_sidebar_right_enabled"] = bool(self.env.user.chatter_sidebar_right_enabled)
        return session_info
