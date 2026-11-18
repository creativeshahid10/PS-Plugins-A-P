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
 * PixelSquad Motion Studio - After Effects Clean Engine
 * Author: PixelSquad Development Team
 */

var PixelSquadAE = {
    getActiveComp: function() {
        if (app.project && app.project.activeItem && app.project.activeItem instanceof CompItem) {
            return app.project.activeItem;
        }
        return null;
    },

    // Apply Easing to Selected Keyframes
    applyEasingCurve: function(curveType) {
        var comp = this.getActiveComp();
        if (!comp) return "ERROR: No active composition found.";
        
        var selectedLayers = comp.selectedLayers;
        if (selectedLayers.length === 0) return "WARNING: Please select at least one layer.";
        
        app.beginUndoGroup("PixelSquad Apply " + curveType);
        try {
            var speed = 75;
            var infl = 75;
            if (curveType === "Snap") { infl = 95; }
            else if (curveType === "Smooth") { infl = 65; }
            else if (curveType === "Bounce") { infl = 85; }
            
            var easeIn = new KeyframeEase(0, infl);
            var easeOut = new KeyframeEase(0, infl);
            
            var appliedCount = 0;
            for (var l = 0; l < selectedLayers.length; l++) {
                var layer = selectedLayers[l];
                var props = layer.selectedProperties;
                for (var p = 0; p < props.length; p++) {
                    var prop = props[p];
                    if (prop.numKeys > 0) {
                        for (var k = 1; k <= prop.numKeys; k++) {
                            if (prop.keySelected(k)) {
                                if (prop.propertyValueType === PropertyValueType.TwoD_SPATIAL || prop.propertyValueType === PropertyValueType.ThreeD_SPATIAL) {
                                    // Spatial eases
                                    prop.setTemporalEaseAtKey(k, [easeIn], [easeOut]);
                                } else {
                                    prop.setTemporalEaseAtKey(k, [easeIn], [easeOut]);
                                }
                                appliedCount++;
                            }
                        }
                    }
                }
            }
            app.endUndoGroup();
            return "SUCCESS: Eased " + appliedCount + " keyframes with " + curveType + " curve.";
        } catch(e) {
            app.endUndoGroup();
            return "ERROR: " + e.toString();
        }
    },

    // Align Anchor Point (9-point matrix)
    alignAnchorPoint: function(pos) {
        var comp = this.getActiveComp();
        if (!comp) return "ERROR: No active composition.";
        
        var layers = comp.selectedLayers;
        if (layers.length === 0) return "WARNING: Select at least one layer.";
        
        app.beginUndoGroup("PixelSquad Align Anchor " + pos);
        try {
            for (var i = 0; i < layers.length; i++) {
                var layer = layers[i];
                var rect = layer.sourceRectAtTime(comp.time, false);
                var x = rect.left;
                var y = rect.top;
                var w = rect.width;
                var h = rect.height;
                
                var newX = x + w / 2;
                var newY = y + h / 2;
                
                if (pos === "TL") { newX = x; newY = y; }
                else if (pos === "TC") { newX = x + w/2; newY = y; }
                else if (pos === "TR") { newX = x + w; newY = y; }
                else if (pos === "ML") { newX = x; newY = y + h/2; }
                else if (pos === "MC") { newX = x + w/2; newY = y + h/2; }
                else if (pos === "MR") { newX = x + w; newY = y + h/2; }
                else if (pos === "BL") { newX = x; newY = y + h; }
                else if (pos === "BC") { newX = x + w/2; newY = y + h; }
                else if (pos === "BR") { newX = x + w; newY = y + h; }
                
                var apProp = layer.property("ADBE Transform Group").property("ADBE Anchor Point");
                var posProp = layer.property("ADBE Transform Group").property("ADBE Position");
                
                var oldAP = apProp.value;
                var diffX = newX - oldAP[0];
                var diffY = newY - oldAP[1];
                
                apProp.setValue([newX, newY, oldAP[2] || 0]);
                var oldPos = posProp.value;
                posProp.setValue([oldPos[0] + diffX, oldPos[1] + diffY, oldPos[2] || 0]);
            }
            app.endUndoGroup();
            return "SUCCESS: Anchor point aligned to " + pos + " on " + layers.length + " layer(s).";
        } catch(e) {
            app.endUndoGroup();
            return "ERROR: " + e.toString();
        }
    },

    // Create Connected Null Controller
    createNullController: function() {
        var comp = this.getActiveComp();
        if (!comp) return "ERROR: No active composition.";
        var layers = comp.selectedLayers;
        if (layers.length === 0) return "WARNING: Select layers to connect to Null.";
        
        app.beginUndoGroup("PixelSquad Create Controller Null");
        try {
            var nullLayer = comp.layers.addNull();
            nullLayer.name = "PixelSquad_Controller";
            for (var i = 0; i < layers.length; i++) {
                layers[i].parent = nullLayer;
            }
            app.endUndoGroup();
            return "SUCCESS: Created controller Null parented to " + layers.length + " layer(s).";
        } catch(e) {
            app.endUndoGroup();
            return "ERROR: " + e.toString();
        }
    },

    // Stagger Selected Layers by Frames
    staggerLayers: function(frameOffset) {
        var comp = this.getActiveComp();
        if (!comp) return "ERROR: No active composition.";
        var layers = comp.selectedLayers;
        if (layers.length <= 1) return "WARNING: Select at least 2 layers to stagger.";
        
        app.beginUndoGroup("PixelSquad Stagger Layers");
        try {
            var fps = comp.frameRate;
            var offsetSec = frameOffset / fps;
            var startTime = comp.time;
            for (var i = 0; i < layers.length; i++) {
                layers[i].startTime = startTime + (i * offsetSec);
            }
            app.endUndoGroup();
            return "SUCCESS: Staggered " + layers.length + " layers by " + frameOffset + " frame(s).";
        } catch(e) {
            app.endUndoGroup();
            return "ERROR: " + e.toString();
        }
    }
};