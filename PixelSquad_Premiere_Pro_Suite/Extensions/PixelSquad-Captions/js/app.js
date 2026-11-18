/**
 * ====================================================================
 * PixelSquad Creative Suite
 * Copyright (C) 2026 PixelSquad. All Rights Reserved.
 * Author: Mohammed Shahid <hello@pixelsquad.in>
 * Proprietary & Confidential. Unauthorized copying, distribution,
 * modification, or reverse engineering is strictly prohibited.
 * ====================================================================
 */

/**
 * PixelSquad PSCaptions - app.js
 * Frontend Controller for Adobe Premiere Pro CEP Extension
 */

(function () {
  'use strict';

  var csInterface = null;
  try {
    csInterface = new CSInterface();
  } catch (e) {
    console.warn("CSInterface not loaded (running outside CEP environment):", e);
  }

  // Preset Definitions
  var PRESETS = [
    {
      id: "01",
      file: "01_Reels_PunchWord.mogrt",
      title: "Reels Punch Word",
      category: "Word-by-Word",
      animClass: "anim-reels-punch",
      desc: "Fast kinetic pop with bold outline"
    },
    {
      id: "02",
      file: "02_Reels_DynamicSub.mogrt",
      title: "Reels Dynamic Sub",
      category: "Word-by-Word",
      animClass: "anim-reels-dynamic",
      desc: "Smooth speech cadence subtitle"
    },
    {
      id: "03",
      file: "03_Hormozi_YellowPop.mogrt",
      title: "Hormozi Yellow Pop",
      category: "Hormozi Bounce",
      animClass: "anim-hormozi-yellow",
      desc: "Iconic yellow pop & black stroke"
    },
    {
      id: "04",
      file: "04_Hormozi_GreenScale.mogrt",
      title: "Hormozi Green Scale",
      category: "Hormozi Bounce",
      animClass: "anim-hormozi-green",
      desc: "Electric lime scale bounce"
    },
    {
      id: "05",
      file: "05_Neon_CyberGlow.mogrt",
      title: "Neon Cyber Glow",
      category: "Neon Glow",
      animClass: "anim-neon-cyber",
      desc: "Cyan glow with subtle flicker"
    },
    {
      id: "06",
      file: "06_Neon_MagentaPulse.mogrt",
      title: "Neon Magenta Pulse",
      category: "Neon Glow",
      animClass: "anim-neon-magenta",
      desc: "Synthwave pink neon radiation"
    },
    {
      id: "07",
      file: "07_Minimal_EditorialSub.mogrt",
      title: "Minimal Editorial",
      category: "Minimal Clean",
      animClass: "anim-minimal-editorial",
      desc: "Swiss typography with underline"
    },
    {
      id: "08",
      file: "08_Minimal_CleanLower.mogrt",
      title: "Minimal Clean Lower",
      category: "Minimal Clean",
      animClass: "anim-minimal-clean",
      desc: "Left accent bar clean lower"
    },
    {
      id: "09",
      file: "09_Box_RoundedPill.mogrt",
      title: "Box Rounded Pill",
      category: "Box Highlight",
      animClass: "anim-box-pill",
      desc: "Contrast pill background box"
    },
    {
      id: "10",
      file: "10_Box_RedAccent.mogrt",
      title: "Box Red Accent",
      category: "Box Highlight",
      animClass: "anim-box-red",
      desc: "High energy punch red highlight"
    },
    {
      id: "11",
      file: "11_Kinetic_SpringUp.mogrt",
      title: "Kinetic Spring Up",
      category: "Kinetic Pop",
      animClass: "anim-kinetic-spring",
      desc: "Elastic bounce slide up"
    },
    {
      id: "12",
      file: "12_Kinetic_SlideImpact.mogrt",
      title: "Kinetic Slide Impact",
      category: "Kinetic Pop",
      animClass: "anim-kinetic-slide",
      desc: "Angled velocity slide & impact"
    }
  ];

  // State Management
  var state = {
    aspect: "9x16_Reels",
    selectedCategory: "all",
    selectedPresetId: "01",
    targetTrack: 1,
    captionText: "VIRAL REELS",
    activeColor: "#FFE600",
    durationSeconds: 1.5,
    mode: "punchline", // "punchline" | "bulk"
    sequence: null
  };

  // DOM Elements
  var els = {
    statusDot: document.getElementById("statusDot"),
    statusLabel: document.getElementById("statusLabel"),
    btnRefreshSeq: document.getElementById("btnRefreshSeq"),
    aspectToggle: document.getElementById("aspectToggle"),
    selectTrack: document.getElementById("selectTrack"),
    categoryNav: document.getElementById("categoryNav"),
    presetsGrid: document.getElementById("presetsGrid"),
    tabPunchline: document.getElementById("tabPunchline"),
    tabBulkSRT: document.getElementById("tabBulkSRT"),
    panelPunchline: document.getElementById("panelPunchline"),
    panelBulkSRT: document.getElementById("panelBulkSRT"),
    captionTextInput: document.getElementById("captionTextInput"),
    btnClearText: document.getElementById("btnClearText"),
    colorSwatches: document.querySelectorAll(".color-swatch"),
    customColorPicker: document.getElementById("customColorPicker"),
    durationChips: document.querySelectorAll(".duration-group .btn-chip"),
    btnApplySingle: document.getElementById("btnApplySingle"),
    srtInput: document.getElementById("srtInput"),
    srtCountBadge: document.getElementById("srtCountBadge"),
    btnLoadSampleSRT: document.getElementById("btnLoadSampleSRT"),
    btnClearSRT: document.getElementById("btnClearSRT"),
    btnApplyBulk: document.getElementById("btnApplyBulk"),
    psToast: document.getElementById("psToast")
  };

  // Toast Helper
  function showToast(message, isError) {
    if (!els.psToast) return;
    els.psToast.textContent = message;
    els.psToast.className = "ps-toast" + (isError ? " error" : "") + " show";
    setTimeout(function () {
      els.psToast.classList.remove("show");
    }, 2800);
  }

  // ExtendScript Bridge Wrapper
  function evalScript(script, callback) {
    if (!csInterface) {
      if (callback) callback({ success: false, message: "CSInterface unavailable" });
      return;
    }
    csInterface.evalScript(script, function (res) {
      var data = null;
      try {
        data = JSON.parse(res);
      } catch (e) {
        data = { raw: res };
      }
      if (callback) callback(data);
    });
  }

  // Bootstrap ExtendScript Engine
  function initEngine() {
    if (!csInterface) return;
    var extPath = csInterface.getSystemPath(SystemPath.EXTENSION);
    var cleanPath = extPath.replace(/\\/g, '/');
    var loadCmd = '$.evalFile("' + cleanPath + '/jsx/PremiereCaptionEngine.jsx")';
    evalScript(loadCmd, function () {
      checkSequenceStatus();
    });
  }

  // Check Premiere Pro Active Sequence
  function checkSequenceStatus() {
    evalScript("PSCaptionsEngine.getActiveSequenceInfo()", function (res) {
      if (res && res.success) {
        state.sequence = res;
        els.statusDot.className = "status-dot connected";
        els.statusLabel.textContent = res.name || "Sequence Ready";
        els.statusLabel.title = "Active Sequence: " + res.name + " (" + res.width + "x" + res.height + ")";
      } else {
        state.sequence = null;
        els.statusDot.className = "status-dot disconnected";
        els.statusLabel.textContent = "No Sequence";
        els.statusLabel.title = res && res.message ? res.message : "Open a sequence in Timeline";
      }
    });
  }

  // Render Preset Cards
  function renderPresets() {
    els.presetsGrid.innerHTML = "";
    var currentText = state.captionText.trim() || "CAPTION";

    PRESETS.forEach(function (preset) {
      if (state.selectedCategory !== "all" && preset.category !== state.selectedCategory) {
        return;
      }

      var card = document.createElement("div");
      card.className = "preset-card" + (preset.id === state.selectedPresetId ? " selected" : "");
      card.dataset.id = preset.id;

      card.innerHTML =
        '<div class="card-preview-stage">' +
          '<span class="card-category-badge">' + preset.category + '</span>' +
          '<div class="preview-text ' + preset.animClass + '" id="prev_' + preset.id + '">' +
            escapeHtml(currentText) +
          '</div>' +
        '</div>' +
        '<div class="card-info">' +
          '<div class="card-title">' + preset.title + '</div>' +
          '<div class="card-meta">' + preset.desc + '</div>' +
        '</div>';

      card.addEventListener("click", function () {
        selectPreset(preset.id);
      });

      card.addEventListener("dblclick", function () {
        selectPreset(preset.id);
        applySingleCaption();
      });

      els.presetsGrid.appendChild(card);
    });
  }

  function escapeHtml(text) {
    return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function selectPreset(id) {
    state.selectedPresetId = id;
    var allCards = els.presetsGrid.querySelectorAll(".preset-card");
    allCards.forEach(function (c) {
      if (c.dataset.id === id) {
        c.classList.add("selected");
      } else {
        c.classList.remove("selected");
      }
    });
  }

  function updatePreviewTexts() {
    var txt = state.captionText.trim() || "CAPTION";
    var prevs = els.presetsGrid.querySelectorAll(".preview-text");
    prevs.forEach(function (p) {
      p.textContent = txt;
    });
  }

  // Get Absolute Path to Selected Preset MOGRT
  function getSelectedPresetPath() {
    var preset = PRESETS.find(function (p) { return p.id === state.selectedPresetId; });
    if (!preset) preset = PRESETS[0];

    if (!csInterface) return "";
    var extPath = csInterface.getSystemPath(SystemPath.EXTENSION);
    var cleanPath = extPath.replace(/\\/g, '/');
    return cleanPath + "/presets/" + state.aspect + "/" + preset.file;
  }

  // Single Caption Placement
  function applySingleCaption() {
    var mogrtPath = getSelectedPresetPath();
    var text = state.captionText.trim() || "CAPTION";
    var track = parseInt(els.selectTrack.value, 10) || 1;

    var options = {
      trackIndex: track,
      durationSeconds: state.durationSeconds,
      color: state.activeColor
    };

    var script = 'PSCaptionsEngine.applyCaptionMOGRT(' +
      JSON.stringify(mogrtPath) + ', ' +
      JSON.stringify(text) + ', ' +
      JSON.stringify(JSON.stringify(options)) + ')';

    showToast("Applying caption to timeline...", false);

    evalScript(script, function (res) {
      if (res && res.success) {
        showToast(res.message || "Caption applied to Sequence!", false);
      } else {
        showToast(res ? (res.message || "Failed to apply caption") : "Error applying caption", true);
      }
      checkSequenceStatus();
    });
  }

  // SRT Parser Helper
  function parseSRT(srtString) {
    var cues = [];
    if (!srtString) return cues;

    // Standard SRT Regex: index, timecode --> timecode, text
    var blocks = srtString.replace(/\r\n/g, '\n').replace(/\r/g, '\n').split('\n\n');
    for (var i = 0; i < blocks.length; i++) {
      var block = blocks[i].trim();
      if (!block) continue;

      var lines = block.split('\n');
      var timeLineIdx = -1;

      for (var l = 0; l < lines.length; l++) {
        if (lines[l].indexOf('-->') !== -1) {
          timeLineIdx = l;
          break;
        }
      }

      if (timeLineIdx !== -1) {
        var timeTokens = lines[timeLineIdx].split('-->');
        if (timeTokens.length === 2) {
          var startSec = srtTimeToSeconds(timeTokens[0].trim());
          var endSec = srtTimeToSeconds(timeTokens[1].trim());
          var textLines = lines.slice(timeLineIdx + 1).join(' ').trim();

          if (textLines) {
            cues.push({
              index: cues.length + 1,
              startSeconds: startSec,
              endSeconds: endSec,
              text: textLines
            });
          }
        }
      } else {
        // Plain text fallback (auto-pacing: 1.5s per line)
        var lineText = block.replace(/\n/g, ' ').trim();
        if (lineText) {
          var autoStart = cues.length * 1.6;
          cues.push({
            index: cues.length + 1,
            startSeconds: autoStart,
            endSeconds: autoStart + 1.5,
            text: lineText
          });
        }
      }
    }
    return cues;
  }

  function srtTimeToSeconds(timeStr) {
    // 00:01:23,456 or 00:01:23.456
    var parts = timeStr.replace(',', '.').split(':');
    if (parts.length === 3) {
      return (parseFloat(parts[0]) * 3600) + (parseFloat(parts[1]) * 60) + parseFloat(parts[2]);
    }
    return 0;
  }

  // Bulk Captions Placement
  function applyBulkCaptions() {
    var srtText = els.srtInput.value.trim();
    if (!srtText) {
      showToast("Please paste SRT or script text first!", true);
      return;
    }

    var cues = parseSRT(srtText);
    if (cues.length === 0) {
      showToast("No valid captions found in text.", true);
      return;
    }

    var mogrtPath = getSelectedPresetPath();
    var track = parseInt(els.selectTrack.value, 10) || 1;

    var options = {
      trackIndex: track,
      color: state.activeColor
    };

    var script = 'PSCaptionsEngine.applyBulkCaptions(' +
      JSON.stringify(JSON.stringify(cues)) + ', ' +
      JSON.stringify(mogrtPath) + ', ' +
      JSON.stringify(JSON.stringify(options)) + ')';

    showToast("Generating " + cues.length + " captions on Timeline...", false);

    evalScript(script, function (res) {
      if (res && res.success) {
        showToast(res.message || ("Successfully added " + res.appliedCount + " captions!"), false);
      } else {
        showToast(res ? (res.message || "Failed bulk import") : "Error during bulk import", true);
      }
      checkSequenceStatus();
    });
  }

  // Sample SRT Template
  var SAMPLE_SRT =
    "1\n00:00:01,000 --> 00:00:02,400\nSTOP SCROLLING RIGHT NOW!\n\n" +
    "2\n00:00:02,500 --> 00:00:04,100\nThis secret changes everything.\n\n" +
    "3\n00:00:04,200 --> 00:00:05,800\nReady to scale your content?\n\n" +
    "4\n00:00:05,900 --> 00:00:07,500\nHit follow and let's build!";

  // Setup Event Listeners
  function initEvents() {
    // Refresh Sequence
    els.btnRefreshSeq.addEventListener("click", checkSequenceStatus);

    // Aspect Toggle
    els.aspectToggle.querySelectorAll(".toggle-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        els.aspectToggle.querySelectorAll(".toggle-btn").forEach(function (b) { b.classList.remove("active"); });
        btn.classList.add("active");
        state.aspect = btn.dataset.aspect;
        showToast("Switched to " + (state.aspect === "9x16_Reels" ? "9:16 Reels" : "16:9 YouTube"), false);
      });
    });

    // Category Nav
    els.categoryNav.querySelectorAll(".category-pill").forEach(function (pill) {
      pill.addEventListener("click", function () {
        els.categoryNav.querySelectorAll(".category-pill").forEach(function (p) { p.classList.remove("active"); });
        pill.classList.add("active");
        state.selectedCategory = pill.dataset.category;
        renderPresets();
      });
    });

    // Caption Text Input
    els.captionTextInput.addEventListener("input", function (e) {
      state.captionText = e.target.value;
      updatePreviewTexts();
    });

    // Clear Text
    els.btnClearText.addEventListener("click", function () {
      els.captionTextInput.value = "";
      state.captionText = "";
      updatePreviewTexts();
      els.captionTextInput.focus();
    });

    // Color Swatches
    els.colorSwatches.forEach(function (swatch) {
      swatch.addEventListener("click", function () {
        els.colorSwatches.forEach(function (s) { s.classList.remove("active"); });
        swatch.classList.add("active");
        state.activeColor = swatch.dataset.color;
      });
    });

    // Custom Color Picker
    els.customColorPicker.addEventListener("input", function (e) {
      state.activeColor = e.target.value;
      els.colorSwatches.forEach(function (s) { s.classList.remove("active"); });
    });

    // Duration Chips
    els.durationChips.forEach(function (chip) {
      chip.addEventListener("click", function () {
        els.durationChips.forEach(function (c) { c.classList.remove("active"); });
        chip.classList.add("active");
        state.durationSeconds = parseFloat(chip.dataset.duration) || 1.5;
      });
    });

    // Mode Switcher
    els.tabPunchline.addEventListener("click", function () {
      els.tabPunchline.classList.add("active");
      els.tabBulkSRT.classList.remove("active");
      els.panelPunchline.classList.add("active");
      els.panelBulkSRT.classList.remove("active");
      state.mode = "punchline";
    });

    els.tabBulkSRT.addEventListener("click", function () {
      els.tabBulkSRT.classList.add("active");
      els.tabPunchline.classList.remove("active");
      els.panelBulkSRT.classList.add("active");
      els.panelPunchline.classList.remove("active");
      state.mode = "bulk";
    });

    // SRT Input
    els.srtInput.addEventListener("input", function () {
      var cues = parseSRT(els.srtInput.value);
      els.srtCountBadge.textContent = cues.length + " cues detected";
    });

    // Load Sample SRT
    els.btnLoadSampleSRT.addEventListener("click", function () {
      els.srtInput.value = SAMPLE_SRT;
      var cues = parseSRT(SAMPLE_SRT);
      els.srtCountBadge.textContent = cues.length + " cues detected";
    });

    // Clear SRT
    els.btnClearSRT.addEventListener("click", function () {
      els.srtInput.value = "";
      els.srtCountBadge.textContent = "0 cues detected";
    });

    // Action Buttons
    els.btnApplySingle.addEventListener("click", applySingleCaption);
    els.btnApplyBulk.addEventListener("click", applyBulkCaptions);
  }

  // Initialization
  document.addEventListener("DOMContentLoaded", function () {
    renderPresets();
    initEvents();
    initEngine();
  });

})();
