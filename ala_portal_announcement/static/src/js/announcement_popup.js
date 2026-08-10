/* Announcement popup - website & portal home pages.
 *
 * Deliberately plain ES5-ish JavaScript with no framework dependency: this runs
 * inside the school's Android WebView as well as desktop browsers, and it must
 * never be the reason a home page fails to render.
 */
(function () {
    "use strict";

    var ROOT_ID = "ala_announcement_root";
    var ENDPOINT = "/ala/announcement/active";
    var KEY_PREFIX = "ala_ann:";

    var root = document.getElementById(ROOT_ID);
    if (!root) {
        return;
    }

    // ------------------------------------------------------------------
    // Storage - degrade quietly when DOM storage is unavailable
    // (private mode, or WebView with setDomStorageEnabled(false)).
    // ------------------------------------------------------------------
    function probe(kind) {
        try {
            var store = window[kind];
            var key = "__ala_probe__";
            store.setItem(key, "1");
            store.removeItem(key);
            return store;
        } catch (err) {
            return null;
        }
    }

    var LOCAL = probe("localStorage");
    var SESSION = probe("sessionStorage");

    function markKey(ann) {
        return KEY_PREFIX + ann.id + ":" + ann.token;
    }

    function readMark(ann) {
        var key = markKey(ann);
        var stores = [SESSION, LOCAL];
        for (var i = 0; i < stores.length; i++) {
            if (!stores[i]) {
                continue;
            }
            try {
                var value = stores[i].getItem(key);
                if (value) {
                    return value;
                }
            } catch (err) {
                /* ignore */
            }
        }
        return null;
    }

    function writeMark(ann, store, value) {
        if (!store) {
            return;
        }
        try {
            store.setItem(markKey(ann), value);
        } catch (err) {
            /* quota exceeded or storage disabled - popup simply reappears */
        }
    }

    function todayStamp() {
        var now = new Date();
        return now.getFullYear() + "-" + (now.getMonth() + 1) + "-" + now.getDate();
    }

    function shouldShow(ann) {
        var mark = readMark(ann);
        if (mark === "perm") {
            return false;
        }
        if (ann.frequency === "always") {
            return true;
        }
        if (!mark) {
            return true;
        }
        if (ann.frequency === "daily") {
            return mark !== todayStamp();
        }
        return false;
    }

    function remember(ann, permanent) {
        if (permanent) {
            writeMark(ann, LOCAL || SESSION, "perm");
            return;
        }
        if (ann.frequency === "session") {
            writeMark(ann, SESSION || LOCAL, "1");
        } else if (ann.frequency === "daily") {
            writeMark(ann, LOCAL || SESSION, todayStamp());
        } else if (ann.frequency === "once") {
            writeMark(ann, LOCAL || SESSION, "1");
        }
    }

    // ------------------------------------------------------------------
    // Labels (translated server-side into the mount point)
    // ------------------------------------------------------------------
    var LABELS = {close: "Close", dontshow: "Do not show this again", fullsize: "Open full size"};
    var labelNodes = root.querySelectorAll(".ala-ann-i18n");
    for (var i = 0; i < labelNodes.length; i++) {
        var key = labelNodes[i].getAttribute("data-key");
        if (key) {
            LABELS[key] = (labelNodes[i].textContent || LABELS[key]).trim();
        }
    }

    // ------------------------------------------------------------------
    // Rendering
    // ------------------------------------------------------------------
    var queue = [];
    var current = null;
    var overlay = null;
    var lastFocused = null;

    function el(tag, className) {
        var node = document.createElement(tag);
        if (className) {
            node.className = className;
        }
        return node;
    }

    function close(permanent) {
        if (!overlay) {
            return;
        }
        if (current) {
            remember(current, permanent === true);
        }
        var node = overlay;
        overlay = null;
        current = null;
        node.classList.remove("is-open");
        document.documentElement.classList.remove("ala-ann-locked");
        window.setTimeout(function () {
            if (node.parentNode) {
                node.parentNode.removeChild(node);
            }
            if (lastFocused && lastFocused.focus) {
                lastFocused.focus();
            }
            showNext();
        }, 180);
    }

    function onKeydown(ev) {
        if (ev.key === "Escape" || ev.keyCode === 27) {
            close(false);
        }
    }

    function build(ann) {
        var wrap = el("div", "ala-ann-overlay");
        wrap.setAttribute("role", "dialog");
        wrap.setAttribute("aria-modal", "true");
        wrap.setAttribute("aria-label", ann.title || LABELS.close);

        var dialog = el("div", "ala-ann-dialog");
        dialog.addEventListener("click", function (ev) {
            ev.stopPropagation();
        });

        var closeBtn = el("button", "ala-ann-close");
        closeBtn.type = "button";
        closeBtn.setAttribute("aria-label", LABELS.close);
        closeBtn.innerHTML = "&#10005;";
        closeBtn.addEventListener("click", function () {
            close(false);
        });
        dialog.appendChild(closeBtn);

        var scroller = el("div", "ala-ann-scroll");

        if (ann.image_url) {
            var figure = el("a", "ala-ann-figure");
            figure.href = ann.image_url;
            figure.target = "_blank";
            figure.rel = "noopener";
            figure.title = LABELS.fullsize;
            var img = el("img", "ala-ann-image");
            img.src = ann.image_url;
            img.alt = ann.image_alt || "";
            img.setAttribute("loading", "eager");
            figure.appendChild(img);
            scroller.appendChild(figure);
        }

        if (ann.title || ann.body) {
            var text = el("div", "ala-ann-text");
            if (ann.title) {
                var heading = el("h2", "ala-ann-title");
                heading.textContent = ann.title;
                text.appendChild(heading);
            }
            if (ann.body) {
                var body = el("div", "ala-ann-body");
                // Server-side sanitised HTML field.
                body.innerHTML = ann.body;
                text.appendChild(body);
            }
            scroller.appendChild(text);
        }

        dialog.appendChild(scroller);

        var footer = el("div", "ala-ann-footer");

        var optOut = el("label", "ala-ann-optout");
        var checkbox = el("input");
        checkbox.type = "checkbox";
        optOut.appendChild(checkbox);
        optOut.appendChild(document.createTextNode(" " + LABELS.dontshow));
        // "once" has no opt-out (it is already one-shot); "always" must show on
        // every page load, so it must not offer a permanent-dismiss either.
        if (ann.frequency !== "once" && ann.frequency !== "always") {
            footer.appendChild(optOut);
        }

        var actions = el("div", "ala-ann-actions");
        if (ann.cta_url && ann.cta_label) {
            var cta = el("a", "ala-ann-cta");
            cta.href = ann.cta_url;
            cta.textContent = ann.cta_label;
            actions.appendChild(cta);
        }
        var dismiss = el("button", "ala-ann-dismiss");
        dismiss.type = "button";
        dismiss.textContent = LABELS.close;
        dismiss.addEventListener("click", function () {
            close(checkbox.checked);
        });
        actions.appendChild(dismiss);
        footer.appendChild(actions);

        dialog.appendChild(footer);
        wrap.appendChild(dialog);
        wrap.addEventListener("click", function () {
            close(checkbox.checked);
        });
        return wrap;
    }

    function showNext() {
        if (overlay) {
            return;
        }
        var ann = null;
        while (queue.length) {
            var candidate = queue.shift();
            if (shouldShow(candidate)) {
                ann = candidate;
                break;
            }
        }
        if (!ann) {
            document.removeEventListener("keydown", onKeydown);
            return;
        }
        current = ann;
        lastFocused = document.activeElement;
        overlay = build(ann);
        document.body.appendChild(overlay);
        document.documentElement.classList.add("ala-ann-locked");
        document.addEventListener("keydown", onKeydown);
        // Next frame, so the opening transition actually runs.
        window.setTimeout(function () {
            if (overlay) {
                overlay.classList.add("is-open");
                var btn = overlay.querySelector(".ala-ann-close");
                if (btn && btn.focus) {
                    btn.focus();
                }
            }
        }, 20);
    }

    // ------------------------------------------------------------------
    // Fetch - XMLHttpRequest for maximum WebView compatibility
    // ------------------------------------------------------------------
    function load() {
        var scope = root.getAttribute("data-scope") || "website";
        var xhr = new XMLHttpRequest();
        xhr.open("GET", ENDPOINT + "?scope=" + encodeURIComponent(scope), true);
        xhr.setRequestHeader("Accept", "application/json");
        xhr.onreadystatechange = function () {
            if (xhr.readyState !== 4 || xhr.status !== 200) {
                return;
            }
            var data;
            try {
                data = JSON.parse(xhr.responseText);
            } catch (err) {
                return;
            }
            queue = (data && data.announcements) || [];
            if (queue.length) {
                showNext();
            }
        };
        try {
            xhr.send();
        } catch (err) {
            /* offline - nothing to show */
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", load);
    } else {
        load();
    }
})();
