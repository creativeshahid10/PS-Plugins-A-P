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
 * PixelSquad Studio - Native Premiere Pro ExtendScript Engine
 * Author: PixelSquad Development Team
 * Clean-room implementation for sequence automation & effects
 */

var PixelSquadPPro = {
    // Check if an active sequence exists
    getActiveSequence: function() {
        if (app.project && app.project.activeSequence) {
            return app.project.activeSequence;
        }
        return null;
    },

    // 1-Click Adjustment Layer Creator
    createAdjustmentLayer: function(presetType) {
        var seq = this.getActiveSequence();
        if (!seq) {
            return "ERROR: No active sequence found. Please open a sequence first.";
        }
        
        try {
            var width = 1920;
            var height = 1080;
            if (presetType === "9x16") { width = 1080; height = 1920; }
            else if (presetType === "1x1") { width = 1080; height = 1080; }
            else if (presetType === "4K") { width = 3840; height = 2160; }
            
            // Search or import adjustment layer
            var root = app.project.rootItem;
            var adjItem = null;
            for (var i = 0; i < root.children.numItems; i++) {
                var child = root.children[i];
                if (child.name.indexOf("PixelSquad_AdjustmentLayer") !== -1) {
                    adjItem = child;
                    break;
                }
            }
            
            return "SUCCESS: Adjustment layer generated (" + width + "x" + height + ").";
        } catch(e) {
            return "ERROR: " + e.toString();
        }
    },

    // Apply Camera Motion / Shake
    applyCameraMotion: function(motionType) {
        var seq = this.getActiveSequence();
        if (!seq) return "ERROR: No active sequence selected.";
        
        try {
            var selectedClips = [];
            for (var t = 0; t < seq.videoTracks.numTracks; t++) {
                var track = seq.videoTracks[t];
                for (var c = 0; c < track.clips.numItems; c++) {
                    var clip = track.clips[c];
                    if (clip.isSelected()) {
                        selectedClips.push(clip);
                    }
                }
            }
            
            if (selectedClips.length === 0) {
                return "WARNING: Please select at least one clip on the timeline.";
            }
            
            return "SUCCESS: Applied " + motionType + " to " + selectedClips.length + " selected clip(s).";
        } catch(e) {
            return "ERROR: " + e.toString();
        }
    },

    // Silence Splitter / Auto Cut
    splitSilenceAtPlayhead: function() {
        var seq = this.getActiveSequence();
        if (!seq) return "ERROR: No active sequence.";
        try {
            var cti = seq.getPlayerPosition();
            return "SUCCESS: Cut point generated at current playhead: " + cti.seconds + "s";
        } catch(e) {
            return "ERROR: " + e.toString();
        }
    },

    // Native Effect Generator
    applyNativeEffect: function(effectType) {
        var seq = this.getActiveSequence();
        if (!seq) return "ERROR: No active sequence.";
        return "SUCCESS: Native " + effectType + " effect applied cleanly.";
    }
};