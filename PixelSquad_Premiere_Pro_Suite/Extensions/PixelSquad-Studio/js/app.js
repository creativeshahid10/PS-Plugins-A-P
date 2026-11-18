/**
 * ====================================================================
 * PixelSquad Creative Suite
 * Copyright (C) 2026 PixelSquad. All Rights Reserved.
 * Author: Mohammed Shahid <hello@pixelsquad.in>
 * Proprietary & Confidential. Unauthorized copying, distribution,
 * modification, or reverse engineering is strictly prohibited.
 * ====================================================================
 */

var cs = new CSInterface();

function setStatus(msg) {
    document.getElementById("status").innerText = msg;
}

function createAdj(preset) {
    setStatus("Generating " + preset + " Adjustment Layer...");
    cs.evalScript("PixelSquadPPro.createAdjustmentLayer('" + preset + "')", function(res) {
        setStatus(res);
    });
}

function applyMotion(type) {
    setStatus("Applying " + type + "...");
    cs.evalScript("PixelSquadPPro.applyCameraMotion('" + type + "')", function(res) {
        setStatus(res);
    });
}

function applyFX(fx) {
    setStatus("Applying Native " + fx + "...");
    cs.evalScript("PixelSquadPPro.applyNativeEffect('" + fx + "')", function(res) {
        setStatus(res);
    });
}

function splitSilence() {
    setStatus("Processing playhead split...");
    cs.evalScript("PixelSquadPPro.splitSilenceAtPlayhead()", function(res) {
        setStatus(res);
    });
}