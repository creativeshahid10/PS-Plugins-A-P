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
 * TXTFX — Apply Text FX (AEP Library, Silent Import)
 */

var extensionRoot = Folder($.fileName).parent.parent.parent.fsName;

function getTXTFXFolder() {
    for (var i = 1; i <= app.project.numItems; i++) {
        var item = app.project.item(i);
        if (item instanceof FolderItem && item.name === "TXTFX.aep") {
            return item;
        }
    }
    return null;
}
function getCameraLayer(comp) {
    for (var i = 1; i <= comp.numLayers; i++) {
        var l = comp.layer(i);
        if (l instanceof CameraLayer) {
            return l;
        }
    }
    return null;
}

function applyTextFX(fxName, lyricsText) {
    if (fxName.indexOf("pro_") === 0) {
        applyProceduralTextFX(fxName, lyricsText);
        return;
    }
    var activeComp = app.project.activeItem;

    if (!(activeComp && activeComp instanceof CompItem)) {
        alert("Open a composition first");
        return;
    }


var txFolder = getTXTFXFolder();

if (!txFolder) {
    var aepFile = new File(extensionRoot + "/assets/TXTFX.aep");

    if (!aepFile.exists) {
        alert("TXTFX.aep not found");
        return;
    }

    app.project.importFile(new ImportOptions(aepFile));

    // wait for AE to register imported items
    app.scheduleTask(
        "applyTextFX_apply('" + fxName + "','" + lyricsText.replace(/'/g, "\\'") + "')",
        150,
        false
    );
} else {
    applyTextFX_apply(fxName, lyricsText);
}
}

function applyTextFX_apply(fxName, lyricsText) {
    app.beginUndoGroup("PSText Apply");

    var activeComp = app.project.activeItem;
    if (!(activeComp && activeComp instanceof CompItem)) {
        alert("Lost active composition");
        app.endUndoGroup();
        return;
    }

// FX → Comp mapping
    var fxMap = {
    "txt1": "TXT 1",
    "txt2": "TXT 2",
    "txt3": "TXT 3",
    "txt4": "TXT 4",
    "txt5": "TXT 5",
    "txt6": "TXT 6",
    "txt7": "TXT 7",
    "txt8": "TXT 8",
    "txt9": "TXT 9",
    "txt10": "TXT 10",
    "txt11": "TXT 11",
    "txt12": "TXT 12",
    "txt13": "TXT 13",
    "txt14": "TXT 14",
    "txt15": "TXT 15",
    "txt16": "TXT 16",
    "txt17": "TXT 17",
    "txt18": "TXT 18",
    "txt19": "TXT 19",
    "txt20": "TXT 20",
    "txt21": "TXT 21",
    "txt22": "TXT 22"
};

    var sourceCompName = fxMap[fxName];
    if (!sourceCompName) {
        alert("This animation is not available yet");
        app.endUndoGroup();
        return;
    }

    // Find source comp (anywhere in project)
    var sourceComp = null;
    for (var i = 1; i <= app.project.numItems; i++) {
        var item = app.project.item(i);
        if (item instanceof CompItem && item.name === sourceCompName) {
            sourceComp = item;
            break;
        }
    }

    if (!sourceComp) {
        alert("Source animation not found");
        app.endUndoGroup();
        return;
    }

// Deselect all layers in active comp
for (var i = 1; i <= activeComp.numLayers; i++) {
    activeComp.layer(i).selected = false;
}
var uniqueComp = sourceComp.duplicate();
var displayName = sourceCompName.replace("Lyrics", "PSText").replace("TXT", "PSText");
var count = 0;
for (var i = 1; i <= app.project.numItems; i++) {
    if (app.project.item(i).name.indexOf(displayName) === 0) count++;
}
uniqueComp.name = displayName + (count > 1 ? " (" + count + ")" : "");
var insertedLayer = activeComp.layers.add(uniqueComp);insertedLayer.startTime = activeComp.time;
// ── Auto-scale to match comp resolution ──────────────────────────────
var scaleFactor = (activeComp.width / uniqueComp.width) * 100;
if (scaleFactor !== 100) {
    insertedLayer.property("Scale").setValue([scaleFactor, scaleFactor, scaleFactor]);
}
// Parse comma-separated lyrics
var words = [];
if (lyricsText && lyricsText.length > 0) {
    var split = lyricsText.split(",");
    for (var i = 0; i < split.length; i++) {
        var clean = split[i].replace(/^\s+|\s+$/g, "");
        if (clean.length > 0) words.push(clean);
    }
}

// Only replace text if custom words were entered (preserves default preset text if blank)
if (words.length > 0) {
    if (words.length > 3) words = words.slice(0, 3);
    var nestedComp = insertedLayer.source;
    var textIndex = 0;

    for (var i = 1; i <= nestedComp.numLayers; i++) {
        var layer = nestedComp.layer(i);
        if (layer instanceof TextLayer && textIndex < words.length) {
            var textProp = layer.property("Source Text");
            var textDoc = textProp.value;
            textDoc.text = words[textIndex];
            textProp.setValue(textDoc);
            textIndex++;
        }
    }
}

    app.endUndoGroup();
}
function buildLyricsFromTrackedSolid() {
    var comp = app.project.activeItem;

    if (!(comp && comp instanceof CompItem)) {
        alert("Open the tracked composition.");
        return;
    }

    var cam = getCameraLayer(comp);
    if (!cam) {
        alert("Camera not found. Create camera first.");
        return;
    }

    // ── Require user to select the solid tracking point ──────────────────
    if (comp.selectedLayers.length !== 1) {
        alert("Select your tracking solid in the timeline first, then click Build From Tracking Point.");
        return;
    }

    var solidLayer = comp.selectedLayers[0];

    if (
        !(solidLayer instanceof AVLayer) ||
        !(solidLayer.source && solidLayer.source.mainSource instanceof SolidSource) ||
        !solidLayer.threeDLayer
    ) {
        alert("Selected layer is not a 3D solid.\nSelect the solid created by your camera tracker and try again.");
        return;
    }

    app.beginUndoGroup("PSText Build Lyrics From Track");
// ── Trim solid to length of layer underneath it ───────────────────────
    try {
        var layerBelow = comp.layer(solidLayer.index + 1);
        solidLayer.inPoint  = layerBelow.inPoint;
        solidLayer.outPoint = layerBelow.outPoint;
    } catch(e) {}
    
    // ── Auto-find the most recently added, unlocked PSText/TXT layer ─────
    var lyricsLayer = null;
    for (var i = 1; i <= comp.numLayers; i++) {
        var l = comp.layer(i);
        if (
            l instanceof AVLayer &&
            l.source instanceof CompItem &&
            (l.source.name.indexOf("PSText") === 0 || l.source.name.indexOf("TXT") === 0) &&
            l.comment !== "PSTEXT_LOCKED"
        ) {
            lyricsLayer = l;
            break;
        }
    }

    if (!lyricsLayer) {
        alert("No unlocked PSText layer found.\nApply an animation from the PSText tab first.");
        app.endUndoGroup();
        return;
    }

    if (!lyricsLayer.threeDLayer) {
        lyricsLayer.threeDLayer = true;
    }

    // Copy position from selected solid
    var pos = solidLayer.property("Position").value;
    lyricsLayer.property("Position").setValue(pos);

    // Scale based on camera distance
    var camPos = cam.property("Position").value;
    var d = Math.sqrt(
        Math.pow(pos[0] - camPos[0], 2) +
        Math.pow(pos[1] - camPos[1], 2) +
        Math.pow(pos[2] - camPos[2], 2)
    );

    var referenceDistance = 1000;
    var referenceScale = 100;
    var s = (d / referenceDistance) * referenceScale;
    lyricsLayer.property("Scale").setValue([s, s, s]);

    solidLayer.enabled = false;
    lyricsLayer.comment = "PSTEXT_LOCKED";

    app.endUndoGroup();
}
function unlockLyricsLayer(layer) {
    layer.comment = "";
}

function add3DCameraTrackerToSelectedLayer() {
    var comp = app.project.activeItem;

    if (!(comp && comp instanceof CompItem)) {
        alert("Open a composition first.");
        return;
    }

    if (comp.selectedLayers.length !== 1) {
        alert("Select ONE footage layer.");
        return;
    }

    var layer = comp.selectedLayers[0];

    if (!(layer instanceof AVLayer)) {
        alert("Selected layer must be footage.");
        return;
    }

    app.beginUndoGroup("Add 3D Camera Tracker");

    // VERY IMPORTANT: layer must be selected + active
    comp.selectedLayers[0].selected = true;

    // Run menu command: Animation → Track Camera
    var cmd = app.findMenuCommandId("Track Camera");

    if (cmd !== 0) {
        app.executeCommand(cmd);
    } else {
        alert("Track Camera command not found.");
    }

    app.endUndoGroup();
}

/* ═══════════════════════════════════════════════════════════════════════════
   PIXEL SQUAD 52+ MASTER TYPOGRAPHY PROCEDURAL ENGINE (REFINED V3)
   ═══════════════════════════════════════════════════════════════════════════ */

function getPresetDisplayName(fxName) {
    var map = {
        // Viral Reels (8)
        "pro_reels1": "Viral Bounce Pop",
        "pro_reels2": "Neon Tube Glow",
        "pro_reels3": "Boxed Sticker Pop",
        "pro_reels4": "Fire Impact Caption",
        "pro_reels5": "Karaoke Word Pop",
        "pro_reels6": "Marker Pen Swipe",
        "pro_reels7": "Chat Bubble Pop",
        "pro_reels8": "Emoji Text Bounce",
        // Cinematic & Luxury (8)
        "pro_cinema1": "Atmospheric Blur",
        "pro_cinema2": "Deep Space Drift",
        "pro_cinema3": "Luxury Gold Shimmer",
        "pro_cinema4": "Sand Dust Disperse",
        "pro_cinema5": "3D Blockbuster Push",
        "pro_cinema6": "Film Burn 16mm",
        "pro_cinema7": "Cinematic Scope Wipe",
        "pro_cinema8": "Luma Cutout",
        // Modern Kinetic (8)
        "pro_kinetic1": "3D Kinetic Flip",
        "pro_kinetic2": "Slot Machine Odo",
        "pro_kinetic3": "Liquid Color Wave",
        "pro_kinetic4": "Rubber Band Elastic",
        "pro_kinetic5": "Gravity Drop Slam",
        "pro_kinetic6": "Infinite Marquee",
        "pro_kinetic7": "Stagger Wave Ripple",
        "pro_kinetic8": "Split Slide Stagger",
        // Glitch, Cyber & Gaming (8)
        "pro_glitch1": "RGB Chromatic Glitch",
        "pro_glitch2": "Cyber Decoder",
        "pro_glitch3": "CRT VHS Distortion",
        "pro_glitch4": "Hologram HUD Target",
        "pro_glitch5": "Matrix Digital Rain",
        "pro_glitch6": "8-Bit Pixel Mosaic",
        "pro_glitch7": "Bad TV Sliced Tear",
        "pro_glitch8": "Cyber Wireframe",
        // Minimal & Corporate (6)
        "pro_minimal1": "Smooth Line Wipe",
        "pro_minimal2": "Draw Underline",
        "pro_minimal3": "Number Counter",
        "pro_minimal4": "Code Terminal",
        "pro_minimal5": "Podcast Float",
        "pro_minimal6": "Stagger Fade Up"
    };
    return map[fxName] || "Motion Text";
}

function applyProceduralTextFX(fxName, lyricsText) {
    var activeComp = app.project.activeItem;
    if (!(activeComp && activeComp instanceof CompItem)) {
        alert("Open a composition first.");
        return;
    }

    app.beginUndoGroup("PSText " + getPresetDisplayName(fxName));

    // Parse words or fallback
    var words = [];
    if (lyricsText && lyricsText.length > 0) {
        var split = lyricsText.split(",");
        for (var i = 0; i < split.length; i++) {
            var clean = split[i].replace(/^\s+|\s+$/g, "");
            if (clean.length > 0) words.push(clean);
        }
    }

    // Curated Fallbacks
    if (words.length === 0) {
        if (fxName.indexOf("pro_reels") === 0) words = ["VIRAL", "REELS", "CAPTION"];
        else if (fxName.indexOf("pro_cinema") === 0) words = ["CINEMATIC", "TITLES"];
        else if (fxName.indexOf("pro_kinetic") === 0) words = ["KINETIC", "MOTION"];
        else if (fxName.indexOf("pro_glitch") === 0) words = ["CYBERPUNK", "SYSTEM"];
        else if (fxName.indexOf("pro_minimal") === 0) words = ["ELEGANT", "MINIMAL"];
        else words = ["PIXEL", "SQUAD"];
    }

    var compW = activeComp.width;
    var compH = activeComp.height;
    var duration = 4.0;
    var fps = activeComp.frameRate || 30;

    var compName = "PSText " + getPresetDisplayName(fxName);
    var count = 0;
    for (var i = 1; i <= app.project.numItems; i++) {
        if (app.project.item(i).name.indexOf(compName) === 0) count++;
    }
    if (count > 0) compName += " (" + (count + 1) + ")";

    var newComp = app.project.items.addComp(compName, compW, compH, 1, duration, fps);

    // Expressions Library
    var springScaleExpr = 
        "n = 0;\n" +
        "if (numKeys > 0){ n = nearestKey(time).index; if (key(n).time > time) n--; }\n" +
        "if (n > 0){\n" +
        "  t = time - key(n).time;\n" +
        "  if (t >= 0 && t < 1.5){\n" +
        "    v = velocityAtTime(key(n).time - thisComp.frameDuration/10);\n" +
        "    amp = 0.12; freq = 4.0; decay = 7.0;\n" +
        "    value + v * amp * Math.sin(freq * t * 2 * Math.PI) / Math.exp(decay * t);\n" +
        "  } else { value; }\n" +
        "} else { value; }";

    var springRotExpr = 
        "n = 0;\n" +
        "if (numKeys > 0){ n = nearestKey(time).index; if (key(n).time > time) n--; }\n" +
        "if (n > 0){\n" +
        "  t = time - key(n).time;\n" +
        "  if (t >= 0 && t < 1.5){\n" +
        "    v = velocityAtTime(key(n).time - thisComp.frameDuration/10);\n" +
        "    amp = 0.10; freq = 3.5; decay = 6.0;\n" +
        "    value + v * amp * Math.sin(freq * t * 2 * Math.PI) / Math.exp(decay * t);\n" +
        "  } else { value; }\n" +
        "} else { value; }";

    // BULLETPROOF TEXT FACTORY (RESET ALL PROPERTIES TO PREVENT HAIL-THIN FONTS & STRAY STROKES)
    function createCleanText(textStr, fSize, fillColor, customFont, customTracking) {
        var t = newComp.layers.addText(textStr);
        var doc = t.property("Source Text").value;

        // Pick heavy, readable bold fonts
        var fontToUse = customFont || "Impact";
        try { doc.font = fontToUse; } catch(e1) {
            try { doc.font = "Arial-BoldMT"; } catch(e2) {
                try { doc.font = "Arial"; } catch(e3) {}
            }
        }

        doc.fontSize = fSize;
        doc.applyFill = true;
        doc.fillColor = fillColor || [1, 1, 1];

        // Explicitly turn OFF stroke by default (never inherit stray cyan/blue stroke!)
        doc.applyStroke = false;
        doc.strokeWidth = 0;

        // Controlled tracking (never inherit 140 tracking unless asked)
        doc.tracking = (typeof customTracking !== "undefined") ? customTracking : 10;
        doc.justification = ParagraphJustification.CENTER_JUSTIFY;

        t.property("Source Text").setValue(doc);

        // Center Anchor Point dynamically
        t.property("Anchor Point").expression = "r = sourceRectAtTime(); [r.left + r.width/2, r.top + r.height/2];";
        t.property("Position").setValue([compW / 2, compH / 2]);

        return t;
    }

    // ═════════════════════════════════════════════════════════════════════════
    // CATEGORY 1: VIRAL REELS (8)
    // ═════════════════════════════════════════════════════════════════════════
    if (fxName === "pro_reels1") {
        // 1. Viral Bounce Pop
        var fSize = Math.round(compW * 0.085);
        var tLayer = createCleanText(words.join(" "), fSize, [1.0, 0.9, 0.0], "Impact", 10);
        var tDoc = tLayer.property("Source Text").value;
        tDoc.applyStroke = true;
        tDoc.strokeColor = [0, 0, 0];
        tDoc.strokeWidth = Math.round(fSize * 0.12);
        tDoc.strokeOverFill = false;
        tLayer.property("Source Text").setValue(tDoc);

        var sProp = tLayer.property("Scale");
        sProp.setValueAtTime(0, [0, 0]);
        sProp.setValueAtTime(0.22, [100, 100]);
        sProp.expression = springScaleExpr;

        try {
            var ds = tLayer.property("Effects").addProperty("ADBE Drop Shadow");
            ds.property("Shadow Opacity").setValue(255);
            ds.property("Distance").setValue(14);
            ds.property("Softness").setValue(0);
        } catch(e) {}

    } else if (fxName === "pro_reels2") {
        // 2. Neon Tube Glow
        var fSize = Math.round(compW * 0.07);
        var tLayer = createCleanText(words.join("  "), fSize, [1, 1, 1], "Impact", 120);
        var tDoc = tLayer.property("Source Text").value;
        tDoc.applyStroke = true;
        tDoc.strokeColor = [0.0, 0.95, 1.0];
        tDoc.strokeWidth = Math.max(3, Math.round(fSize * 0.04));
        tDoc.strokeOverFill = false;
        tLayer.property("Source Text").setValue(tDoc);

        try {
            var g1 = tLayer.property("Effects").addProperty("ADBE Glo2");
            g1.property("Glow Threshold").setValue(50);
            g1.property("Glow Radius").setValue(16);
            g1.property("Glow Intensity").setValue(1.8);
            g1.property("Composite Original").setValue(2);
            g1.property("Glow Colors").setValue(1);
            g1.property("Glow Intensity").expression = "1.8 + Math.sin(time * 10) * 0.35 + (random(-0.15, 0.15) * (random() > 0.88 ? 1 : 0));";

            var g2 = tLayer.property("Effects").addProperty("ADBE Glo2");
            g2.property("Glow Threshold").setValue(45);
            g2.property("Glow Radius").setValue(65);
            g2.property("Glow Intensity").setValue(1.0);
            g2.property("Composite Original").setValue(2);
            g2.property("Glow Colors").setValue(1);
        } catch(e) {}

        var sProp = tLayer.property("Scale");
        sProp.setValueAtTime(0, [60, 60]);
        sProp.setValueAtTime(0.25, [100, 100]);
        sProp.expression = springScaleExpr;

    } else if (fxName === "pro_reels3") {
        // 3. Boxed Sticker Pop (EXACT SOURCERECT BOUNDS)
        var textStr = words.join(" ");
        var fSize = Math.round(compW * 0.075);
        var tLayer = createCleanText(textStr, fSize, [0.05, 0.05, 0.08], "Impact", 15);

        // Exact text bounds
        var r = tLayer.sourceRectAtTime(0, false);
        var boxW = r.width + 70;
        var boxH = r.height + 30;

        var shapeLayer = newComp.layers.addShape();
        shapeLayer.name = "Sticker Background";
        var contents = shapeLayer.property("Contents");
        var group = contents.addProperty("ADBE Vector Group");
        var gContents = group.property("Contents");

        var rect = gContents.addProperty("ADBE Vector Shape - Rect");
        rect.property("Size").setValue([boxW, boxH]);
        rect.property("Roundness").setValue(28);

        var fill = gContents.addProperty("ADBE Vector Graphic - Fill");
        fill.property("Color").setValue([1.0, 0.92, 0.02]); // Vibrant Yellow

        var stroke = gContents.addProperty("ADBE Vector Graphic - Stroke");
        stroke.property("Color").setValue([0, 0, 0]);
        stroke.property("Stroke Width").setValue(5);

        try {
            var ds = shapeLayer.property("Effects").addProperty("ADBE Drop Shadow");
            ds.property("Shadow Opacity").setValue(255);
            ds.property("Distance").setValue(14);
            ds.property("Softness").setValue(0);
        } catch(e) {}

        shapeLayer.property("Position").setValue([compW / 2, compH / 2]);
        shapeLayer.moveAfter(tLayer);
        tLayer.parent = shapeLayer;

        shapeLayer.property("Scale").setValueAtTime(0, [0, 0]);
        shapeLayer.property("Scale").setValueAtTime(0.24, [100, 100]);
        shapeLayer.property("Scale").expression = springScaleExpr;

        shapeLayer.property("Rotation").setValueAtTime(0, -10);
        shapeLayer.property("Rotation").setValueAtTime(0.26, -2);
        shapeLayer.property("Rotation").expression = springRotExpr;

    } else if (fxName === "pro_reels4") {
        // 4. Fire Impact Caption
        var fSize = Math.round(compW * 0.085);
        var tLayer = createCleanText(words.join(" "), fSize, [1.0, 0.35, 0.0], "Impact", 10);
        var tDoc = tLayer.property("Source Text").value;
        tDoc.applyStroke = true;
        tDoc.strokeColor = [0.1, 0, 0];
        tDoc.strokeWidth = Math.round(fSize * 0.12);
        tDoc.strokeOverFill = false;
        tLayer.property("Source Text").setValue(tDoc);

        var sProp = tLayer.property("Scale");
        sProp.setValueAtTime(0, [220, 220]);
        sProp.setValueAtTime(0.25, [100, 100]);
        sProp.expression = springScaleExpr;
        tLayer.property("Opacity").setValueAtTime(0, 0);
        tLayer.property("Opacity").setValueAtTime(0.12, 100);

    } else if (fxName === "pro_reels5") {
        // 5. Karaoke Word Pop
        var textStr = words.join(" ");
        var fSize = Math.round(compW * 0.075);
        var tLayer = createCleanText(textStr, fSize, [1, 1, 1], "Impact", 15);
        var anim = tLayer.property("Text").property("Animators").addProperty("ADBE Text Animator");
        var fillCol = anim.property("ADBE Text Animator Properties").addProperty("ADBE Text Fill Color");
        fillCol.setValue([0.2, 1.0, 0.3]);
        var scaleA = anim.property("ADBE Text Animator Properties").addProperty("ADBE Text Scale 3D");
        scaleA.setValue([120, 120, 100]);

        var selector = anim.property("ADBE Text Selectors").addProperty("ADBE Text Selector");
        selector.property("Start").setValueAtTime(0, 0);
        selector.property("Start").setValueAtTime(2.0, 100);
        selector.property("End").setValueAtTime(0, 33);
        selector.property("End").setValueAtTime(2.0, 100);

    } else if (fxName === "pro_reels6") {
        // 6. Marker Pen Swipe (EXACT SOURCERECT & REAL LEFT-TO-RIGHT SWIPE)
        var textStr = words.join(" ");
        var fSize = Math.round(compW * 0.07);
        var tLayer = createCleanText(textStr, fSize, [0.08, 0.08, 0.1], "Impact", 15);

        // Exact measured bounds of text
        var r = tLayer.sourceRectAtTime(0, false);
        var boxW = r.width + 60;
        var boxH = r.height + 24;

        var marker = newComp.layers.addShape();
        marker.name = "Highlighter Marker";
        var group = marker.property("Contents").addProperty("ADBE Vector Group");
        var gContents = group.property("Contents");

        var rect = gContents.addProperty("ADBE Vector Shape - Rect");
        rect.property("Size").setValue([boxW, boxH]);
        rect.property("Roundness").setValue(10);

        var fill = gContents.addProperty("ADBE Vector Graphic - Fill");
        fill.property("Color").setValue([0.98, 1.0, 0.0]); // Neon Highlighter Yellow

        marker.moveAfter(tLayer);

        // Position marker left-aligned to text and swipe left-to-right!
        marker.property("Anchor Point").setValue([-boxW / 2, 0]);
        marker.property("Position").setValue([(compW / 2) - (boxW / 2), compH / 2]);

        var sProp = marker.property("Scale");
        sProp.setValueAtTime(0.05, [0, 100]);
        sProp.setValueAtTime(0.35, [100, 100]);
        sProp.expression = springScaleExpr;

    } else if (fxName === "pro_reels7") {
        // 7. Chat Bubble Pop (EXACT SOURCERECT)
        var textStr = words.join(" ");
        var fSize = Math.round(compW * 0.065);
        var tLayer = createCleanText(textStr, fSize, [0.05, 0.08, 0.12], "Arial-BoldMT", 10);

        var r = tLayer.sourceRectAtTime(0, false);
        var boxW = r.width + 60;
        var boxH = r.height + 28;

        var bubble = newComp.layers.addShape();
        bubble.name = "Chat Bubble";
        var group = bubble.property("Contents").addProperty("ADBE Vector Group");
        var rect = group.property("Contents").addProperty("ADBE Vector Shape - Rect");
        rect.property("Size").setValue([boxW, boxH]);
        rect.property("Roundness").setValue(20);

        var fill = group.property("Contents").addProperty("ADBE Vector Graphic - Fill");
        fill.property("Color").setValue([0.92, 0.94, 0.98]);

        bubble.property("Position").setValue([compW / 2, compH / 2]);
        bubble.moveAfter(tLayer);
        tLayer.parent = bubble;

        bubble.property("Scale").setValueAtTime(0, [0, 0]);
        bubble.property("Scale").setValueAtTime(0.25, [100, 100]);
        bubble.property("Scale").expression = springScaleExpr;

    } else if (fxName === "pro_reels8") {
        // 8. Emoji Text Bounce
        var tLayer = createCleanText(words.join(" "), Math.round(compW * 0.08), [1.0, 0.85, 0.1], "Impact", 15);
        var sProp = tLayer.property("Scale");
        sProp.setValueAtTime(0, [0, 0]);
        sProp.setValueAtTime(0.18, [130, 70]);
        sProp.setValueAtTime(0.32, [85, 115]);
        sProp.setValueAtTime(0.45, [100, 100]);
        sProp.expression = springScaleExpr;

    // ═════════════════════════════════════════════════════════════════════════
    // CATEGORY 2: CINEMATIC & LUXURY (8)
    // ═════════════════════════════════════════════════════════════════════════
    } else if (fxName === "pro_cinema1") {
        // 9. Atmospheric Blur
        var tLayer = createCleanText(words.join(" "), Math.round(compW * 0.055), [0.95, 0.95, 1.0], "Arial-BoldMT", 250);

        try {
            var blur = tLayer.property("Effects").addProperty("ADBE Fast Blur");
            blur.property("Blurriness").setValueAtTime(0, 50);
            blur.property("Blurriness").setValueAtTime(1.2, 0);
            try { blur.property("Repeat Edge Pixels").setValue(0); } catch(err) {
                try { blur.property(3).setValue(0); } catch(err2) {}
            }
        } catch(e) {}
        tLayer.property("Opacity").setValueAtTime(0, 0);
        tLayer.property("Opacity").setValueAtTime(1.0, 100);

    } else if (fxName === "pro_cinema2") {
        // 10. Deep Space Drift
        var tLayer = createCleanText(words.join("  ").toUpperCase(), Math.round(compW * 0.04), [1, 1, 1], "Arial-BoldMT", 400);
        var pProp = tLayer.property("Position");
        pProp.setValueAtTime(0, [compW / 2, (compH / 2) + 20]);
        pProp.setValueAtTime(3.5, [compW / 2, compH / 2]);
        tLayer.property("Opacity").setValueAtTime(0, 0);
        tLayer.property("Opacity").setValueAtTime(1.2, 100);

    } else if (fxName === "pro_cinema3") {
        // 11. Luxury Gold Shimmer
        var tLayer = createCleanText(words.join("  ").toUpperCase(), Math.round(compW * 0.055), [1.0, 0.86, 0.45], "Arial-BoldMT", 300);

        try {
            var glow = tLayer.property("Effects").addProperty("ADBE Glo2");
            glow.property("Glow Threshold").setValue(60);
            glow.property("Glow Radius").setValue(40);
            glow.property("Glow Intensity").setValue(1.5);
            glow.property("Composite Original").setValue(2);
        } catch(e) {}

        tLayer.property("Opacity").setValueAtTime(0, 0);
        tLayer.property("Opacity").setValueAtTime(0.8, 100);
        tLayer.property("Scale").setValueAtTime(0, [96, 96]);
        tLayer.property("Scale").setValueAtTime(3.0, [104, 104]);

    } else if (fxName === "pro_cinema4") {
        // 12. Sand Dust Disperse
        var tLayer = createCleanText(words.join(" "), Math.round(compW * 0.055), [0.9, 0.88, 0.82], "Arial-BoldMT", 200);
        tLayer.property("Opacity").setValueAtTime(0, 0);
        tLayer.property("Opacity").setValueAtTime(1.0, 100);
        tLayer.property("Opacity").setValueAtTime(2.5, 100);
        tLayer.property("Opacity").setValueAtTime(3.8, 0);

        try {
            var turb = tLayer.property("Effects").addProperty("ADBE Turbulent Displace");
            turb.property("Amount").setValueAtTime(2.2, 0);
            turb.property("Amount").setValueAtTime(3.8, 120);
            turb.property("Size").setValue(12);
        } catch(e) {}

    } else if (fxName === "pro_cinema5") {
        // 13. 3D Blockbuster Push
        var tLayer = createCleanText(words.join("  ").toUpperCase(), Math.round(compW * 0.05), [1, 1, 1], "Arial-BoldMT", 350);
        tLayer.threeDLayer = true;
        newComp.motionBlur = true;
        tLayer.motionBlur = true;

        var pos = tLayer.property("Position");
        pos.setValueAtTime(0, [compW / 2, compH / 2, -600]);
        pos.setValueAtTime(3.5, [compW / 2, compH / 2, 0]);

        tLayer.property("Opacity").setValueAtTime(0, 0);
        tLayer.property("Opacity").setValueAtTime(0.6, 100);

    } else if (fxName === "pro_cinema6") {
        // 14. Film Burn 16mm
        var tLayer = createCleanText(words.join(" "), Math.round(compW * 0.06), [1.0, 0.96, 0.88], "Arial-BoldMT", 50);
        tLayer.property("Position").expression = "w = wiggle(18, 3) - value; value + [w[0], w[1]];";
        tLayer.property("Opacity").expression = "90 + random(-15, 10);";

    } else if (fxName === "pro_cinema7") {
        // 15. Cinematic Scope Wipe
        var tLayer = createCleanText(words.join(" "), Math.round(compW * 0.055), [1, 1, 1], "Arial-BoldMT", 100);
        var anim = tLayer.property("Text").property("Animators").addProperty("ADBE Text Animator");
        anim.property("ADBE Text Animator Properties").addProperty("ADBE Text Scale 3D").setValue([100, 0, 100]);
        var sel = anim.property("ADBE Text Selectors").addProperty("ADBE Text Selector");
        sel.property("Start").setValueAtTime(0, 0);
        sel.property("Start").setValueAtTime(1.2, 100);

    } else if (fxName === "pro_cinema8") {
        // 16. Luma Cutout
        var tLayer = createCleanText(words.join(" "), Math.round(compW * 0.08), [1, 1, 1], "Impact", 20);
        tLayer.blendingMode = BlendingMode.DIFFERENCE;
        tLayer.property("Scale").setValueAtTime(0, [80, 80]);
        tLayer.property("Scale").setValueAtTime(0.4, [100, 100]);
        tLayer.property("Scale").expression = springScaleExpr;

    // ═════════════════════════════════════════════════════════════════════════
    // CATEGORY 3: MODERN KINETIC (8)
    // ═════════════════════════════════════════════════════════════════════════
    } else if (fxName === "pro_kinetic1") {
        // 17. 3D Kinetic Flip
        var tLayer = createCleanText(words.join(" "), Math.round(compW * 0.08), [1, 1, 1], "Impact", 20);
        tLayer.threeDLayer = true;
        newComp.motionBlur = true;
        tLayer.motionBlur = true;

        var xRot = tLayer.property("X Rotation");
        xRot.setValueAtTime(0, -90);
        xRot.setValueAtTime(0.35, 0);
        xRot.expression = springRotExpr;

        var pos = tLayer.property("Position");
        pos.setValueAtTime(0, [compW / 2, compH / 2, -350]);
        pos.setValueAtTime(0.35, [compW / 2, compH / 2, 0]);

        tLayer.property("Opacity").setValueAtTime(0, 0);
        tLayer.property("Opacity").setValueAtTime(0.12, 100);

    } else if (fxName === "pro_kinetic2") {
        // 18. Slot Machine Odo
        var tLayer = createCleanText(words.join(" "), Math.round(compW * 0.08), [1, 1, 1], "Impact", 20);
        var anim = tLayer.property("Text").property("Animators").addProperty("ADBE Text Animator");
        anim.property("ADBE Text Animator Properties").addProperty("ADBE Text Position 3D").setValue([0, 150, 0]);
        var sel = anim.property("ADBE Text Selectors").addProperty("ADBE Text Selector");
        sel.property("Start").setValueAtTime(0, 0);
        sel.property("Start").setValueAtTime(0.8, 100);

    } else if (fxName === "pro_kinetic3") {
        // 19. Liquid Color Wave
        var tLayer = createCleanText(words.join(" "), Math.round(compW * 0.075), [1, 1, 1], "Impact", 15);
        var anim = tLayer.property("Text").property("Animators").addProperty("ADBE Text Animator");
        var fillProp = anim.property("ADBE Text Animator Properties").addProperty("ADBE Text Fill Color");
        fillProp.setValue([0.65, 0.3, 1.0]);
        fillProp.expression = "c1 = [0.65, 0.3, 1.0]; c2 = [0.0, 0.9, 1.0]; c3 = [1.0, 0.3, 0.2];\n" +
            "t = (time * 1.5) % 3;\n" +
            "if(t < 1) linear(t, 0, 1, c1, c2);\n" +
            "else if(t < 2) linear(t, 1, 2, c2, c3);\n" +
            "else linear(t, 2, 3, c3, c1);";

    } else if (fxName === "pro_kinetic4") {
        // 20. Rubber Band Elastic
        var tLayer = createCleanText(words.join(" "), Math.round(compW * 0.08), [1, 1, 1], "Impact", 20);
        var sProp = tLayer.property("Scale");
        sProp.setValueAtTime(0, [0, 0]);
        sProp.setValueAtTime(0.18, [150, 60]);
        sProp.setValueAtTime(0.35, [75, 125]);
        sProp.setValueAtTime(0.5, [100, 100]);
        sProp.expression = springScaleExpr;

    } else if (fxName === "pro_kinetic5") {
        // 21. Gravity Drop Slam
        var tLayer = createCleanText(words.join(" "), Math.round(compW * 0.085), [1, 1, 1], "Impact", 15);
        var pProp = tLayer.property("Position");
        pProp.setValueAtTime(0, [compW / 2, -150]);
        pProp.setValueAtTime(0.25, [compW / 2, compH / 2]);
        pProp.expression = 
            "n = 0; if (numKeys > 0){ n = nearestKey(time).index; if (key(n).time > time) n--; }\n" +
            "if (n > 0){\n" +
            "  t = time - key(n).time;\n" +
            "  if (t >= 0 && t < 1.2){\n" +
            "    v = velocityAtTime(key(n).time - thisComp.frameDuration/10);\n" +
            "    amp = 0.08; freq = 5.0; decay = 8.0;\n" +
            "    value + [0, -v[1] * amp * Math.abs(Math.sin(freq * t * 2 * Math.PI)) / Math.exp(decay * t)];\n" +
            "  } else { value; }\n" +
            "} else { value; }";

    } else if (fxName === "pro_kinetic6") {
        // 22. Infinite Marquee
        var fullStr = (words.join("   •   ") + "   •   ").repeat(4);
        var tLayer = createCleanText(fullStr, Math.round(compW * 0.06), [1, 1, 1], "Impact", 20);
        tLayer.property("Position").expression = "value - [(time * 250) % 800, 0];";

    } else if (fxName === "pro_kinetic7") {
        // 23. Stagger Wave Ripple
        var tLayer = createCleanText(words.join(" "), Math.round(compW * 0.075), [1, 1, 1], "Impact", 15);
        var anim = tLayer.property("Text").property("Animators").addProperty("ADBE Text Animator");
        anim.property("ADBE Text Animator Properties").addProperty("ADBE Text Position 3D").setValue([0, -40, 0]);
        var sel = anim.property("ADBE Text Selectors").addProperty("ADBE Text Selector");
        sel.property("Start").setValueAtTime(0, 0);
        sel.property("Start").setValueAtTime(1.5, 100);

    } else if (fxName === "pro_kinetic8") {
        // 24. Split Slide Stagger
        var textStr = words.join(" ");
        var fSize = Math.round(compW * 0.08);
        var t1 = createCleanText(textStr, fSize, [1, 1, 1], "Impact", 20);
        t1.name = "Text Top Half";
        var t2 = createCleanText(textStr, fSize, [0.0, 0.85, 1.0], "Impact", 20);
        t2.name = "Text Bottom Half";

        t1.property("Position").setValueAtTime(0, [compW / 2 - 120, compH / 2]);
        t1.property("Position").setValueAtTime(0.3, [compW / 2, compH / 2]);
        t1.property("Position").expression = springScaleExpr;

        t2.property("Position").setValueAtTime(0, [compW / 2 + 120, compH / 2]);
        t2.property("Position").setValueAtTime(0.3, [compW / 2, compH / 2]);
        t2.property("Position").expression = springScaleExpr;

    // ═════════════════════════════════════════════════════════════════════════
    // CATEGORY 4: GLITCH, CYBER & GAMING (8)
    // ═════════════════════════════════════════════════════════════════════════
    } else if (fxName === "pro_glitch1") {
        // 25. RGB Chromatic Aberration
        var textStr = words.join(" ");
        var fSize = Math.round(compW * 0.07);

        var rLayer = createCleanText(textStr, fSize, [1, 0, 0], "Impact", 15);
        rLayer.blendingMode = BlendingMode.ADD;
        rLayer.property("Position").expression = 
            "w = wiggle(16, 22) - value;\n" +
            "glitch = (time % 1.2 < 0.25) ? 1.0 : 0.15;\n" +
            "value + [w[0] * glitch + 8, (w[1] * 0.15) * glitch];";

        var cLayer = createCleanText(textStr, fSize, [0, 1, 1], "Impact", 15);
        cLayer.blendingMode = BlendingMode.ADD;
        cLayer.property("Position").expression = 
            "w = wiggle(16, 22) - value;\n" +
            "glitch = (time % 1.2 < 0.25) ? 1.0 : 0.15;\n" +
            "value - [w[0] * glitch + 8, (w[1] * 0.15) * glitch];";

        var wLayer = createCleanText(textStr, fSize, [1, 1, 1], "Impact", 15);
        wLayer.blendingMode = BlendingMode.ADD;
        wLayer.property("Opacity").setValue(85);

    } else if (fxName === "pro_glitch2") {
        // 26. Cyber Decoder Typewriter
        var textStr = words.join(" ");
        var tLayer = createCleanText(textStr, Math.round(compW * 0.06), [0.2, 1.0, 0.4], "Courier New", 100);

        var fullStrEsc = textStr.replace(/"/g, '\\"');
        tLayer.property("Source Text").expression = 
            'full = "' + fullStrEsc + '";\n' +
            'len = Math.round(linear(time, 0, 1.2, 0, full.length));\n' +
            'cursor = (Math.floor(time * 6) % 2 === 0) ? "_" : " ";\n' +
            'full.substr(0, len) + cursor;';

    } else if (fxName === "pro_glitch3") {
        // 27. CRT & VHS Distortion
        var tLayer = createCleanText(words.join(" "), Math.round(compW * 0.07), [0.9, 1.0, 0.9], "Courier New", 40);
        tLayer.property("Position").expression = "w = wiggle(10, 8) - value; value + [(time % 0.8 < 0.12 ? w[0]*3 : 0), 0];";
        tLayer.property("Scale").setValueAtTime(0, [100, 0]);
        tLayer.property("Scale").setValueAtTime(0.12, [100, 100]);

    } else if (fxName === "pro_glitch4") {
        // 28. Hologram HUD Brackets
        var textStr = "[  " + words.join(" ").toUpperCase() + "  ]";
        var tLayer = createCleanText(textStr, Math.round(compW * 0.06), [0.0, 0.9, 1.0], "Impact", 120);
        tLayer.property("Opacity").expression = "70 + Math.sin(time * 25) * 20 + random(-10, 10);";
        tLayer.property("Scale").setValueAtTime(0, [130, 130]);
        tLayer.property("Scale").setValueAtTime(0.2, [100, 100]);
        tLayer.property("Scale").expression = springScaleExpr;

    } else if (fxName === "pro_glitch5") {
        // 29. Matrix Digital Rain
        var textStr = words.join(" ");
        var tLayer = createCleanText(textStr, Math.round(compW * 0.065), [0.1, 1.0, 0.3], "Courier New", 60);
        var anim = tLayer.property("Text").property("Animators").addProperty("ADBE Text Animator");
        anim.property("ADBE Text Animator Properties").addProperty("ADBE Text Character Range").setValue(26);
        var sel = anim.property("ADBE Text Selectors").addProperty("ADBE Text Selector");
        sel.property("Start").setValueAtTime(0, 0);
        sel.property("Start").setValueAtTime(1.2, 100);

    } else if (fxName === "pro_glitch6") {
        // 30. 8-Bit Pixel Mosaic
        var tLayer = createCleanText(words.join(" "), Math.round(compW * 0.075), [1, 1, 1], "Impact", 20);
        try {
            var mos = tLayer.property("Effects").addProperty("ADBE Mosaic");
            mos.property("Horizontal Blocks").setValueAtTime(0, 8);
            mos.property("Horizontal Blocks").setValueAtTime(0.6, 100);
            mos.property("Vertical Blocks").setValueAtTime(0, 4);
            mos.property("Vertical Blocks").setValueAtTime(0.6, 60);
        } catch(e) {}

    } else if (fxName === "pro_glitch7") {
        // 31. Bad TV Sliced Tear
        var tLayer = createCleanText(words.join(" "), Math.round(compW * 0.075), [1, 1, 1], "Impact", 20);
        tLayer.property("Position").expression = 
            "tear = (time % 0.6 < 0.08) ? random(-40, 40) : 0;\n" +
            "value + [tear, 0];";

    } else if (fxName === "pro_glitch8") {
        // 32. Cyber Wireframe
        var tLayer = createCleanText(words.join(" "), Math.round(compW * 0.075), [0, 0, 0], "Impact", 25);
        var tDoc = tLayer.property("Source Text").value;
        tDoc.applyStroke = true;
        tDoc.strokeColor = [0.0, 0.95, 1.0];
        tDoc.strokeWidth = 3;
        tDoc.strokeOverFill = false;
        tLayer.property("Source Text").setValue(tDoc);

        try {
            var g = tLayer.property("Effects").addProperty("ADBE Glo2");
            g.property("Glow Radius").setValue(20);
            g.property("Glow Intensity").setValue(2.0);
        } catch(e) {}

    // ═════════════════════════════════════════════════════════════════════════
    // CATEGORY 5: MINIMAL & CORPORATE (6)
    // ═════════════════════════════════════════════════════════════════════════
    } else if (fxName === "pro_minimal1") {
        // 33. Smooth Line Wipe
        var textStr = words.join(" ");
        var fSize = Math.round(compW * 0.06);
        var tLayer = createCleanText(textStr, fSize, [1, 1, 1], "Arial-BoldMT", 10);

        var pProp = tLayer.property("Position");
        pProp.setValueAtTime(0, [compW / 2, compH / 2 + fSize]);
        pProp.setValueAtTime(0.4, [compW / 2, compH / 2]);
        pProp.expression = springScaleExpr;
        tLayer.property("Opacity").setValueAtTime(0, 0);
        tLayer.property("Opacity").setValueAtTime(0.25, 100);

    } else if (fxName === "pro_minimal2") {
        // 34. Draw Underline (EXACT SOURCERECT WIDTH)
        var textStr = words.join(" ");
        var fSize = Math.round(compW * 0.06);
        var tLayer = createCleanText(textStr, fSize, [1, 1, 1], "Arial-BoldMT", 10);

        var r = tLayer.sourceRectAtTime(0, false);
        var lineW = r.width + 20;

        var line = newComp.layers.addShape();
        line.name = "Accent Underline";
        var group = line.property("Contents").addProperty("ADBE Vector Group");
        var rect = group.property("Contents").addProperty("ADBE Vector Shape - Rect");
        rect.property("Size").setValue([lineW, 4]);
        var fill = group.property("Contents").addProperty("ADBE Vector Graphic - Fill");
        fill.property("Color").setValue([0.65, 0.35, 1.0]);

        line.property("Anchor Point").setValue([-lineW / 2, 0]);
        line.property("Position").setValue([(compW / 2) - (lineW / 2), (compH / 2) + (r.height / 2) + 16]);

        var sProp = line.property("Scale");
        sProp.setValueAtTime(0.15, [0, 100]);
        sProp.setValueAtTime(0.55, [100, 100]);
        sProp.expression = springScaleExpr;

    } else if (fxName === "pro_minimal3") {
        // 35. Animated Number Counter
        var tLayer = createCleanText("0", Math.round(compW * 0.09), [1, 1, 1], "Arial-BoldMT", 10);
        tLayer.property("Source Text").expression = 
            'num = Math.round(linear(time, 0, 1.5, 0, 100000));\n' +
            'num.toString().replace(/\\B(?=(\\d{3})+(?!\\d))/g, ",");';

    } else if (fxName === "pro_minimal4") {
        // 36. Modern Code Terminal
        var textStr = "> " + words.join(" ");
        var tLayer = createCleanText(textStr, Math.round(compW * 0.055), [0.85, 0.9, 1.0], "Courier New", 80);

        var fullEsc = textStr.replace(/"/g, '\\"');
        tLayer.property("Source Text").expression = 
            'full = "' + fullEsc + '";\n' +
            'len = Math.round(linear(time, 0, 1.0, 2, full.length));\n' +
            'cursor = (Math.floor(time * 5) % 2 === 0) ? "█" : " ";\n' +
            'full.substr(0, len) + cursor;';

    } else if (fxName === "pro_minimal5") {
        // 37. Podcast Float
        var tLayer = createCleanText(words.join(" "), Math.round(compW * 0.055), [0.95, 0.95, 0.98], "Arial-BoldMT", 15);
        tLayer.property("Position").expression = 
            "drift = Math.sin(time * 1.5) * 8;\n" +
            "value + [0, drift];";
        tLayer.property("Opacity").setValueAtTime(0, 0);
        tLayer.property("Opacity").setValueAtTime(0.8, 100);

    } else if (fxName === "pro_minimal6") {
        // 38. Stagger Fade Up
        var tLayer = createCleanText(words.join(" "), Math.round(compW * 0.06), [1, 1, 1], "Arial-BoldMT", 15);
        var anim = tLayer.property("Text").property("Animators").addProperty("ADBE Text Animator");
        anim.property("ADBE Text Animator Properties").addProperty("ADBE Text Position 3D").setValue([0, 50, 0]);
        anim.property("ADBE Text Animator Properties").addProperty("ADBE Text Opacity").setValue(0);
        var sel = anim.property("ADBE Text Selectors").addProperty("ADBE Text Selector");
        sel.property("Start").setValueAtTime(0, 0);
        sel.property("Start").setValueAtTime(1.0, 100);
    }

    // Insert into activeComp
    var insertedLayer = activeComp.layers.add(newComp);
    insertedLayer.startTime = activeComp.time;

    app.endUndoGroup();
}
