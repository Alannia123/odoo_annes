/* Copyright 2023 Taras Shabaranskyi
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl). */

import {Component, xml, useState} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {user} from "@web/core/user";

class AppsMenuPreferences extends Component {
    setup() {
        this.action = useService("action");
        this.user = user;

        // reactive state
        this.state = useState({ isAdmin: false });
    }

    async loadGroups() {
        try {
            this.state.isAdmin = await this.user.hasGroup("base.group_system");
        } catch (e) {
            console.error("Group check failed:", e);
        }
    }

    async _onClick() {
        const onClose = () => this.action.doAction("reload_context");
        const action = await this.action.loadAction(
            "web_responsive.res_users_view_form_apps_menu_preferences_action"
        );
        this.action.doAction({...action, res_id: this.user.userId}, {onClose}).then();
    }
    async _onrefreshClick() {
        this.action.doAction({ type: "ir.actions.client", tag: "reload" });
    }
}

AppsMenuPreferences.template = xml`

    <div class="o-dropdown dropdown o-dropdown--no-caret">
        <button
            role="button"
            type="button"
            title="Refresh"
            class="dropdown-toggle o-dropdown--narrow"
            t-on-click="_onrefreshClick">
                <i class="fa fa-refresh fa-lg px-1"/>
        </button>
    </div>
    
    <div class="o-dropdown dropdown o-dropdown--no-caret" t-if="state.isAdmin">
        <button
            role="button"
            type="button"
            title="App Menu Preferences"
            class="dropdown-toggle o-dropdown--narrow"
            t-on-click="_onClick">
                <i class="fa fa-tint fa-lg px-1"/>
        </button>
    </div>
`;

registry
    .category("systray")
    .add("AppMenuTheme", {Component: AppsMenuPreferences}, {sequence: 100});
