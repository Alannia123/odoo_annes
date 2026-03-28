/** @odoo-module **/

import { ImageField } from "@web/views/fields/image/image_field";
import { registry } from "@web/core/registry";

export class CameraImageField extends ImageField {

    _onFileInputChange(ev) {
        const input = ev.target;
        if (input) {
            input.setAttribute("accept", "image/*");
            input.setAttribute("capture", "environment"); // back camera
        }
        super._onFileInputChange(ev);
    }
}

// Register custom widget (DO NOT override core image)
registry.category("fields").add("camera_image", CameraImageField);
