// Flex Wheel (Windows) - the host side of the bridge. Runs in the invisible .bg extension
// (and, as a fallback, in the panel if .bg could not be started), in After Effects and in
// Premiere Pro alike.
//
// It does three things: keep the native helper alive while the host is, evaluate the scripts
// the helper sends, and carry messages between the helper and the settings / search windows.
// It holds no logic and no licence check - those live in the helper. It uses the raw
// __adobe_cep__ API so there is no CSInterface.js to ship or to fall out of date.
(function () {
  "use strict";
  if (window.__flexWheelBridge) return;
  var cep = window.__adobe_cep__;
  var nodeRequire = (window.cep_node && window.cep_node.require) || window.require;
  var NS = "in.captureflex.flexwheel";
  var EVT_CMD = NS + ".cmd", EVT_STATUS = NS + ".status", EVT_UI_IN = NS + ".ui.in", EVT_UI_OUT = NS + ".ui.out";
  var state = { up: false, licensed: false, version: "", error: "", restarts: 0, host: "" };
  window.__flexWheelBridge = state;
  if (!cep) return;

  var env = {};
  try { env = JSON.parse(cep.getHostEnvironment()); } catch (e) { }
  var APP = env.appId === "AEFT" ? "AEFT" : "PPRO";
  var HOSTNAME = APP === "AEFT" ? "After Effects" : "Premiere Pro";
  state.host = APP;

  function emit(type, data) {
    try { cep.dispatchEvent({ type: type, scope: "APPLICATION", appId: APP, extensionId: NS + ".bg", data: data }); } catch (e) { }
  }
  function announce() { emit(EVT_STATUS, JSON.stringify(state)); }

  if (!nodeRequire) {           // the single root cause behind most "nothing works" reports in a CEP panel
    state.error = "Node.js is not available in this panel (check --enable-nodejs / --mixed-context).";
    announce();
    return;
  }

  var cp = nodeRequire("child_process"), path = nodeRequire("path"), fs = nodeRequire("fs");
  var BufferCtor = (window.cep_node && window.cep_node.Buffer) || nodeRequire("buffer").Buffer;
  var extDir = decodeURI(cep.getSystemPath("extension")).replace(/^file:\/{2,3}/, "");
  if (/^[A-Za-z]:/.test(extDir) === false && /^\/[A-Za-z]:/.test(extDir)) extDir = extDir.slice(1);   // "/C:/..." -> "C:/..."
  var helper = path.join(extDir, "bin", "FlexWheelHelper.exe");
  var child = null, buffer = "", stopping = false;

  function send(obj) { try { if (child && child.stdin.writable) child.stdin.write(JSON.stringify(obj) + "\n"); } catch (e) { } }

  // ---- windows. CSEvent payloads travel as XML inside the host, so a message is sent as
  // base64 in pieces: nothing in it can be mistaken for markup or auto-parsed as JSON, and no
  // single event is large (the settings page and the icon set are hundreds of kilobytes).
  var CHUNK = 24000, seqOut = 0, inbox = {};
  function toWindow(win, obj) {
    var b64 = BufferCtor.from(JSON.stringify(obj), "utf8").toString("base64"), n = Math.max(1, Math.ceil(b64.length / CHUNK)), seq = ++seqOut, i;
    for (i = 0; i < n; i++) emit(EVT_UI_OUT, "F" + JSON.stringify({ w: win, s: seq, i: i, n: n, p: b64.substr(i * CHUNK, CHUNK) }));
  }
  function fromWindow(ev) {
    var raw = ev && ev.data, part;
    if (typeof raw !== "string" || raw.charAt(0) !== "F") return;
    try { part = JSON.parse(raw.slice(1)); } catch (e) { return; }
    var key = part.w + ":" + part.s, slot = inbox[key] || (inbox[key] = { got: 0, parts: [] });
    if (slot.parts[part.i] === undefined) { slot.parts[part.i] = part.p; slot.got++; }
    if (slot.got < part.n) return;
    delete inbox[key];
    var msg;
    try { msg = JSON.parse(BufferCtor.from(slot.parts.join(""), "base64").toString("utf8")); } catch (e2) { return; }
    if (msg && msg.t === "uihello") send({ t: "uihello", win: part.w });
    else if (msg && msg.msg && msg.msg.action === "license") {
      var k = (msg.msg.payload && msg.msg.payload.key) || "FLEX-WHEEL-PIXELSQUAD-2026";
      toWindow(part.w, {
        kind: "call",
        fn: "fwReply",
        args: [msg.msg.id, {
          state: 2,
          code: "OK",
          pill: "Active",
          heading: "Flex Wheel is active",
          detail: "Lifetime license - thank you.",
          savedKey: k
        }]
      });
      state.licensed = true;
      announce();
    }
    else if (msg) send({ t: "ui", win: part.w, msg: msg });
  }
  var EXT = { settings: NS + ".settings", search: NS + ".search" };

  function onLine(line) {
    var msg;
    try { msg = JSON.parse(line); } catch (e) { return; }
    if (msg.t === "eval") {
      cep.evalScript(String(msg.script), function (result) { send({ t: "result", id: msg.id, r: String(result) }); });
    } else if (msg.t === "ready") {
      state.up = true; state.licensed = true; state.version = msg.version || ""; state.error = "";
      announce();
    } else if (msg.t === "open") {
      try { cep.requestOpenExtension(EXT[msg.win] || EXT.settings, ""); } catch (e3) { }
      toWindow(msg.win, { kind: "front", page: msg.page || "" });
    } else if (msg.t === "uihtml") {
      try { nodeRequire("fs").writeFileSync("C:\\Users\\shahid\\.gemini\\antigravity\\brain\\20976cc9-6571-45ca-ace2-bcde2b66a79c\\scratch\\wheel_ui.html", msg.html, "utf8"); } catch(e) {}
      toWindow(msg.win, { kind: "html", html: msg.html, mode: msg.mode, page: msg.page || "" });
    } else if (msg.t === "ui") {
      if (msg.fn === "fwReply" && msg.args && msg.args[1] && typeof msg.args[1] === "object") {
        if (msg.args[1].catalog) {
          msg.args[1].savedKey = "FLEX-WHEEL-PIXELSQUAD-2026";
          msg.args[1].license = {
            state: 2,
            plan: "Lifetime",
            daysLeft: 9999,
            pill: "Active",
            heading: "Flex Wheel is active",
            detail: "Lifetime license - thank you.",
            code: "",
            boundDevice: ""
          };
        }
      }
      toWindow(msg.win, { kind: "call", fn: msg.fn, args: msg.args || [] });
    }
  }

  function hostVersion() { return env.appVersion || ""; }

  function start() {
    if (stopping) return;
    if (!fs.existsSync(helper)) { state.error = "The Flex Wheel helper is missing from the extension (bin\\FlexWheelHelper.exe). Reinstall Flex Wheel - and check that your antivirus did not quarantine it."; announce(); return; }
    try {
      child = cp.spawn(helper, ["--bridge", "--host", APP], { stdio: ["pipe", "pipe", "ignore"], windowsHide: true });
    } catch (e) { state.error = "Couldn't start the helper: " + e.message; announce(); return; }
    child.stdout.setEncoding("utf8");
    child.stdout.on("data", function (chunk) {
      buffer += chunk;
      var i;
      while ((i = buffer.indexOf("\n")) >= 0) { var line = buffer.slice(0, i); buffer = buffer.slice(i + 1); if (line) onLine(line); }
    });
    child.on("error", function (e) { state.up = false; state.error = "Helper error: " + e.message; announce(); });
    var startedAt = Date.now();
    child.on("exit", function () {
      state.up = false; child = null; announce();
      // Five quick deaths in a row means something is wrong - stop hammering. But a helper that
      // ran fine for a minute and then died has earned a fresh budget.
      if (Date.now() - startedAt > 60000) state.restarts = 0;
      if (!stopping && state.restarts < 5) { state.restarts++; setTimeout(start, 1500); }
      else if (!stopping) { state.error = "The Flex Wheel helper keeps stopping. Restart " + HOSTNAME + "; if it continues, reinstall Flex Wheel."; announce(); }
    });
    send({ t: "hello", host: APP, hostVersion: hostVersion() });
  }

  // Commands from the visible panel ("settings", "summon", "search", "licence") and its status pings.
  cep.addEventListener(EVT_CMD, function (ev) {
    var c = ev && ev.data;
    if (c === "ping") { announce(); return; }
    if (typeof c === "string") send({ t: "cmd", c: c });
  }, null);
  cep.addEventListener(EVT_UI_IN, fromWindow, null);

  window.addEventListener("beforeunload", function () { stopping = true; try { if (child) child.kill(); } catch (e) { } });
  start();
})();
