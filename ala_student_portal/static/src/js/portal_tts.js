/** @odoo-module **/

function speakText(id) {
    const span = document.getElementById(`speechText_${id}`);
    if (!span) {
        return;
    }

    const text = span.getAttribute("data-speak");
    if (!text) {
        return;
    }

    if (window.AndroidTTS && typeof window.AndroidTTS.speakText === "function") {
        window.AndroidTTS.speakText(text);
        return;
    }

    if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();
        const msg = new SpeechSynthesisUtterance(text);
        msg.lang = "en-US";
        window.speechSynthesis.speak(msg);
    }
}

window.speakText = speakText;
export { speakText };
