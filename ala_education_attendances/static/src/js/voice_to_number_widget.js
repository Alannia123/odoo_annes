/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { CharField } from "@web/views/fields/char/char_field";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

/* ============================================================
   🎤 VOICE TO NUMBER BUTTON
   ============================================================ */

class VoiceToNumberButton extends Component {
    static template = "ala_education_attendances.VoiceToNumberButton";
    static props = ["record", "fieldName"];

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
        recognition.lang = "en-IN"; // 🔒 Fixed language

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

    // 🔁 Toggle mic (click)
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

    // ❌ Error handler
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

    // 🎧 Speech → Numbers
   _onResult(event) {
    let transcript = "";

    for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) {
            transcript += event.results[i][0].transcript;
        }
    }

    if (!transcript) return;

    const converted = this._speechToNumbers(transcript);
    if (!converted) return;

    let current =
        this.props.record.data[this.props.fieldName] || "";

    let updated = current + converted;

    // ✅ Normalize commas
    updated = updated
        .replace(/,+/g, ",")      // remove duplicate commas
        .replace(/^,|,$/g, "");   // no leading/trailing comma

    this.props.record.update({
        [this.props.fieldName]: updated,
    });
}




   _speechToNumbers(text) {
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
        next: "|",   // ⬅ temp separator (important)
    };

    // Word → symbol conversion
    Object.keys(map).forEach((word) => {
        const re = new RegExp(`\\b${word}\\b`, "g");
        t = t.replace(re, map[word]);
    });

    // Keep digits + separator only
    t = t.replace(/[^0-9|]/g, "");

    // Normalize separators → comma
    t = t
        .replace(/\|+/g, ",")    // no multiple separators
        .replace(/^,|,$/g, "");  // no leading/trailing comma

    return t;
}




}

/* ============================================================
   🧾 VOICE TO NUMBER FIELD (Char + Button)
   ============================================================ */

class VoiceToNumberField extends Component {
    static template = "ala_education_attendances.VoiceToNumberField";
    static components = { CharField, VoiceToNumberButton };
    static props = {
        ...standardFieldProps,
    };

    get record() {
        return this.props.record;
    }

    clearText() {
        this.props.record.update({ [this.props.name]: "" });
    }
}

/* ============================================================
   🧩 REGISTER FIELD WIDGET
   ============================================================ */

registry.category("fields").add("voice_to_number", {
    component: VoiceToNumberField,
});
