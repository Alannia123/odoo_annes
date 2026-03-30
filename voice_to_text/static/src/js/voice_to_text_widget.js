/** @odoo-module */

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { TextField } from "@web/views/fields/text/text_field";
import { Component, useState } from "@odoo/owl";

export class VoiceToTextButton extends Component {
    static template = "voice_to_text.VoiceToTextButton";
    static props = {
        record: Object,
        fieldName: String,
        selectedLang: String,
    };

    setup() {
        this.notification = useService("notification");
        this.state = useState({
            isListening: false,
            isError: false,
            recognition: null,
            supported: true,
        });

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            this.state.supported = false;
            return;
        }

        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = false;
        recognition.lang = this.props.selectedLang;

        recognition.onstart = () => {
            this.state.isListening = true;
            this.state.isError = false;
        };

        recognition.onend = () => {
            this.state.isListening = false;
        };

        recognition.onerror = (event) => this.onRecognitionError(event);
        recognition.onresult = (event) => this.onRecognitionResult(event);

        this.state.recognition = recognition;
    }

    toggleRecording(ev) {
        ev.preventDefault();
        ev.stopPropagation();

        if (!this.state.supported) {
            this.notification.add(_t("Speech recognition is not supported in this browser."), {
                type: "warning",
            });
            return;
        }

        if (!this.state.recognition) {
            return;
        }

        try {
            if (this.state.isListening) {
                this.state.recognition.stop();
            } else {
                this.state.recognition.lang = this.props.selectedLang;
                this.state.recognition.start();
            }
        } catch {
            // Browser speech APIs can throw if start/stop is called rapidly.
        }
    }

    onRecognitionError(event) {
        this.state.isError = true;
        this.state.isListening = false;

        let message = _t("Voice recognition failed.");
        if (event.error === "not-allowed") {
            message = _t("Microphone permission denied.");
        } else if (event.error === "no-speech") {
            message = _t("No speech detected.");
        } else if (event.error === "network") {
            message = _t("Speech recognition network error.");
        }

        this.notification.add(message, { type: "danger" });

        try {
            this.state.recognition.stop();
        } catch {
            // no-op
        }
    }

    onRecognitionResult(event) {
        let transcript = "";
        for (let i = event.resultIndex; i < event.results.length; i++) {
            if (event.results[i].isFinal) {
                transcript += event.results[i][0].transcript;
            }
        }

        if (!transcript) {
            return;
        }

        const currentValue = this.props.record.data[this.props.fieldName] || "";
        const nextValue = currentValue ? `${currentValue}\n${transcript.trim()}` : transcript.trim();

        this.props.record.update({
            [this.props.fieldName]: nextValue,
        });
    }
}

export class VoiceToTextField extends Component {
    static template = "voice_to_text.VoiceWidget";
    static components = { TextField, VoiceToTextButton };
    static props = {
        ...standardFieldProps,
    };

    static supportedTypes = ["text", "char"];

    setup() {
        this.state = useState({
            selectedLang: "en-IN",
        });

        this.languages = [
            { code: "en-IN", name: "English (India)" },
            { code: "hi-IN", name: "Hindi / हिंदी" },
            { code: "bn-IN", name: "Bengali / বাংলা" },
            { code: "ta-IN", name: "Tamil / தமிழ்" },
        ];
    }

    get record() {
        return this.props.record;
    }

    clearText(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        this.props.record.update({ [this.props.name]: "" });
    }

    onLangChange(ev) {
        this.state.selectedLang = ev.target.value;
    }
}

registry.category("fields").add("voice_to_text", {
    component: VoiceToTextField,
    displayName: _t("Voice To Text"),
    supportedTypes: ["text", "char"],
});
