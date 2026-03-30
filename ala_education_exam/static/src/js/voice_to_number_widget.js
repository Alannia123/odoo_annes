/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { CharField } from "@web/views/fields/char/char_field";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

/* ============================================================
   🎤 VOICE TO ROLL-MARKS BUTTON
   ============================================================ */

class VoiceToMarksButton extends Component {
    static template = "ala_education_exam.VoiceToMarksButton";
    static props = ["record", "fieldName"];

    static props = {
        record: Object,
        fieldName: String,
    };

    setup() {
        this.notification = useService("notification");

        this.state = useState({
            isListening: false,
            recognition: null,
        });

        const SpeechRecognition =
            window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRecognition) {
            console.warn("Speech Recognition not supported");
            return;
        }

        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = false;
        recognition.lang = "en-IN";

        recognition.onstart = () => {
            this.state.isListening = true;
        };

        recognition.onend = () => {
            this.state.isListening = false;
        };

        recognition.onerror = (event) => this._onError(event);
        recognition.onresult = (event) => this._onResult(event);

        this.state.recognition = recognition;
    }

    /* 🔁 Toggle microphone */
    toggleRecording(ev) {
        ev.preventDefault();
        if (!this.state.recognition) return;

        try {
            if (!this.state.isListening) {
                this.state.recognition.start();
            } else {
                this.state.recognition.stop();
            }
        } catch (e) {
            console.warn("Speech toggle failed", e);
        }
    }

    /* ❌ Error handler */
    _onError(event) {
        this.state.isListening = false;

        let msg = _t(`Error: ${event.error}`);
        if (event.error === "not-allowed") {
            msg = _t("Microphone permission denied");
        } else if (event.error === "no-speech") {
            msg = _t("No speech detected");
        }

        this.notification.add(msg, { type: "danger" });
    }

    /* 🎧 Speech → roll-marks */
    _onResult(event) {
        let transcript = "";

        for (let i = event.resultIndex; i < event.results.length; i++) {
            if (event.results[i].isFinal) {
                transcript += " " + event.results[i][0].transcript;
            }
        }

        if (!transcript.trim()) return;

        const converted = this._speechToRollMarks(transcript);
        if (!converted) return;

        let current =
            this.props.record.data[this.props.fieldName] || "";

        let updated = current
            ? `${current},${converted}`
            : converted;

        // Normalize separators
        updated = updated
            .replace(/,{2,}/g, ",")
            .replace(/-{2,}/g, "-")
            .replace(/,\-/g, "-")
            .replace(/^,|,$/g, "");

        this.props.record.update({
            [this.props.fieldName]: updated,
        });
    }

    /* 🧠 CORE CONVERSION LOGIC */
    _speechToRollMarks(text) {
        let t = text.toLowerCase();

        const map = {
            zero: "0",
            one: "1",
            two: "2",
            three: "3",
            four: "4",
            five: "5",
            six: "6",
            seven: "7",
            eight: "8",
            nine: "9",
            ten: "10",
            eleven: "11",
            twelve: "12",
            thirteen: "13",
            fourteen: "14",
            fifteen: "15",
            sixteen: "16",
            seventeen: "17",
            eighteen: "18",
            nineteen: "19",
            twenty: "20",
            thirty: "30",
            forty: "40",
            fifty: "50",
            sixty: "60",
            seventy: "70",
            eighty: "80",
            ninety: "90",

            dash: "-",
            hyphen: "-",
            minus: "-",

            point: ".",
            dot: ".",

            then: ",",
            next: ",",
            comma: ",",
        };

        Object.keys(map).forEach((word) => {
            const re = new RegExp(`\\b${word}\\b`, "g");
            t = t.replace(re, map[word]);
        });

        // Keep digits and separators only
        t = t.replace(/[^0-9,.-]/g, "");

        // Normalize formatting
        t = t
            .replace(/\.{2,}/g, ".")
            .replace(/,{2,}/g, ",")
            .replace(/-{2,}/g, "-")
            .replace(/^,|,$/g, "");

        // Ensure format roll-marks
        if (!t.includes("-")) {
            return "";
        }

        return t;
    }
}

/* ============================================================
   🧾 FIELD (Char + Button)
   ============================================================ */

class VoiceToMarksField extends Component {
    static template = "ala_education_exam.VoiceToMarksField";
    static components = { CharField, VoiceToMarksButton };
    static props = {
        ...standardFieldProps,
    };

    clearText() {
        this.props.record.update({ [this.props.name]: "" });
    }
}

/* ============================================================
   🧩 REGISTER FIELD WIDGET
   ============================================================ */

registry.category("fields").add("voice_to_marks", {
    component: VoiceToMarksField,
});
