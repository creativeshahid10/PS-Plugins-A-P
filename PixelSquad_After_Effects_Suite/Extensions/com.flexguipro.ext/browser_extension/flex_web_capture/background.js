











const DEFAULT_PORT = 45327;
const HOSTS = ['127.0.0.1', 'localhost'];


const MAX_ASSET = 10 * 1024 * 1024;
const MAX_TOTAL = 64 * 1024 * 1024;
const FETCH_TIMEOUT = 12000;
const POST_TIMEOUT = 60000;

async function getPort() {
    try {
        const v = await chrome.storage.local.get({ port: DEFAULT_PORT });
        const p = parseInt(v.port, 10);
        return p >= 1024 && p <= 65535 ? p : DEFAULT_PORT;
    } catch (e) { return DEFAULT_PORT; }
}

function withTimeout(ms) {
    const c = new AbortController();
    const t = setTimeout(() => c.abort(), ms);
    return { signal: c.signal, done: () => clearTimeout(t) };
}



let lastGoodBase = '';

async function bases() {
    const port = await getPort();
    const list = HOSTS.map(h => `http://${h}:${port}`);
    if (lastGoodBase && list.includes(lastGoodBase)) {
        return [lastGoodBase, ...list.filter(b => b !== lastGoodBase)];
    }
    return list;
}

async function ping() {
    for (const base of await bases()) {
        const t = withTimeout(2500);
        try {
            const r = await fetch(base + '/ping', { signal: t.signal, cache: 'no-store' });
            t.done();
            if (!r.ok) continue;
            const j = await r.json();
            if (j && j.app === 'flex-web2ae') { lastGoodBase = base; return { ok: true, info: j, base }; }
        } catch (e) { t.done(); }
    }
    return { ok: false, error: 'No panel listening on port ' + (await getPort()) };
}

function toBase64(buf) {
    const bytes = new Uint8Array(buf);
    let s = '';
    const CH = 0x8000;
    for (let i = 0; i < bytes.length; i += CH) {
        s += String.fromCharCode.apply(null, bytes.subarray(i, i + CH));
    }
    return btoa(s);
}




async function resolveAssets(assets, budget) {
    const out = {};
    const names = Object.keys(assets || {});
    let used = 0, failed = 0;

    for (const name of names) {
        const a = assets[name];
        if (!a) continue;

        if (a.data) {
            const m = /^data:([^;,]+)?(;base64)?,(.*)$/s.exec(a.data);
            if (!m) { failed++; continue; }
            const mime = m[1] || 'application/octet-stream';
            let b64;
            if (m[2]) b64 = m[3];
            else {
                try { b64 = toBase64(new TextEncoder().encode(decodeURIComponent(m[3])).buffer); }
                catch (e) { failed++; continue; }
            }
            const size = Math.floor(b64.length * 0.75);
            if (size > MAX_ASSET || used + size > budget) { failed++; continue; }
            used += size;
            out[name] = { b64, mime, kind: a.kind || 'image' };
            continue;
        }

        if (!a.url) continue;
        const t = withTimeout(FETCH_TIMEOUT);
        try {
            const r = await fetch(a.url, { signal: t.signal, credentials: 'omit', cache: 'force-cache' });
            t.done();
            if (!r.ok) { failed++; continue; }
            const buf = await r.arrayBuffer();
            if (buf.byteLength > MAX_ASSET || used + buf.byteLength > budget) { failed++; continue; }
            used += buf.byteLength;
            const mime = (r.headers.get('content-type') || '').split(';')[0] || 'image/png';
            out[name] = { b64: toBase64(buf), mime, kind: a.kind || 'image' };
        } catch (e) {
            t.done();
            failed++;
        }
    }
    return { assets: out, bytes: used, failed };
}

async function postCapture(payload) {
    const list = await bases();
    let lastErr = 'no bridge';
    const body = JSON.stringify(payload);

    for (const base of list) {
        const t = withTimeout(POST_TIMEOUT);
        try {
            const r = await fetch(base + '/capture', {
                method: 'POST',
                signal: t.signal,
                headers: { 'Content-Type': 'application/json' },
                body
            });
            t.done();
            if (!r.ok) { lastErr = 'panel returned ' + r.status; continue; }
            const j = await r.json();
            if (j && j.ok) { lastGoodBase = base; return j; }
            lastErr = (j && j.error) || 'panel rejected the capture';
        } catch (e) {
            t.done();
            lastErr = /abort/i.test(String(e && e.name)) ? 'panel timed out' : 'AE not connected';
        }
    }
    return { ok: false, error: lastErr };
}

async function handleCapture(payload, sender) {
    const pre = await ping();
    if (!pre.ok) return pre;

    const resolved = await resolveAssets(payload.assets, MAX_TOTAL);
    payload.assets = resolved.assets;
    payload.assetBytes = resolved.bytes;
    payload.assetsFailed = resolved.failed;
    if (sender && sender.tab) {
        payload.tab = { title: sender.tab.title || '', favIcon: sender.tab.favIconUrl || '' };
    }

    const res = await postCapture(payload);
    if (res.ok) {
        flash('✓', '#43e07f');
        chrome.storage.local.set({
            lastSend: { at: Date.now(), url: payload.url, nodes: payload.nodes.length, id: res.id || '' }
        });
    } else {
        flash('!', '#ff5b5b');
    }
    return res;
}

function flash(text, color) {
    try {
        chrome.action.setBadgeText({ text });
        chrome.action.setBadgeBackgroundColor({ color });
        setTimeout(() => chrome.action.setBadgeText({ text: '' }), 2600);
    } catch (e) { }
}



chrome.runtime.onMessage.addListener((msg, sender, respond) => {
    if (!msg || !msg.type) return false;

    if (msg.type === 'flex-ping') {
        ping().then(respond);
        return true;
    }
    if (msg.type === 'flex-capture') {
        handleCapture(msg.payload, sender).then(respond).catch(e => respond({ ok: false, error: String(e && e.message || e) }));
        return true;
    }
    if (msg.type === 'flex-send-active') {
        sendToActiveTab(msg.source || 'popup').then(respond);
        return true;
    }
    return false;
});

async function sendToActiveTab(source) {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab || !tab.id) return { ok: false, error: 'no active tab' };
    if (/^(chrome|edge|about|devtools|chrome-extension):/i.test(tab.url || '')) {
        return { ok: false, error: 'This page cannot be captured by a browser extension.' };
    }
    try {
        return await chrome.tabs.sendMessage(tab.id, { type: 'flex-send', source });
    } catch (e) {
        
        try {
            await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ['capture_engine.js', 'content.js'] });
            return await chrome.tabs.sendMessage(tab.id, { type: 'flex-send', source });
        } catch (e2) {
            return { ok: false, error: 'Reload the page, then try again.' };
        }
    }
}

chrome.commands.onCommand.addListener(async (cmd) => {
    if (cmd === 'send-to-ae') { sendToActiveTab('shortcut'); return; }
    if (cmd === 'toggle-button') {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (tab && tab.id) { try { await chrome.tabs.sendMessage(tab.id, { type: 'flex-toggle-button' }); } catch (e) { } }
    }
});

chrome.runtime.onInstalled.addListener(() => {
    chrome.storage.local.get({ port: DEFAULT_PORT }, v => chrome.storage.local.set({ port: v.port }));
});
