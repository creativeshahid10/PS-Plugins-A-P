



(function () {
    'use strict';

    var DEFAULTS = { showButton: true, fullPage: true, images: true, splitLines: false, port: 45327 };
    var $ = function (id) { return document.getElementById(id); };

    function setStatus(state, html) {
        var dot = $('dot');
        dot.classList.toggle('on', state === 'on');
        dot.classList.toggle('off', state === 'off');
        $('status').innerHTML = html;
    }

    function refresh() {
        chrome.runtime.sendMessage({ type: 'flex-ping' }, function (res) {
            if (res && res.ok) {
                setStatus('on', '<b>Connected</b> to Flex GUI Pro' +
                    (res.info && res.info.host ? ' · ' + res.info.host : ''));
                $('send').disabled = false;
            } else {
                setStatus('off', '<b>After Effects not found.</b> Open Flex GUI Pro and switch to the WEB TO AE tab.');
                $('send').disabled = false;   
            }
        });

        chrome.storage.local.get({ lastSend: null }, function (v) {
            if (!v.lastSend) return;
            var ago = Math.round((Date.now() - v.lastSend.at) / 1000);
            var when = ago < 60 ? ago + 's ago' : ago < 3600 ? Math.round(ago / 60) + 'm ago' : Math.round(ago / 3600) + 'h ago';
            $('foot').insertAdjacentHTML('afterbegin',
                'Last send: <b>' + v.lastSend.nodes + ' layers</b>, ' + when + '<br>');
        });
    }

    chrome.storage.local.get(DEFAULTS, function (v) {
        var s = Object.assign({}, DEFAULTS, v);
        document.querySelectorAll('.opt input').forEach(function (inp) {
            inp.checked = !!s[inp.getAttribute('data-k')];
            inp.addEventListener('change', function () {
                var patch = {};
                patch[inp.getAttribute('data-k')] = inp.checked;
                chrome.storage.local.set(patch, notifyTab);
            });
        });
        $('port').value = s.port;
        $('port').addEventListener('change', function () {
            var p = parseInt(this.value, 10);
            if (!(p >= 1024 && p <= 65535)) { this.value = DEFAULTS.port; p = DEFAULTS.port; }
            chrome.storage.local.set({ port: p }, refresh);
        });
    });

    function notifyTab() {
        chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
            if (!tabs || !tabs[0]) return;
            try { chrome.tabs.sendMessage(tabs[0].id, { type: 'flex-settings-changed' }, function () { void chrome.runtime.lastError; }); }
            catch (e) { }
        });
    }

    $('send').addEventListener('click', function () {
        var btn = $('send');
        btn.disabled = true;
        btn.textContent = 'Capturing…';
        chrome.runtime.sendMessage({ type: 'flex-send-active', source: 'popup' }, function (res) {
            if (res && res.ok) {
                btn.textContent = 'Sent to After Effects ✓';
                setStatus('on', '<b>Sent.</b> Build it from the WEB TO AE tab.');
            } else {
                btn.textContent = 'Send this page to After Effects';
                btn.disabled = false;
                setStatus('off', '<b>' + ((res && res.error) || 'Send failed') + '</b>');
            }
        });
    });

    try { $('ver').textContent = chrome.runtime.getManifest().version; } catch (e) { }
    refresh();
}());
