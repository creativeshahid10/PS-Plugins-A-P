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

function alignAP(pos) {
    setStatus("Aligning anchor point to " + pos + "...");
    cs.evalScript("PixelSquadAE.alignAnchorPoint('" + pos + "')", function(res) {
        setStatus(res);
    });
}

function easeCurve(curve) {
    setStatus("Applying " + curve + " curve...");
    cs.evalScript("PixelSquadAE.applyEasingCurve('" + curve + "')", function(res) {
        setStatus(res);
    });
}

function createNull() {
    setStatus("Creating connected controller Null...");
    cs.evalScript("PixelSquadAE.createNullController()", function(res) {
        setStatus(res);
    });
}

function stagger(frames) {
    setStatus("Staggering layers by " + frames + " frames...");
    cs.evalScript("PixelSquadAE.staggerLayers(" + frames + ")", function(res) {
        setStatus(res);
    });
}