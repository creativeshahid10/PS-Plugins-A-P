function _0x7cb5(_0x1661ab, _0x202d22) {
  const _0x424e56 = _0x424e();
  return _0x7cb5 = function (_0x7cb582, _0x3da090) {
    _0x7cb582 = _0x7cb582 - 325;
    let _0x35bb84 = _0x424e56[_0x7cb582];
    return _0x35bb84;
  }, _0x7cb5(_0x1661ab, _0x202d22);
}
const _0x3d1481 = _0x7cb5;
(function (_0x1ac74, _0x54e571) {
  const _0x5a3738 = _0x7cb5, _0x44e8a2 = _0x1ac74();
  while (true) {
    try {
      const _0x5a2b4c = -parseInt(_0x5a3738(330)) / 1 + parseInt(_0x5a3738(380)) / 2 + -parseInt(_0x5a3738(417)) / 3 + parseInt(_0x5a3738(328)) / 4 + parseInt(_0x5a3738(498)) / 5 * (-parseInt(_0x5a3738(344)) / 6) + parseInt(_0x5a3738(415)) / 7 * (parseInt(_0x5a3738(397)) / 8) + parseInt(_0x5a3738(432)) / 9 * (parseInt(_0x5a3738(346)) / 10);
      if (_0x5a2b4c === _0x54e571) break; else _0x44e8a2.push(_0x44e8a2.shift());
    } catch (_0x3c5d41) {
      _0x44e8a2.push(_0x44e8a2.shift());
    }
  }
}(_0x424e, 865209));
const cs = new CSInterface;
var currentValues = {x: 0, y: 0, z: 0, d: 0, pa: 0, ti: 0, ro: 0, px: 500, speed: 2, focus: 1e3, blur: 300, amp: 15, freq: 8, fade: 10, dist: 100, min: 50};
function applySpacing(_0x31d196, _0x1e6513) {
  const _0x2b9439 = _0x7cb5;
  let _0x3db978 = "";
  if (_0x31d196 === "x") _0x3db978 = _0x2b9439(490);
  if (_0x31d196 === "y") _0x3db978 = _0x2b9439(331);
  if (_0x31d196 === "z") _0x3db978 = _0x2b9439(445);
  if (!_0x3db978) return;
  console.log(_0x2b9439(421) + _0x31d196 + " spacing: " + _0x1e6513), cs[_0x2b9439(461)](_0x3db978 + "(" + _0x1e6513 + ")");
}
function applyRandomSpacing() {
  const _0x499698 = _0x7cb5, _0x25e323 = currentValues.d || document[_0x499698(495)]("dInput")[_0x499698(418)] || 100;
  console.log(_0x499698(425) + _0x25e323), cs[_0x499698(461)](_0x499698(376) + _0x25e323 + ")");
}
function syncValues(_0x59b833, _0x6ef912) {
  const _0x5e40b3 = _0x7cb5, _0x49ad9e = document[_0x5e40b3(495)](_0x59b833 + _0x5e40b3(377)), _0x4dd143 = document[_0x5e40b3(495)](_0x59b833 + _0x5e40b3(351));
  if (!_0x49ad9e || !_0x4dd143) return;
  let _0xcbeb18;
  _0x6ef912 === _0x49ad9e ? (_0xcbeb18 = _0x49ad9e[_0x5e40b3(418)], _0x4dd143[_0x5e40b3(418)] = _0xcbeb18) : (_0xcbeb18 = _0x4dd143.value, _0x49ad9e.value = _0xcbeb18);
  currentValues[_0x59b833] = parseFloat(_0xcbeb18);
  if (["x", "y", "z"][_0x5e40b3(494)](_0x59b833)) applySpacing(_0x59b833, _0xcbeb18); else {
    if (_0x59b833 === "pa") cs[_0x5e40b3(461)](_0x5e40b3(336) + _0xcbeb18 + ")"); else {
      if (_0x59b833 === "ti") cs.evalScript(_0x5e40b3(363) + _0xcbeb18 + ")"); else {
        if (_0x59b833 === "ro") cs.evalScript(_0x5e40b3(348) + _0xcbeb18 + ")"); else {
          if (_0x59b833 === "px") cs[_0x5e40b3(461)](_0x5e40b3(342) + _0xcbeb18 + ")"); else _0x59b833 === _0x5e40b3(491) && cs[_0x5e40b3(461)](_0x5e40b3(356) + _0xcbeb18 + _0x5e40b3(483) + _0xcbeb18 + ";");
        }
      }
    }
  }
  console[_0x5e40b3(354)]("[OK] " + _0x59b833.toUpperCase() + _0x5e40b3(428) + _0xcbeb18);
}
document[_0x3d1481(383)](_0x3d1481(488), function () {
  const _0xcfec36 = _0x3d1481;
  console[_0xcfec36(354)]("Initializing Camera3D Toolkit Pro event listeners..."), ["x", "y", "z"][_0xcfec36(443)](_0x3519ce => {
    const _0x850c79 = _0xcfec36, _0x571cc7 = document[_0x850c79(495)](_0x3519ce + _0x850c79(377)), _0x26b55b = document[_0x850c79(495)](_0x3519ce + _0x850c79(351));
    _0x571cc7 && _0x571cc7[_0x850c79(383)](_0x850c79(401), function (_0x3bde2a) {
      syncValues(_0x3519ce, _0x571cc7);
    }), _0x26b55b && _0x26b55b[_0x850c79(383)](_0x850c79(401), function (_0x143ebf) {
      syncValues(_0x3519ce, _0x26b55b);
    });
  });
  const _0x2d52dc = document[_0xcfec36(495)](_0xcfec36(433)), _0x399929 = document[_0xcfec36(495)](_0xcfec36(419));
  _0x2d52dc && _0x2d52dc[_0xcfec36(383)](_0xcfec36(401), function (_0x5a092c) {
    syncValues("d", _0x2d52dc);
  });
  _0x399929 && _0x399929[_0xcfec36(383)](_0xcfec36(401), function (_0x86a55a) {
    syncValues("d", _0x399929);
  });
  const _0x5ac3bc = document[_0xcfec36(467)](_0xcfec36(335));
  _0x5ac3bc && _0x5ac3bc[_0xcfec36(383)]("click", function () {
    applyRandomSpacing();
  }), initializeOtherControls(), console.log(_0xcfec36(388));
});
function initializeOtherControls() {
  const _0x291341 = _0x3d1481;
  ["pa", "ti", "ro"].forEach(_0x18a0f6 => {
    const _0x52ce93 = _0x7cb5, _0xf0a002 = document[_0x52ce93(495)](_0x18a0f6 + _0x52ce93(377)), _0x19ab28 = document[_0x52ce93(495)](_0x18a0f6 + _0x52ce93(351));
    _0xf0a002 && _0xf0a002[_0x52ce93(383)](_0x52ce93(401), function (_0x33f128) {
      syncValues(_0x18a0f6, _0xf0a002);
    }), _0x19ab28 && _0x19ab28.addEventListener(_0x52ce93(401), function (_0x451c98) {
      syncValues(_0x18a0f6, _0x19ab28);
    });
  }), ["px", _0x291341(491)][_0x291341(443)](_0x25c0d6 => {
    const _0x19d3e5 = _0x291341, _0x1832bb = document[_0x19d3e5(495)](_0x25c0d6 + _0x19d3e5(377)), _0x46f717 = document[_0x19d3e5(495)](_0x25c0d6 + "Input");
    _0x1832bb && _0x1832bb.addEventListener(_0x19d3e5(401), function (_0x511bed) {
      syncValues(_0x25c0d6, _0x1832bb);
    }), _0x46f717 && _0x46f717[_0x19d3e5(383)](_0x19d3e5(401), function (_0x17bf15) {
      syncValues(_0x25c0d6, _0x46f717);
    });
  }), [_0x291341(327), _0x291341(472)][_0x291341(443)](_0x109ed5 => {
    const _0x2a250d = _0x291341, _0x3ec174 = document[_0x2a250d(495)](_0x109ed5 + _0x2a250d(377)), _0xf15c59 = document[_0x2a250d(495)](_0x109ed5 + "Input");
    _0x3ec174 && _0x3ec174[_0x2a250d(383)](_0x2a250d(401), function (_0x41e5a6) {
      syncValues(_0x109ed5, _0x3ec174);
    }), _0xf15c59 && _0xf15c59[_0x2a250d(383)](_0x2a250d(401), function (_0x50af17) {
      syncValues(_0x109ed5, _0xf15c59);
    });
  }), [_0x291341(360), _0x291341(386)][_0x291341(443)](_0x5b4cdc => {
    const _0xb129f9 = _0x291341, _0x4fcada = document.getElementById(_0x5b4cdc + "Slider"), _0x49bf4c = document[_0xb129f9(495)](_0x5b4cdc + _0xb129f9(351));
    _0x4fcada && _0x4fcada[_0xb129f9(383)](_0xb129f9(401), function (_0x40e551) {
      syncValues(_0x5b4cdc, _0x4fcada);
    }), _0x49bf4c && _0x49bf4c[_0xb129f9(383)](_0xb129f9(401), function (_0x1f2467) {
      syncValues(_0x5b4cdc, _0x49bf4c);
    });
  }), [_0x291341(477), _0x291341(427)][_0x291341(443)](_0x5d4328 => {
    const _0x42fca8 = _0x291341, _0x4c6b3d = document[_0x42fca8(495)](_0x5d4328 + _0x42fca8(377)), _0x166d78 = document[_0x42fca8(495)](_0x5d4328 + _0x42fca8(351));
    _0x4c6b3d && _0x4c6b3d[_0x42fca8(383)](_0x42fca8(401), function (_0x5040dc) {
      syncValues(_0x5d4328, _0x4c6b3d);
    }), _0x166d78 && _0x166d78[_0x42fca8(383)](_0x42fca8(401), function (_0x586e5b) {
      syncValues(_0x5d4328, _0x166d78);
    });
  });
  const _0x500b07 = document[_0x291341(495)](_0x291341(337)), _0x4b33af = document.getElementById("minInput");
  _0x500b07 && _0x500b07[_0x291341(383)](_0x291341(401), function (_0x4fdc42) {
    const _0x3f7cf9 = _0x291341;
    syncValues(_0x3f7cf9(411), _0x500b07);
  }), _0x4b33af && _0x4b33af[_0x291341(383)]("input", function (_0x1e9b9b) {
    const _0xa39d52 = _0x291341;
    syncValues(_0xa39d52(411), _0x4b33af);
  });
}
function quickSetup() {
  const _0x1d513e = _0x3d1481;
  console[_0x1d513e(354)](_0x1d513e(409)), cs.evalScript("quickSetup()");
}
function panLeft() {
  const _0x51efc9 = _0x3d1481;
  console[_0x51efc9(354)](_0x51efc9(447)), cs[_0x51efc9(461)]("panLeft()");
}
function panRight() {
  const _0xd27a19 = _0x3d1481;
  console[_0xd27a19(354)](_0xd27a19(437)), cs.evalScript(_0xd27a19(395));
}
function tiltUp() {
  const _0x55a2c9 = _0x3d1481;
  console.log("Tilt Up"), cs[_0x55a2c9(461)](_0x55a2c9(378));
}
function tiltDown() {
  const _0x1f402a = _0x3d1481;
  console[_0x1f402a(354)](_0x1f402a(434)), cs.evalScript("tiltDown()");
}
function rollLeft() {
  const _0x218118 = _0x3d1481;
  console[_0x218118(354)](_0x218118(359)), cs[_0x218118(461)](_0x218118(471));
}
function rollRight() {
  const _0x5d53b1 = _0x3d1481;
  console[_0x5d53b1(354)](_0x5d53b1(458)), cs[_0x5d53b1(461)](_0x5d53b1(382));
}
function moveUp() {
  const _0x496879 = _0x3d1481;
  console.log(_0x496879(451)), cs[_0x496879(461)](_0x496879(429));
}
function moveDown() {
  const _0x2a970e = _0x3d1481;
  console[_0x2a970e(354)](_0x2a970e(449)), cs[_0x2a970e(461)](_0x2a970e(468));
}
function moveLeft() {
  const _0xa6cd6f = _0x3d1481;
  console[_0xa6cd6f(354)]("Move Left"), cs.evalScript(_0xa6cd6f(345));
}
function moveRight() {
  const _0x543a4b = _0x3d1481;
  console[_0x543a4b(354)](_0x543a4b(438)), cs[_0x543a4b(461)](_0x543a4b(370));
}
function moveForward() {
  const _0x5a9cac = _0x3d1481;
  console.log(_0x5a9cac(399)), cs[_0x5a9cac(461)](_0x5a9cac(334));
}
function moveBackward() {
  const _0x213b8f = _0x3d1481;
  console.log("Move Backward"), cs[_0x213b8f(461)](_0x213b8f(379));
}
function moveUp() {
  const _0x3b5012 = _0x3d1481;
  console[_0x3b5012(354)]("Travel Up"), cs[_0x3b5012(461)]("travelUp()");
}
function moveDown() {
  const _0x42bd55 = _0x3d1481;
  console[_0x42bd55(354)](_0x42bd55(340)), cs.evalScript(_0x42bd55(426));
}
function moveLeft() {
  const _0x3dd0f4 = _0x3d1481;
  console[_0x3dd0f4(354)]("Travel Left"), cs.evalScript("travelLeft()");
}
function moveRight() {
  const _0xad67ba = _0x3d1481;
  console.log(_0xad67ba(431)), cs[_0xad67ba(461)]("travelRight()");
}
function moveForward() {
  const _0x37b1f4 = _0x3d1481;
  console[_0x37b1f4(354)](_0x37b1f4(374)), cs[_0x37b1f4(461)](_0x37b1f4(373));
}
function moveBackward() {
  const _0xebd595 = _0x3d1481;
  console.log(_0xebd595(478)), cs[_0xebd595(461)](_0xebd595(362));
}
function applyAutoFocus() {
  const _0xa92ff5 = _0x3d1481;
  console[_0xa92ff5(354)](_0xa92ff5(464)), cs[_0xa92ff5(461)]("dollyToTarget()");
}
function moveToSelectedTarget() {
  const _0x5787cc = _0x3d1481;
  console[_0x5787cc(354)](_0x5787cc(485)), cs[_0x5787cc(461)]("moveToTarget()");
}
function applyLookAtTarget() {
  const _0x3cf2f6 = _0x3d1481;
  console[_0x3cf2f6(354)](_0x3cf2f6(371)), cs.evalScript(_0x3cf2f6(333));
}
function applyCameraShake() {
  const _0x179476 = _0x3d1481;
  console[_0x179476(354)](_0x179476(410)), cs.evalScript(_0x179476(381));
}
function applyCameraShakeS() {
  const _0x1cf77a = _0x3d1481;
  console[_0x1cf77a(354)](_0x1cf77a(481)), cs.evalScript("applyScaleAndRotation()");
}
function applyCustomSR(_0x3b3be3, _0x2f0eb2) {
  const _0x13d443 = _0x3d1481;
  console[_0x13d443(354)](_0x13d443(466) + _0x3b3be3 + _0x13d443(400) + _0x2f0eb2 + "°"), cs[_0x13d443(461)](_0x13d443(450) + _0x3b3be3 + ", " + _0x2f0eb2 + ")");
}
function resetScaleRotation() {
  const _0x17a260 = _0x3d1481;
  console[_0x17a260(354)]("Reset Scale + Rotation"), cs[_0x17a260(461)]("resetScaleAndRotation()");
}
function getCameraInfo() {
  const _0x5f0082 = _0x3d1481;
  console[_0x5f0082(354)](_0x5f0082(493)), cs[_0x5f0082(461)](_0x5f0082(367));
}
function addCameraKeyframe() {
  const _0x187345 = _0x3d1481;
  console[_0x187345(354)]("Create Overlap Keys Chain"), cs.evalScript(_0x187345(424));
}
function applyFocalDistance() {
  const _0x22653c = _0x3d1481, _0x5e2320 = currentValues[_0x22653c(411)] || document[_0x22653c(495)](_0x22653c(486))[_0x22653c(418)] || 50;
  console[_0x22653c(354)](_0x22653c(420) + _0x5e2320 + "%"), cs.evalScript(_0x22653c(391) + _0x5e2320 + ")");
}
function updateMinValue(_0x1a14e5) {
  const _0x58f947 = _0x3d1481;
  currentValues[_0x58f947(411)] = parseFloat(_0x1a14e5) || 50, console[_0x58f947(354)](_0x58f947(440) + currentValues[_0x58f947(411)] + "%"), $[_0x58f947(357)](_0x58f947(484) + currentValues[_0x58f947(411)] + "%");
}
function _0x424e() {
  const _0x35f1ed = ["applyCameraShakeMain()", "rollLeft()", "blur", "normal-handheld", "small-explosion", "fast-circular", "Apply Camera Shake", "fade", "Travel Backward", "toUpperCase", "car-engine", "Apply Scale + Rotation (S+R)", "tagName", "); DEFAULT_SPEED = ", "Min% updated: ", "Move To Target", "minInput", "truck-vehicle", "DOMContentLoaded", "subtle-random", "applyXSpacing", "speed", "cameraAmpInput", "Camera Info", "includes", "getElementById", "none", "applyEaseIn()", "593490BEgeyZ", "gentle-wind", "Parent Camera to Null", "Setup/Parent/Reset controls initialized", "focus", "3925944eyVFfK", "Create Depth Fade Keyframes", "1317314TKsUdo", "applyYSpacing", "applySmoothStandard()", "dollyToTargetLookAt()", "moveForward()", 'button[title="Random Spacing"]', "applyPanValue(", "minSlider", "TEXTAREA", "smooth-circular", "Travel Down", "cameraFreqInput", "updatePxValue(", "Remove Depth Fade Keyframes", "18FLBBzN", "moveLeft()", "80kTfhrn", "strong-wind", "applyRollValue(", "updateCameraAperture(", "Create 3D Path Trace", "Input", "change", "focusInput", "log", "Center Map Null", "updateSpeedValue(", "writeln", "createMapNull()", "Roll Left", "amp", "Setup button found", "travelBackward()", "applyTiltValue(", 'button[onclick="resetAll()"]', "Remove Camera Shake", "big-explosion", 'alert("Get Camera Info function")', "updateCameraShakeType(0)", "centerAnchorPointsForSelectionOrAll()", "moveRight()", "Dolly To Target Look At", "px, Freq:", "travelForward()", "Travel Forward", "preventDefault", "applyRandomSpacing(", "Slider", "tiltUp()", "moveBackward()", "2804088VfKrRy", "applyRandomRotation()", "rollRight()", "addEventListener", "); createDepthFadeKeyframes();", "updateCameraBlurLevel(", "freq", "Get Camera Info", "Event listeners initialized successfully", "create3DPathTrace()", "createPremiumCameraRig()", "applySpeedFloor(", "Show About", "deleteMapNull()", "focusSlider", "panRight()", "soft-handheld", "170008tjMRfY", "blurInput", "Move Forward", "%, Rotation=", "input", "cameraFreqSlider", "parentCameraToNull()", 'button[onclick="getCameraInfo()"]', "updateFadeStepValue(", "applyEaseOut()", "updateCameraShakeFrequency(", "dragstart", "Quick Setup clicked", "Apply Random Rotation", "min", "Hz, Type:", "INPUT", "Setup Camera Rig", "168OdJstX", "selectstart", "1393539wHvkVS", "value", "dInput", "Apply Speed Floor: ", "Applying ", "Delete Map Null", "Apply Smooth Standard (70%)", "createOverlapKeysChain()", "Applying random spacing: ", "travelDown()", "dist", " updated: ", "moveUp()", "target", "Travel Right", "123273ybgPxL", "dSlider", "Tilt Down", "Create Map Null", " (Amp:", "Pan Right", "Move Right", "charAt", "Live Speed Floor: ", "Camera preset reset to None", "Parent button found", "forEach", "updateCameraShakeType(", "applyZSpacing", "cameraPreset", "Pan Left", "round", "Move Down", "applyCustomScaleAndRotation(", "Move Up", "Available: Spacing, Animation (Pan/Tilt/Roll), Movement (6D), Smooth Keyframes", "updateCameraShakeAmplitude(", "Apply Ease Out (fast to slow)", "contextmenu", "confirmPremiumReset()", "slice", "Roll Right", "vintage-film", "Reset Keyframe Velocities", "evalScript", "Travel Up", "Camera Shake controls initialized", "Dolly To Target", "cameraAmpSlider", "Apply Custom S+R: Scale=", "querySelector", "moveDown()", "Reset All Premium Values"];
  _0x424e = function () {
    return _0x35f1ed;
  };
  return _0x424e();
}
function resetKeyframeVelocities() {
  const _0x409ef3 = _0x3d1481;
  console[_0x409ef3(354)](_0x409ef3(460)), cs.evalScript("resetKeyframeVelocities()");
}
function applyAutoFocusM() {
  const _0x4934b3 = _0x3d1481;
  console[_0x4934b3(354)](_0x4934b3(435)), cs[_0x4934b3(461)](_0x4934b3(358));
}
function selectMap() {
  const _0x2a4d7f = _0x3d1481;
  console.log("Select Map Null"), cs[_0x2a4d7f(461)]("selectMapNull()");
}
function deleteMap() {
  const _0x5e0a4c = _0x3d1481;
  console.log(_0x5e0a4c(422)), cs[_0x5e0a4c(461)](_0x5e0a4c(393));
}
function centerMap() {
  const _0x41f296 = _0x3d1481;
  console[_0x41f296(354)](_0x41f296(355)), cs[_0x41f296(461)]("centerMapNull()");
}
function create3DTrace() {
  const _0x29b5b9 = _0x3d1481;
  console.log(_0x29b5b9(350)), cs[_0x29b5b9(461)](_0x29b5b9(389));
}
var isUpdatingFocus = false, isUpdatingBlur = false;
function updateFocusRealTime(_0x2b430d) {
  const _0x486e2f = _0x3d1481;
  if (isUpdatingFocus) return;
  isUpdatingFocus = true;
  var _0x50d6e6 = parseFloat(_0x2b430d) || 1e3;
  currentValues[_0x486e2f(327)] = _0x50d6e6, cs.evalScript(_0x486e2f(349) + _0x50d6e6 + ")"), isUpdatingFocus = false;
}
function updateBlurRealTime(_0x390ab3) {
  const _0x218b94 = _0x3d1481;
  if (isUpdatingBlur) return;
  isUpdatingBlur = true;
  var _0x80943b = parseFloat(_0x390ab3) || 300;
  currentValues[_0x218b94(472)] = _0x80943b, cs[_0x218b94(461)](_0x218b94(385) + _0x80943b + ")"), isUpdatingBlur = false;
}
function syncFocusBlur(_0x3b1551, _0xcd965b) {
  const _0x410af1 = _0x3d1481, _0x194f3d = document[_0x410af1(495)](_0x3b1551 + "Slider"), _0x65917b = document[_0x410af1(495)](_0x3b1551 + "Input");
  if (!_0x194f3d || !_0x65917b) return;
  let _0x44fe8a;
  _0xcd965b === _0x194f3d ? (_0x44fe8a = _0x194f3d.value, _0x65917b.value = _0x44fe8a) : (_0x44fe8a = _0x65917b[_0x410af1(418)], _0x194f3d[_0x410af1(418)] = _0x44fe8a);
  if (_0x3b1551 === _0x410af1(327)) updateFocusRealTime(_0x44fe8a); else _0x3b1551 === _0x410af1(472) && updateBlurRealTime(_0x44fe8a);
}
document.addEventListener(_0x3d1481(488), function () {
  const _0x53e36a = _0x3d1481, _0x3e4b8f = document[_0x53e36a(495)](_0x53e36a(394)), _0x468cd0 = document[_0x53e36a(495)](_0x53e36a(353));
  _0x3e4b8f && _0x3e4b8f[_0x53e36a(383)]("input", function (_0x2d2d67) {
    const _0x3d70ac = _0x53e36a;
    syncFocusBlur(_0x3d70ac(327), _0x3e4b8f);
  });
  _0x468cd0 && _0x468cd0[_0x53e36a(383)]("input", function (_0x30efb4) {
    const _0x10fc6b = _0x53e36a;
    syncFocusBlur(_0x10fc6b(327), _0x468cd0);
  });
  const _0x332fb7 = document[_0x53e36a(495)]("blurSlider"), _0x26f31e = document[_0x53e36a(495)](_0x53e36a(398));
  _0x332fb7 && _0x332fb7.addEventListener(_0x53e36a(401), function (_0x595d53) {
    const _0x1ca279 = _0x53e36a;
    syncFocusBlur(_0x1ca279(472), _0x332fb7);
  }), _0x26f31e && _0x26f31e[_0x53e36a(383)](_0x53e36a(401), function (_0x566d11) {
    const _0x7ca0f3 = _0x53e36a;
    syncFocusBlur(_0x7ca0f3(472), _0x26f31e);
  });
});
var isUpdatingFade = false;
function updateFadeValue(_0x3a96c3) {
  const _0x5b8077 = _0x3d1481;
  if (isUpdatingFade) return;
  isUpdatingFade = true;
  var _0x3a5a06 = parseFloat(_0x3a96c3) || 10;
  if (_0x3a5a06 < 0) _0x3a5a06 = 0;
  if (_0x3a5a06 > 100) _0x3a5a06 = 100;
  currentValues[_0x5b8077(477)] = _0x3a5a06, console[_0x5b8077(354)]("Real-time fade update: " + _0x3a5a06 + "%"), cs.evalScript(_0x5b8077(405) + _0x3a5a06 + _0x5b8077(384)), isUpdatingFade = false;
}
function swapOpacityOrder() {
  const _0x3adc07 = _0x3d1481;
  console[_0x3adc07(354)]("Swap Opacity Order"), cs.evalScript("swapOpacityOrder()");
}
function startKeyframeDOF() {
  const _0x1822ae = _0x3d1481;
  console.log(_0x1822ae(329)), cs[_0x1822ae(461)]("createDepthFadeKeyframes()");
}
function stopKeyframeDOF() {
  const _0x392b13 = _0x3d1481;
  console.log(_0x392b13(343)), cs[_0x392b13(461)]("removeDepthFadeKeyframes()");
}
var isUpdatingCamera = false;
function updateCameraPreset(_0x326288) {
  const _0x41381b = _0x3d1481;
  if (_0x326288 === _0x41381b(496)) {
    console[_0x41381b(354)]("Camera Preset: None (using current slider values)");
    const _0x3c0319 = document[_0x41381b(495)](_0x41381b(492))[_0x41381b(418)] || 40, _0x2f206c = document[_0x41381b(495)](_0x41381b(341))[_0x41381b(418)] || 18;
    cs[_0x41381b(461)](_0x41381b(368)), cs.evalScript("updateCameraShakeAmplitude(" + _0x3c0319 + ")"), cs[_0x41381b(461)](_0x41381b(407) + _0x2f206c + ")");
    return;
  }
  var _0x3e4087, _0x537f5f, _0x51473f;
  switch (_0x326288) {
    case _0x41381b(396):
      _0x3e4087 = 8, _0x537f5f = 6, _0x51473f = 2;
      break;
    case _0x41381b(473):
      _0x3e4087 = 15, _0x537f5f = 8, _0x51473f = 2;
      break;
    case "heavy-handheld":
      _0x3e4087 = 25, _0x537f5f = 12, _0x51473f = 2;
      break;
    case "light-earthquake":
      _0x3e4087 = 12, _0x537f5f = 4, _0x51473f = 1;
      break;
    case "strong-earthquake":
      _0x3e4087 = 35, _0x537f5f = 8, _0x51473f = 1;
      break;
    case _0x41381b(499):
      _0x3e4087 = 10, _0x537f5f = 3, _0x51473f = 3;
      break;
    case _0x41381b(347):
      _0x3e4087 = 20, _0x537f5f = 6, _0x51473f = 3;
      break;
    case _0x41381b(480):
      _0x3e4087 = 6, _0x537f5f = 15, _0x51473f = 4;
      break;
    case _0x41381b(487):
      _0x3e4087 = 18, _0x537f5f = 10, _0x51473f = 4;
      break;
    case _0x41381b(474):
      _0x3e4087 = 30, _0x537f5f = 20, _0x51473f = 5;
      break;
    case _0x41381b(366):
      _0x3e4087 = 60, _0x537f5f = 25, _0x51473f = 5;
      break;
    case _0x41381b(339):
      _0x3e4087 = 12, _0x537f5f = 2, _0x51473f = 6;
      break;
    case _0x41381b(475):
      _0x3e4087 = 20, _0x537f5f = 8, _0x51473f = 6;
      break;
    case _0x41381b(489):
      _0x3e4087 = 8, _0x537f5f = 5, _0x51473f = 7;
      break;
    case "chaotic-random":
      _0x3e4087 = 40, _0x537f5f = 15, _0x51473f = 7;
      break;
    case _0x41381b(459):
      _0x3e4087 = 5, _0x537f5f = 12, _0x51473f = 8;
      break;
    case "old-projector":
      _0x3e4087 = 12, _0x537f5f = 18, _0x51473f = 8;
      break;
    case "precision-x":
      _0x3e4087 = 15, _0x537f5f = 8, _0x51473f = 9;
      break;
    case "precision-y":
      _0x3e4087 = 15, _0x537f5f = 8, _0x51473f = 9;
      break;
    default:
      _0x3e4087 = 40, _0x537f5f = 18, _0x51473f = 0;
  }
  const _0x36ac7e = document[_0x41381b(495)](_0x41381b(465)), _0xd362c7 = document.getElementById(_0x41381b(492)), _0x32b9b2 = document[_0x41381b(495)](_0x41381b(402)), _0x196221 = document[_0x41381b(495)](_0x41381b(341));
  _0x36ac7e && _0xd362c7 && (_0x36ac7e[_0x41381b(418)] = _0x3e4087, _0xd362c7.value = _0x3e4087, updateCameraAmp(_0x3e4087)), _0x32b9b2 && _0x196221 && (_0x32b9b2[_0x41381b(418)] = _0x537f5f, _0x196221[_0x41381b(418)] = _0x537f5f, updateCameraFreq(_0x537f5f)), cs[_0x41381b(461)](_0x41381b(444) + _0x51473f + ")"), console.log("🎛️ Camera preset: " + _0x326288 + _0x41381b(436) + _0x3e4087 + _0x41381b(372) + _0x537f5f + _0x41381b(412) + _0x51473f + ")");
}
function updateCameraAmp(_0x22aaff) {
  const _0x45988c = _0x3d1481;
  if (isUpdatingCamera) return;
  isUpdatingCamera = true;
  var _0x23f04f = parseFloat(_0x22aaff) || 40;
  if (_0x23f04f < 0) _0x23f04f = 0;
  if (_0x23f04f > 100) _0x23f04f = 100;
  cs.evalScript(_0x45988c(453) + _0x23f04f + ")");
  const _0x3a654d = document[_0x45988c(495)](_0x45988c(446));
  _0x3a654d && _0x3a654d[_0x45988c(418)] !== _0x45988c(496) && (_0x3a654d[_0x45988c(418)] = _0x45988c(496), console[_0x45988c(354)]("🎛️ Camera preset reset to None")), isUpdatingCamera = false;
}
function updateCameraFreq(_0x325ec3) {
  const _0x428b5d = _0x3d1481;
  if (isUpdatingCamera) return;
  isUpdatingCamera = true;
  var _0x4e70e9 = parseFloat(_0x325ec3) || 18;
  if (_0x4e70e9 < 0) _0x4e70e9 = 0;
  if (_0x4e70e9 > 30) _0x4e70e9 = 30;
  _0x4e70e9 = Math[_0x428b5d(448)](_0x4e70e9 * 10) / 10, cs[_0x428b5d(461)](_0x428b5d(407) + _0x4e70e9 + ")");
  const _0x517db9 = document[_0x428b5d(495)](_0x428b5d(446));
  _0x517db9 && _0x517db9[_0x428b5d(418)] !== _0x428b5d(496) && (_0x517db9[_0x428b5d(418)] = "none", console[_0x428b5d(354)]("Camera preset reset to None")), isUpdatingCamera = false;
}
function syncCamera(_0x29d157, _0x5c0c5c) {
  const _0x2483a7 = _0x3d1481, _0x72feee = document[_0x2483a7(495)]("camera" + _0x29d157[_0x2483a7(439)](0)[_0x2483a7(479)]() + _0x29d157[_0x2483a7(457)](1) + "Slider"), _0x456e8c = document[_0x2483a7(495)]("camera" + _0x29d157[_0x2483a7(439)](0).toUpperCase() + _0x29d157[_0x2483a7(457)](1) + _0x2483a7(351));
  if (!_0x72feee || !_0x456e8c) return;
  let _0x49e6d0;
  _0x5c0c5c === _0x72feee ? (_0x49e6d0 = _0x72feee[_0x2483a7(418)], _0x456e8c[_0x2483a7(418)] = _0x49e6d0) : (_0x49e6d0 = _0x456e8c[_0x2483a7(418)], _0x72feee[_0x2483a7(418)] = _0x49e6d0);
  if (_0x29d157 === _0x2483a7(360)) updateCameraAmp(_0x49e6d0); else _0x29d157 === _0x2483a7(386) && updateCameraFreq(_0x49e6d0);
}
function applyCameraShakeMain() {
  const _0x36efda = _0x3d1481;
  console[_0x36efda(354)](_0x36efda(476)), cs[_0x36efda(461)](_0x36efda(470));
}
function removeCameraShakeMain() {
  const _0x4d818a = _0x3d1481;
  console[_0x4d818a(354)](_0x4d818a(365)), cs.evalScript("removeCameraShakeMain()");
}
document.addEventListener(_0x3d1481(488), function () {
  const _0x2d3c9b = _0x3d1481, _0x5913b1 = document[_0x2d3c9b(495)](_0x2d3c9b(446)), _0x4ee145 = document.getElementById(_0x2d3c9b(465)), _0x1829c8 = document[_0x2d3c9b(495)](_0x2d3c9b(492)), _0x360afe = document[_0x2d3c9b(495)](_0x2d3c9b(402)), _0x17c305 = document[_0x2d3c9b(495)]("cameraFreqInput");
  _0x5913b1 && _0x5913b1.addEventListener(_0x2d3c9b(352), function () {
    const _0x1c62cb = _0x2d3c9b;
    updateCameraPreset(_0x5913b1[_0x1c62cb(418)]);
  }), _0x4ee145 && _0x4ee145[_0x2d3c9b(383)](_0x2d3c9b(401), function () {
    const _0x35cd66 = _0x2d3c9b;
    syncCamera(_0x35cd66(360), _0x4ee145);
  }), _0x1829c8 && _0x1829c8.addEventListener(_0x2d3c9b(401), function () {
    const _0x37aa04 = _0x2d3c9b;
    syncCamera(_0x37aa04(360), _0x1829c8);
  }), _0x360afe && _0x360afe[_0x2d3c9b(383)]("input", function () {
    const _0x116678 = _0x2d3c9b;
    syncCamera(_0x116678(386), _0x360afe);
  }), _0x17c305 && _0x17c305[_0x2d3c9b(383)](_0x2d3c9b(401), function () {
    syncCamera("freq", _0x17c305);
  }), console[_0x2d3c9b(354)](_0x2d3c9b(463));
});
function setupCameraRig() {
  const _0x13caf1 = _0x3d1481;
  console[_0x13caf1(354)](_0x13caf1(414)), cs[_0x13caf1(461)](_0x13caf1(390));
}
function parentCamera() {
  const _0x5401bb = _0x3d1481;
  console[_0x5401bb(354)](_0x5401bb(325)), cs.evalScript(_0x5401bb(403));
}
function resetAll() {
  const _0x4b3db7 = _0x3d1481;
  console[_0x4b3db7(354)](_0x4b3db7(469)), cs[_0x4b3db7(461)](_0x4b3db7(456));
}
function getCameraInfo() {
  const _0x299be9 = _0x3d1481;
  console.log("ℹ️ Get Camera Rig Info"), cs[_0x299be9(461)]("getCameraRigInfo()");
}
document[_0x3d1481(383)](_0x3d1481(488), function () {
  const _0x397618 = _0x3d1481, _0x3edcad = document[_0x397618(467)]('button[onclick="setupCameraRig()"]'), _0x25361d = document.querySelector('button[onclick="parentCamera()"]'), _0x181d50 = document.querySelector(_0x397618(364)), _0x40a9aa = document.querySelector(_0x397618(404));
  if (_0x3edcad) console[_0x397618(354)](_0x397618(361));
  if (_0x25361d) console.log(_0x397618(442));
  if (_0x181d50) console[_0x397618(354)]("✅ Reset button found");
  if (_0x40a9aa) console.log("✅ Info button found");
  console[_0x397618(354)](_0x397618(326));
});
function getCameraInfo() {
  const _0x10e4cb = _0x3d1481;
  console[_0x10e4cb(354)](_0x10e4cb(387)), cs[_0x10e4cb(461)]("getCameraInfo()");
}
function showAbout() {
  const _0xb7f7e0 = _0x3d1481;
  console[_0xb7f7e0(354)](_0xb7f7e0(392)), cs[_0xb7f7e0(461)]("showAbout()");
}
document.addEventListener("DOMContentLoaded", function () {
  const _0x4e543f = _0x3d1481;
  document[_0x4e543f(383)](_0x4e543f(455), function (_0x463464) {
    const _0xcd0a3f = _0x4e543f;
    return _0x463464[_0xcd0a3f(375)](), false;
  }), document[_0x4e543f(383)](_0x4e543f(416), function (_0x58abbd) {
    const _0x3606fa = _0x4e543f;
    if (_0x58abbd.target.tagName !== _0x3606fa(413) && _0x58abbd[_0x3606fa(430)][_0x3606fa(482)] !== _0x3606fa(338)) return _0x58abbd.preventDefault(), false;
  }), document[_0x4e543f(383)](_0x4e543f(408), function (_0x4f6aad) {
    const _0x387e3f = _0x4e543f;
    return _0x4f6aad[_0x387e3f(375)](), false;
  });
});
function applySmoothStandard() {
  const _0x21f797 = _0x3d1481;
  console[_0x21f797(354)](_0x21f797(423)), cs[_0x21f797(461)](_0x21f797(332));
}
function applyEaseOut() {
  const _0xb4dcc8 = _0x3d1481;
  console.log(_0xb4dcc8(454)), cs.evalScript(_0xb4dcc8(406));
}
function applyEaseIn() {
  const _0x54281a = _0x3d1481;
  console[_0x54281a(354)]("Apply Ease In (slow to fast)"), cs[_0x54281a(461)](_0x54281a(497));
}
function autofocusClick() {
  const _0x29b95f = _0x3d1481;
  console[_0x29b95f(354)]("Autofocus (10f)"), cs[_0x29b95f(461)]("autofocusSelectedLayer()");
}
function apc() {
  const _0x5cefda = _0x3d1481;
  cs[_0x5cefda(461)](_0x5cefda(369));
}
console[_0x3d1481(354)]("Camera3D Toolkit Pro v2.2 - index.js loaded"), console[_0x3d1481(354)]("Premium Features: Orientation-based Animation, Smart Controller Detection"), console[_0x3d1481(354)](_0x3d1481(452));
