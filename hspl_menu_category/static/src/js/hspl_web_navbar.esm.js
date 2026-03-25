/** @odoo-module **/

/* eslint-disable no-unused-vars */

import {onWillStart, useState} from "@odoo/owl";
import {NavBar} from "@web/webclient/navbar/navbar";
import {patch} from "@web/core/utils/patch";
import {useService} from "@web/core/utils/hooks";

patch(NavBar.prototype, {
    async setup() {
        super.setup();
        this.orm = useService("orm");

        // Define state
        this.state = useState({
            _ctgs: [],
        });

        // Load menu categories
        this.state._ctgs = await this._loadMenuCategories();
    },

    async _loadMenuCategories() {
        // Fetch data from the server
        const ctgData = await this.orm.call("ir.ui.menu.category", "get_category", []);
        console.log('CATE----------------',ctgData)
        // Map data to the required format
        return ctgData.map((appCtgData) => ({
            ctgID: appCtgData.id,
            name: appCtgData.name,
        }));
    },
});
