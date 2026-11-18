/**
 * ====================================================================
 * PixelSquad Creative Suite
 * Copyright (C) 2026 PixelSquad. All Rights Reserved.
 * Author: Mohammed Shahid <hello@pixelsquad.in>
 * Proprietary & Confidential. Unauthorized copying, distribution,
 * modification, or reverse engineering is strictly prohibited.
 * ====================================================================
 */

const fs = cep_node['require']('fs')
  , path = cep_node['require']('path')
  , os = cep_node['require']('os')
  , {execFile: execFile, execSync: execSync} = cep_node['require']('child_process')
  , csInterface = new CSInterface()
  , activateBtn = document['getElementById']('activateBtn')
  , pasteBtn = document['getElementById']('pasteBtn')
  , {spawn: spawn} = cep_node['require']('child_process')
  , pencilParkLink = document['getElementById']('pencilParkLink')
  , statusDiv = document['getElementById']('status');

window.addEventListener("DOMContentLoaded", () => {
  const cs = new CSInterface();

  let isShiftPressed = false;

  // Theo dõi trạng thái phím Shift
  window.addEventListener("keydown", (e) => {
    if (e.key === "Shift") isShiftPressed = true;
  });
  window.addEventListener("keyup", (e) => {
    if (e.key === "Shift") isShiftPressed = false;
  });

  // Load JSX khi extension khởi động
  cs.evalScript('$.evalFile(new File("' + cs.getSystemPath(SystemPath.EXTENSION) + '/jsx/QuickToolsPro2.0.jsx"));');

// Quick Tool Panel /////////////////////////////////////////////////////////////////////////////////
  const offsetBtn = document.querySelector('[aria-label="Offset"]');
  offsetBtn.addEventListener("click", () => {
  cs.evalScript("offsetLayerAndKey()");
  });

  const renameBtn = document.querySelector('[aria-label="Rename"]');
  renameBtn.addEventListener("click", () => {
  cs.evalScript("showRenameWindow()");
  });

  const expressionBtn = document.querySelector('[aria-label="Expression"]');
  expressionBtn.addEventListener("click", () => {
  cs.evalScript("openAddExpressionWindow()");
  });
  
  const easeCopyBtn = document.querySelector('[aria-label="Ease Copy"]');
  easeCopyBtn.addEventListener("click", () => {
  cs.evalScript("copyEase()");
  });    

  const easePasteBtn = document.querySelector('[aria-label="Ease Paste"]');
  easePasteBtn.addEventListener("click", () => {
  cs.evalScript("pasteEase()");
  });  


  const overBtn = document.querySelector('[aria-label="Overshoot"]');
  overBtn.addEventListener("click", (event) => {
    const shiftPressed = event.shiftKey;
    cs.evalScript(`applyOverShootToSelected(${shiftPressed})`);
  });

  const bounceBtn = document.querySelector('[aria-label="Bounce"]');
  bounceBtn.addEventListener("click", (event) => {
    const shiftPressed = event.shiftKey;
    cs.evalScript(`applyBounceToSelected(${shiftPressed})`);
  });

  const effectorBtn = document.querySelector('[aria-label="Effector"]');
  effectorBtn.addEventListener("click", () => {
    cs.evalScript("effectorTools()");
  }); 

  const aniMarkerBtn = document.querySelector('[aria-label="Ani-Marker"]');
  aniMarkerBtn.addEventListener("click", () => {
    cs.evalScript("AniMarker()");
  }); 

  const randomBtn = document.querySelector('[aria-label="Randomize"]');
  randomBtn.addEventListener("click", () => {
    cs.evalScript("randomProperty()");
  }); 

  const textToolBtn = document.querySelector('[aria-label="Text Tool"]');
  textToolBtn.addEventListener("click", () => {
    cs.evalScript("textToolsUI()");
  });

  const unPreCompBtn = document.querySelector('[aria-label="Un-Precomp"]');
  unPreCompBtn.addEventListener("click", () => {
    cs.evalScript("unPreCompMain()");
  });

  const dupCompBtn = document.querySelector('[aria-label="DUP-Comp"]');
  dupCompBtn.addEventListener("click", () => {
    cs.evalScript("dupComp()");
  });

  const selectPathBtn = document.querySelector('[aria-label="Select Path"]');
  selectPathBtn.addEventListener("click", () => {
    cs.evalScript("runShowPathWithMasks()");
  });

  const controlPathBtn = document.querySelector('[aria-label="Control Path"]');
  controlPathBtn.addEventListener("click", () => {
    cs.evalScript("runFullNullControlPath()");
  });

  const motionPathBtn = document.querySelector('[aria-label="Motion Path"]');
  motionPathBtn.addEventListener("click", () => {
    cs.evalScript("motionPath()");
  });

  const mergeBtn = document.querySelector('[aria-label="Merge"]');
  mergeBtn.addEventListener("click", () => {
    cs.evalScript("mergeShape()");
  });

  const splitBtn = document.querySelector('[aria-label="Split"]');
  splitBtn.addEventListener("click", () => {
    cs.evalScript("splitShape()");
  });

// Label Setup /////////////////////////////////////////////////////
  const labelDropdown = document.getElementById("label-select");
  const saveBtn = document.querySelector('[aria-label="Save Label"]');
  const selectBtn = document.querySelector('[aria-label="Select label"]');
  const enableBtn = document.querySelector('[aria-label="Enable/Disable"]');
  const colorControlBtn = document.querySelector('[aria-label="Color Control"]');

  colorControlBtn.addEventListener("click", () => {
    cs.evalScript("colorControl()");
  });

  const labelMap = {
    none: 0, red: 1, yellow: 2, aqua: 3, pink: 4, lavender: 5,
    peach: 6, seafoam: 7, blue: 8, green: 9, purple: 10,
    fuchsia: 11, tan: 12, olive: 13, orange: 14, brown: 15, magenta: 16
  };

  // 🧠 Hàm tiện ích: lấy giá trị label hiện tại
  function getCurrentLabel() {
    const selected = labelDropdown.value;
    if (!selected || selected === "none") {
      alert("Select label first.");
      return null;
    }
    const labelVal = labelMap[selected];
    if (labelVal === undefined) {
      alert("Invalid label selected.");
      return null;
    }
    return labelVal;
  }

  // 🟥 Save Label
  saveBtn.addEventListener("click", () => {
    const labelVal = getCurrentLabel();
    if (labelVal === null) return;
    cs.evalScript(`saveLabel(${labelVal})`, (res) => console.log("✅", res));
  });

  // 🟨 Select Label
  selectBtn.addEventListener("click", (e) => {
    const isShift = e.shiftKey;
    const isCtrl = e.ctrlKey || e.metaKey; // ⌘ trên macOS

    // 🟦 Nếu nhấn Ctrl → chọn layer có label khác dropdown hiện tại
    if (isCtrl) {
      const labelVal = getCurrentLabel();
      if (labelVal === null) return;
      cs.evalScript(`selectLabelInverse(${labelVal})`, (res) => {
        console.log("✅ Inverse Select:", res);
      });
      return; // ✅ dừng ở đây, không chạy phần còn lại
    }

    // 🟨 Nếu nhấn Shift → chọn theo label của layer cuối cùng đang chọn
    const labelVal = isShift ? "auto" : getCurrentLabel();
    if (labelVal === null) return;

    cs.evalScript(`selectLabel("${labelVal}")`, (res) => {
      console.log("✅", res);

      // Chỉ update dropdown nếu shift-click, bình thường giữ nguyên
      if (isShift && res !== "0") {
        const labelName = Object.keys(labelMap).find(
          (key) => labelMap[key] === parseInt(res)
        );
        if (labelName) labelDropdown.value = labelName;
      }
    });
  });


  // 🟩 Enable / Disable
  enableBtn.addEventListener("click", (e) => {
    const labelVal = getCurrentLabel();
    if (labelVal === null) return;

    let mode = "normal";
    if (e.ctrlKey || e.metaKey) mode = "ctrl";   // Ctrl (Windows) hoặc Command (Mac)
    else if (e.shiftKey) mode = "shift";

    cs.evalScript(`toggleEnable(${labelVal}, "${mode}")`, (res) => console.log("✅", res));
  });





// Graph Tool ////////////////////////////////////////////////////////////
// --- CHECKBOX ---
const getFlag = () => document.getElementById("affect-layer")?.checked ? "true" : "false";

  const evalAE = (cmd) => {
    console.log("▶ AE:", cmd);
    cs.evalScript(cmd);
  };

  // --- Buttons ---
  const btnMap = {
    "btn-linear": "linear",
    "btn-holdL": "holdL",
    "btn-hold": "holdB",
    "btn-holdR": "holdR",
    "btn-auto": "auto",
    "btn-cont": "cont",
    "btn-ease-in": "easeIn",
    "btn-ease-out": "easeOut",
  };

  Object.entries(btnMap).forEach(([id, mode]) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.addEventListener("click", () => {
      evalAE(`setTemporalMode('${mode}', ${getFlag()})`);
    });
  });

  // --- Sliders ---
  const bindSlider = (sliderId, inputId, jsxFn) => {
    const slider = document.getElementById(sliderId);
    const input = document.getElementById(inputId);
    if (!slider || !input) return;

    const apply = (val, shift = false) => {
      val = Math.max(0, Math.min(100, parseFloat(val) || 0));
      slider.value = val;
      input.value = val;
      const v = parseFloat(val);
      if (isNaN(v)) return;
      evalAE(`${jsxFn}(${v}, ${getFlag()})`);
      if (shift) evalAE(`applySpeed(0, ${getFlag()})`);
    };

    // Realtime kéo slider
    slider.addEventListener("input", (e) => {
      input.value = slider.value;
      apply(slider.value, e.shiftKey);
    });

    // Khi thả slider hoặc blur input
    slider.addEventListener("change", (e) => apply(slider.value, e.shiftKey));
    input.addEventListener("change", (e) => apply(input.value, e.shiftKey));

    // Nhấn Enter trong input
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        e.stopPropagation();
        slider.value = input.value;
        apply(input.value, e.shiftKey);
        input.blur();
      }
    });

    // Click vào slider track mà không kéo
    slider.addEventListener("mouseup", (e) => apply(slider.value, e.shiftKey));
    slider.addEventListener("touchend", (e) => apply(slider.value, e.shiftKey));

      input.addEventListener("input", () => {
        slider.value = input.value;
        apply(input.value, false);
      });

      // optional: ensure keyup cho phím ↑/↓ cũng update
      input.addEventListener("keyup", (e) => {
        if (e.key === "ArrowUp" || e.key === "ArrowDown") {
          slider.value = input.value;
          apply(input.value, e.shiftKey);
        }
      });
  };

  // --- Bind all sliders ---
  bindSlider("ease-in-slider", "ease-in-input", "applyInfluenceIn");
  bindSlider("ease-out-slider", "ease-out-input", "applyInfluenceOut");
  bindSlider("both-slider", "both-input", "applyInfluenceBoth");

  // --- SPEED input ---
  const speedInput = document.getElementById("speed-input");
  if (speedInput) {
    speedInput.addEventListener("change", () => {
      const v = parseFloat(speedInput.value);
      if (!isNaN(v)) evalAE(`applySpeed(${v}, ${getFlag()})`);
    });
    speedInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        e.stopPropagation();
        const v = parseFloat(speedInput.value);
        if (!isNaN(v)) evalAE(`applySpeed(${v}, ${getFlag()})`);
        speedInput.blur();
      }
    });
  }

// Set Anchor and Null ///////////////////////////////////////////////////////
const parentBtn = document.querySelector('[aria-label="Parent"]');
  parentBtn.addEventListener("click", () => {
    cs.evalScript("parentSelectedLayersToLast()");
  });

const setAnchorBtn = document.querySelector('[aria-label="Set Anchor"]');
  setAnchorBtn.addEventListener("click", () => {
    cs.evalScript("quickSetAnchor()");
  });

const quickSetNullBtn = document.querySelector('[aria-label="Set Null"]');
  quickSetNullBtn.addEventListener("click", () => {
    cs.evalScript("quickSetNull()");
  });

// Sell ====
const modeDropdown = document.getElementById("mode-select");
const ignoreMaskCheckbox = document.querySelector('[aria-label="Ignore Mask"]');
const anchorButtons = document.querySelectorAll(".control-pad .button.large");

const labelToXY = {
  "Top Left": [0, 0],
  "Top Center": [0.5, 0],
  "Top Right": [1, 0],
  "Middle Left": [0, 0.5],
  "Center": [0.5, 0.5],
  "Middle Right": [1, 0.5],
  "Bottom Left": [0, 1],
  "Bottom Center": [0.5, 1],
  "Bottom Right": [1, 1]
};

anchorButtons.forEach(btn => {
  btn.addEventListener("click", (e) => {
    const shiftHeld = e.shiftKey;
    const label = btn.getAttribute("aria-label");
    const [xx, yy] = labelToXY[label] || [0.5, 0.5];

    const moveTypeIndex = modeDropdown.selectedIndex || 0;
    const ignoreMasks = ignoreMaskCheckbox.checked;

    if (!shiftHeld) {
      cs.evalScript(`findAndMoveAnchor(${xx}, ${yy}, 0, ${moveTypeIndex}, ${ignoreMasks}, true)`);
    } else {
      cs.evalScript(`findAndSetNull(${xx}, ${yy}, 0, ${moveTypeIndex}, ${ignoreMasks}, true)`);
    }
  });
});

});

