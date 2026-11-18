









(function () {
    'use strict';

    if (window.__flexWebToAE) return;
    window.__flexWebToAE = true;

    var DEFAULTS = {
        showButton: true,
        fullPage: true,
        images: true,
        splitLines: false,
        corner: 'br',
        offset: { x: 24, y: 24 }
    };

    var settings = Object.assign({}, DEFAULTS);
    var ui = null;
    var busy = false;
    var connected = null;      

    

    function load(cb) {
        try {
            chrome.storage.local.get(DEFAULTS, function (v) {
                if (!chrome.runtime.lastError && v) settings = Object.assign({}, DEFAULTS, v);
                cb && cb();
            });
        } catch (e) { cb && cb(); }
    }

    function save() {
        try { chrome.storage.local.set(settings); } catch (e) { }
    }

    

    var CSS = [
        ':host{all:initial}',
        '.wrap{position:fixed;z-index:2147483600;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;',
        '-webkit-font-smoothing:antialiased;user-select:none}',
        '.pill{display:flex;align-items:center;gap:9px;height:40px;padding:0 16px 0 13px;border-radius:20px;',
        'background:linear-gradient(135deg,#1d1e26 0%,#14151b 100%);color:#f0f0f5;border:1px solid rgba(255,255,255,.13);',
        'box-shadow:0 8px 28px rgba(0,0,0,.45),0 2px 6px rgba(0,0,0,.3);cursor:pointer;',
        'font-size:12.5px;font-weight:650;letter-spacing:.2px;white-space:nowrap;transition:transform .16s,border-color .16s,box-shadow .16s}',
        '.pill:hover{transform:translateY(-1px);border-color:rgba(0,255,85,.55);box-shadow:0 12px 34px rgba(0,0,0,.5)}',
        '.pill:active{transform:translateY(0)}',
        '.pill.busy{cursor:progress;opacity:.9}',
        '.pill.ok{border-color:rgba(0,255,85,.6)}',
        '.pill.err{border-color:rgba(255,91,91,.65)}',
        '.mark{width:20px;height:20px;flex:0 0 20px;border-radius:6px;display:flex;align-items:center;justify-content:center;',
        'background:linear-gradient(135deg,#00ff55,#00b33c)}',
        '.mark svg{width:12px;height:12px;fill:#0b1200;display:block}',
        '.dot{width:6px;height:6px;border-radius:50%;background:#5a5a64;flex:0 0 6px;margin-left:2px;transition:background .2s}',
        '.dot.on{background:#00ff55;box-shadow:0 0 8px rgba(0,255,85,.8)}',
        '.dot.off{background:#ff5b5b}',
        '.caret{width:22px;height:40px;margin-left:-6px;margin-right:-8px;display:flex;align-items:center;justify-content:center;',
        'cursor:pointer;opacity:.55}',
        '.caret:hover{opacity:1}',
        '.caret svg{width:9px;height:9px;fill:currentColor}',
        '.spin{animation:flexspin .8s linear infinite}',
        '@keyframes flexspin{to{transform:rotate(360deg)}}',

        '.menu{position:absolute;bottom:52px;right:0;width:230px;padding:8px;border-radius:14px;',
        'background:rgba(20,21,27,.98);border:1px solid rgba(255,255,255,.12);box-shadow:0 16px 44px rgba(0,0,0,.55);',
        'color:#d8d8e0;font-size:12px;display:none}',
        '.menu.open{display:block}',
        '.menu h4{margin:2px 4px 8px;font-size:9.5px;font-weight:700;letter-spacing:.8px;text-transform:uppercase;color:#7a7a88}',
        '.opt{display:flex;align-items:center;gap:9px;padding:7px 8px;border-radius:9px;cursor:pointer}',
        '.opt:hover{background:rgba(255,255,255,.06)}',
        '.opt input{accent-color:#00ff55;width:13px;height:13px;margin:0}',
        '.opt span{flex:1}',
        '.foot{margin:6px 4px 2px;font-size:10px;color:#6b6b78;line-height:1.45}',
        '.hint{color:#00ff55;text-decoration:none}'
    ].join('');

    var MARK = '<svg viewBox="0 0 24 24"><path d="M4 3h16v3.2H8.6v4.1H19v3.2H8.6V21H4z"/></svg>';
    var CARET = '<svg viewBox="0 0 10 6"><path d="M0 0l5 6 5-6z"/></svg>';
    var SPIN = '<svg viewBox="0 0 24 24" class="spin"><path d="M12 2a10 10 0 0 1 10 10h-3a7 7 0 0 0-7-7z"/></svg>';

    function mountButton() {
        if (ui || !document.body) return;

        var host = document.createElement('div');
        host.id = 'flex-web-to-ae';
        host.setAttribute('data-flex-ignore', '1');
        
        host.style.cssText = 'all:initial;position:static';

        var sr = host.attachShadow ? host.attachShadow({ mode: 'open' }) : null;
        if (!sr) return;

        var style = document.createElement('style');
        style.textContent = CSS;
        sr.appendChild(style);

        var wrap = document.createElement('div');
        wrap.className = 'wrap';
        wrap.innerHTML =
            '<div class="menu" part="menu">' +
            '  <h4>Capture</h4>' +
            '  <label class="opt"><input type="checkbox" data-k="fullPage"><span>Full page (scrolls first)</span></label>' +
            '  <label class="opt"><input type="checkbox" data-k="images"><span>Include images &amp; icons</span></label>' +
            '  <label class="opt"><input type="checkbox" data-k="splitLines"><span>One layer per text line</span></label>' +
            '  <label class="opt"><input type="checkbox" data-k="showButton"><span>Show this button</span></label>' +
            '  <div class="foot" id="foot">Alt+Shift+A sends without the button.</div>' +
            '</div>' +
            '<div style="display:flex;align-items:center">' +
            '  <div class="pill" id="pill">' +
            '    <span class="mark">' + MARK + '</span>' +
            '    <span id="label">Send to AE</span>' +
            '    <span class="dot" id="dot"></span>' +
            '    <span class="caret" id="caret">' + CARET + '</span>' +
            '  </div>' +
            '</div>';
        sr.appendChild(wrap);

        (document.body || document.documentElement).appendChild(host);

        ui = {
            host: host, wrap: wrap,
            pill: sr.getElementById('pill'),
            label: sr.getElementById('label'),
            dot: sr.getElementById('dot'),
            caret: sr.getElementById('caret'),
            menu: wrap.querySelector('.menu'),
            foot: sr.getElementById('foot'),
            mark: wrap.querySelector('.mark')
        };

        place();
        syncMenu();

        ui.pill.addEventListener('click', function (e) {
            if (e.target.closest('.caret')) return;
            if (dragged) return;
            send('button');
        });

        ui.caret.addEventListener('click', function (e) {
            e.stopPropagation();
            ui.menu.classList.toggle('open');
            if (ui.menu.classList.contains('open')) ping();
        });

        wrap.querySelectorAll('.opt input').forEach(function (inp) {
            inp.addEventListener('change', function () {
                settings[inp.getAttribute('data-k')] = inp.checked;
                save();
                if (inp.getAttribute('data-k') === 'showButton' && !inp.checked) {
                    ui.menu.classList.remove('open');
                    setVisible(false);
                }
            });
        });

        document.addEventListener('click', function (e) {
            if (!ui) return;
            if (e.target === ui.host) return;
            ui.menu.classList.remove('open');
        }, true);

        makeDraggable();
        setVisible(settings.showButton);
        ping();
    }

    function place() {
        if (!ui) return;
        var o = settings.offset || DEFAULTS.offset;
        var w = ui.wrap.style;
        w.top = w.bottom = w.left = w.right = 'auto';
        if (settings.corner === 'br') { w.right = o.x + 'px'; w.bottom = o.y + 'px'; }
        else if (settings.corner === 'bl') { w.left = o.x + 'px'; w.bottom = o.y + 'px'; }
        else if (settings.corner === 'tr') { w.right = o.x + 'px'; w.top = o.y + 'px'; }
        else { w.left = o.x + 'px'; w.top = o.y + 'px'; }
        ui.menu.style.right = /r$/.test(settings.corner) ? '0' : 'auto';
        ui.menu.style.left = /l$/.test(settings.corner) ? '0' : 'auto';
        ui.menu.style.bottom = /^b/.test(settings.corner) ? '52px' : 'auto';
        ui.menu.style.top = /^t/.test(settings.corner) ? '52px' : 'auto';
    }

    function syncMenu() {
        if (!ui) return;
        ui.wrap.querySelectorAll('.opt input').forEach(function (inp) {
            inp.checked = !!settings[inp.getAttribute('data-k')];
        });
    }

    function setVisible(on) {
        if (!ui) return;
        ui.wrap.style.display = on ? 'block' : 'none';
    }

    

    var dragged = false;
    function makeDraggable() {
        var startX = 0, startY = 0, moved = 0, dragging = false;

        ui.pill.addEventListener('mousedown', function (e) {
            if (e.target.closest('.caret')) return;
            dragging = true; moved = 0; dragged = false;
            startX = e.clientX; startY = e.clientY;
            e.preventDefault();
        });

        window.addEventListener('mousemove', function (e) {
            if (!dragging) return;
            moved = Math.abs(e.clientX - startX) + Math.abs(e.clientY - startY);
            if (moved < 5) return;
            dragged = true;
            var w = ui.wrap.style;
            w.top = (e.clientY - 20) + 'px'; w.left = (e.clientX - 60) + 'px';
            w.right = w.bottom = 'auto';
        });

        window.addEventListener('mouseup', function (e) {
            if (!dragging) return;
            dragging = false;
            if (!dragged) return;
            settings.corner = (e.clientY > window.innerHeight / 2 ? 'b' : 't') +
                (e.clientX > window.innerWidth / 2 ? 'r' : 'l');
            settings.offset = {
                x: Math.max(12, Math.min(window.innerWidth - 200, /r$/.test(settings.corner)
                    ? window.innerWidth - e.clientX - 60 : e.clientX - 60)),
                y: Math.max(12, /^b/.test(settings.corner) ? window.innerHeight - e.clientY - 20 : e.clientY - 20)
            };
            save();
            place();
            setTimeout(function () { dragged = false; }, 0);
        });
    }

    function setState(kind, text) {
        if (!ui) return;
        ui.pill.classList.remove('busy', 'ok', 'err');
        if (kind === 'busy') ui.pill.classList.add('busy');
        if (kind === 'ok') ui.pill.classList.add('ok');
        if (kind === 'err') ui.pill.classList.add('err');
        ui.label.textContent = text;
        ui.mark.innerHTML = kind === 'busy' ? SPIN : MARK;
    }

    function setConnected(on, detail) {
        connected = on;
        if (!ui) return;
        ui.dot.classList.toggle('on', !!on);
        ui.dot.classList.toggle('off', on === false);
        ui.foot.textContent = on
            ? 'After Effects panel connected. Alt+Shift+A sends without the button.'
            : 'Open Flex GUI Pro in After Effects and switch to WEB TO AE. ' + (detail || '');
    }

    

    function bg(msg, cb) {
        try {
            chrome.runtime.sendMessage(msg, function (res) {
                if (chrome.runtime.lastError) { cb && cb({ ok: false, error: chrome.runtime.lastError.message }); return; }
                cb && cb(res || { ok: false, error: 'no response' });
            });
        } catch (e) { cb && cb({ ok: false, error: String(e && e.message || e) }); }
    }

    function ping() {
        bg({ type: 'flex-ping' }, function (res) { setConnected(!!(res && res.ok), res && res.error); });
    }

    

    function send(source) {
        if (busy) return;
        if (!window.FlexWebCapture) { setState('err', 'Engine missing'); return; }
        busy = true;
        setState('busy', settings.fullPage ? 'Scanning page…' : 'Capturing…');

        var opts = {
            viewportOnly: !settings.fullPage,
            images: settings.images,
            splitLines: settings.splitLines
        };

        window.FlexWebCapture.prepare(opts, function () {
            setState('busy', 'Reading layers…');
            var payload;
            try {
                payload = window.FlexWebCapture.capture(opts);
            } catch (e) {
                busy = false;
                setState('err', 'Capture failed');
                reset(2600);
                return;
            }
            payload.source = source || 'button';
            var count = payload.nodes.length;
            setState('busy', 'Sending ' + count + ' layers…');

            bg({ type: 'flex-capture', payload: payload }, function (res) {
                busy = false;
                if (res && res.ok) {
                    setConnected(true);
                    setState('ok', 'Sent ' + count + ' layers');
                } else {
                    setConnected(false, (res && res.error) || '');
                    setState('err', shortError(res && res.error));
                }
                reset(3000);
            });
        });
    }

    function shortError(e) {
        e = String(e || 'Send failed');
        if (/failed to fetch|refused|ECONNREFUSED|network/i.test(e)) return 'AE not connected';
        return e.length > 26 ? e.slice(0, 26) + '…' : e;
    }

    function reset(ms) {
        setTimeout(function () { if (!busy) setState('idle', 'Send to AE'); }, ms);
    }

    
    chrome.runtime.onMessage.addListener(function (msg, sender, respond) {
        if (!msg) return;
        if (msg.type === 'flex-send') { send(msg.source || 'command'); respond({ ok: true }); return true; }
        if (msg.type === 'flex-toggle-button') {
            settings.showButton = !settings.showButton;
            save();
            if (!ui && settings.showButton) mountButton();
            setVisible(settings.showButton);
            syncMenu();
            respond({ ok: true, shown: settings.showButton });
            return true;
        }
        if (msg.type === 'flex-settings-changed') {
            load(function () { syncMenu(); place(); setVisible(settings.showButton); });
            respond({ ok: true });
            return true;
        }
        if (msg.type === 'flex-status') {
            respond({ ok: true, connected: connected, busy: busy, url: location.href });
            return true;
        }
        return false;
    });

    load(function () {
        if (settings.showButton) mountButton();
        else ping();
    });
}());
