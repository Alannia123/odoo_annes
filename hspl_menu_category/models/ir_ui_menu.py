from odoo import fields, models


class IrUiMenu(models.Model):
    _inherit = "ir.ui.menu"

    category_id = fields.Many2one("ir.ui.menu.category", string="Category")

    def load_web_menus(self, debug):
        web_menus = super().load_web_menus(debug)

        menu_ids = [menu_id for menu_id in web_menus if menu_id != "root"]
        if not menu_ids:
            return web_menus

        menu_data = {
            menu["id"]: menu["category_id"]
            for menu in self.browse(menu_ids).read(["category_id"])
        }

        for menu_id, values in web_menus.items():
            if menu_id == "root":
                values["category_id"] = False
            else:
                values["category_id"] = menu_data.get(menu_id, False)

        return web_menus