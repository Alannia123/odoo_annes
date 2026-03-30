/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useRef, onMounted, onWillUnmount, useState } from "@odoo/owl";

export class CameraCropDialog extends Component {
    static template = "ala_education_core.CameraCropTemplate";

    setup() {
        this.videoRef = useRef("video");
        this.canvasRef = useRef("canvas");
        this.imageContainerRef = useRef("image_container");

        this.state = useState({
            facingMode: "environment",
            captured: false,
        });

        this.cropper = null;
        this.stream = null;
        this.capturedImage = null;

        onMounted(async () => {
            await this.startCamera();
        });

        onWillUnmount(() => {
            this._cleanup();
        });
    }

    async startCamera() {
        this.stopCamera();

        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: this.state.facingMode,
                },
                audio: false,
            });

            if (this.videoRef.el) {
                this.videoRef.el.srcObject = this.stream;
                await this.videoRef.el.play();
            }
        } catch (error) {
            console.error("Camera access denied or unavailable:", error);
            this._notify("Unable to access camera.", "danger");
        }
    }

    stopCamera() {
        if (this.stream) {
            this.stream.getTracks().forEach((track) => track.stop());
            this.stream = null;
        }
    }

    switchCamera() {
        this.state.facingMode =
            this.state.facingMode === "environment" ? "user" : "environment";
        this.startCamera();
    }

    captureImage() {
    const video = this.videoRef.el;
    const canvas = this.canvasRef.el;

    const ctx = canvas.getContext("2d");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0);

    this.stopCamera();
    video.style.display = "none";

    const image = document.createElement("img");
    image.src = canvas.toDataURL("image/png");
    image.style.maxWidth = "100%";
    image.style.marginTop = "10px";

    video.parentNode.appendChild(image);

    // ✅ ADD HERE
    if (!window.Cropper) {
        this._notify("Cropper not loaded.", "danger");
        return;
    }

    this.cropper = new window.Cropper(image, {
        aspectRatio: 1,
        viewMode: 1,
        autoCropArea: 1,
        responsive: true,
    });
}

    retakeImage() {
        this._destroyCropper();
        this._removeCapturedImage();

        if (this.videoRef.el) {
            this.videoRef.el.style.display = "block";
        }

        this.state.captured = false;
        this.startCamera();
    }

    async saveImage() {
        if (!this.cropper) {
            this._notify("Please capture image first.", "warning");
            return;
        }

        try {
            const croppedCanvas = this.cropper.getCroppedCanvas({
                width: 500,
                height: 500,
                imageSmoothingEnabled: true,
                imageSmoothingQuality: "high",
            });

            if (!croppedCanvas) {
                this._notify("Failed to crop image.", "danger");
                return;
            }

            const base64 = croppedCanvas.toDataURL("image/png").split(",")[1];

            await this.env.services.orm.write(
                this.props.model,
                [this.props.record_id],
                { [this.props.field_name]: base64 }
            );

            this._notify("Image saved successfully.", "success");
            this.cancel();

            await this.env.services.action.doAction({
                type: "ir.actions.act_window",
                res_model: this.props.model,
                res_id: this.props.record_id,
                views: [[false, "form"]],
                target: "current",
            });
        } catch (error) {
            console.error("Failed to save image:", error);
            this._notify("Failed to save image.", "danger");
        }
    }

    cancel() {
        this._cleanup();
        if (this.props.close) {
            this.props.close();
        }
    }

    _destroyCropper() {
        if (this.cropper) {
            this.cropper.destroy();
            this.cropper = null;
        }
    }

    _removeCapturedImage() {
        if (this.capturedImage && this.capturedImage.parentNode) {
            this.capturedImage.parentNode.removeChild(this.capturedImage);
        }
        this.capturedImage = null;
    }

    _cleanup() {
        this.stopCamera();
        this._destroyCropper();
        this._removeCapturedImage();
    }

    _notify(message, type = "info") {
        if (this.env.services.notification) {
            this.env.services.notification.add(message, { type });
        } else {
            alert(message);
        }
    }
}

registry.category("actions").add("open_camera_widget", (env, action) => {
    env.services.dialog.add(CameraCropDialog, {
        model: action.params.model,
        record_id: action.params.record_id,
        field_name: action.params.field_name,
    });
});