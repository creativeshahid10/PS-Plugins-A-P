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
 * PixelSquad PSCaptions - PremiereCaptionEngine.jsx
 * ExtendScript Backend for Adobe Premiere Pro CEP Panel
 * Compatible with Premiere Pro CC 2020 (v14.0) through 2026+ (v25.0+)
 *
 * Strict ES3 Compliance for Adobe ExtendScript Engine
 */

(function () {
    // Basic JSON Polyfill for ES3 ExtendScript engines if needed
    if (typeof JSON !== "object") {
        JSON = {};
    }
    if (typeof JSON.stringify !== "function") {
        JSON.stringify = function (obj) {
            var t = typeof obj;
            if (t !== "object" || obj === null) {
                if (t === "string") return '"' + obj.replace(/\\/g, '\\\\').replace(/"/g, '\\"') + '"';
                return String(obj);
            } else {
                var json = [], isArr = (obj && obj.constructor === Array);
                for (var n in obj) {
                    if (obj.hasOwnProperty(n)) {
                        var v = obj[n];
                        var vt = typeof v;
                        if (vt === "string") v = '"' + v.replace(/\\/g, '\\\\').replace(/"/g, '\\"') + '"';
                        else if (vt === "object" && v !== null) v = JSON.stringify(v);
                        json.push((isArr ? "" : '"' + n + '":') + String(v));
                    }
                }
                return (isArr ? "[" : "{") + String(json) + (isArr ? "]" : "}");
            }
        };
    }
    if (typeof JSON.parse !== "function") {
        JSON.parse = function (str) {
            return eval("(" + str + ")");
        };
    }
})();

var PSCaptionsEngine = {
    TICKS_PER_SECOND: 254016000000,

    ping: function () {
        var appVer = "Unknown";
        try {
            appVer = app.version;
        } catch (e) { }
        return JSON.stringify({
            success: true,
            app: "Premiere Pro",
            version: appVer,
            timestamp: new Date().getTime()
        });
    },

    getActiveSequenceInfo: function () {
        if (!app.project) {
            return JSON.stringify({
                success: false,
                message: "No project is open in Premiere Pro."
            });
        }
        var seq = app.project.activeSequence;
        if (!seq) {
            return JSON.stringify({
                success: false,
                message: "No active sequence found. Please open a sequence in the Timeline panel."
            });
        }

        var playerPos = seq.getPlayerPosition();
        var tracks = [];
        var numVTracks = seq.videoTracks ? seq.videoTracks.numTracks : 0;
        for (var i = 0; i < numVTracks; i++) {
            tracks.push({
                index: i,
                name: seq.videoTracks[i].name || ("V" + (i + 1))
            });
        }

        return JSON.stringify({
            success: true,
            name: seq.name,
            id: seq.sequenceID,
            width: seq.frameSizeHorizontal,
            height: seq.frameSizeVertical,
            timeTicks: playerPos ? playerPos.ticks : "0",
            timeSeconds: playerPos ? playerPos.seconds : 0,
            videoTracksCount: numVTracks,
            tracks: tracks
        });
    },

    // Convert seconds to ticks string
    secondsToTicks: function (seconds) {
        var t = Math.round(seconds * this.TICKS_PER_SECOND);
        return t.toString();
    },

    // Convert ticks string to seconds
    ticksToSeconds: function (ticksStr) {
        var t = parseFloat(ticksStr);
        if (isNaN(t)) return 0;
        return t / this.TICKS_PER_SECOND;
    },

    // Find or target an appropriate video track for captions
    getTargetVideoTrackIndex: function (preferredIndex) {
        var seq = app.project.activeSequence;
        if (!seq || !seq.videoTracks) return 0;
        var numTracks = seq.videoTracks.numTracks;

        if (typeof preferredIndex === "number" && preferredIndex >= 0 && preferredIndex < numTracks) {
            return preferredIndex;
        }

        // Default to V2 (index 1) if available, so V1 background footage is not overlaid directly
        if (numTracks > 1) {
            return 1;
        }
        return 0;
    },

    // Apply single caption MOGRT at current playhead or specified time
    applyCaptionMOGRT: function (mogrtFullPath, captionText, optionsJsonStr) {
        try {
            if (!app.project) {
                return JSON.stringify({ success: false, message: "No project open in Premiere Pro." });
            }
            var seq = app.project.activeSequence;
            if (!seq) {
                return JSON.stringify({ success: false, message: "No active sequence found. Open a sequence in the Timeline." });
            }

            var options = {};
            if (optionsJsonStr) {
                try {
                    options = JSON.parse(optionsJsonStr);
                } catch (e) { }
            }

            // Verify file exists
            var f = new File(mogrtFullPath);
            if (!f.exists) {
                return JSON.stringify({
                    success: false,
                    message: "MOGRT file not found on disk: " + mogrtFullPath
                });
            }

            // Determine target playhead time
            var targetTicks = "0";
            if (options.targetTicks) {
                targetTicks = String(options.targetTicks);
            } else if (options.targetSeconds !== undefined) {
                targetTicks = this.secondsToTicks(options.targetSeconds);
            } else {
                var currPos = seq.getPlayerPosition();
                targetTicks = currPos ? currPos.ticks : "0";
            }

            // Determine video track
            var targetTrackIndex = this.getTargetVideoTrackIndex(options.trackIndex);

            // Import MOGRT
            // app.project.activeSequence.importMOGRT(path, timeTicks, videoTrackIndex, audioTrackIndex)
            var importedItem = null;
            try {
                if (typeof seq.importMGT === "function") {
                    importedItem = seq.importMGT(f.fsName, targetTicks, targetTrackIndex, 0);
                } else if (typeof seq.importMOGRT === "function") {
                    importedItem = seq.importMOGRT(f.fsName, targetTicks, targetTrackIndex, 0);
                } else {
                    throw new Error("Active sequence does not support importMGT (function missing).");
                }
            } catch (importErr) {
                return JSON.stringify({
                    success: false,
                    message: "Failed to import MOGRT into sequence: " + importErr.toString()
                });
            }

            // If text was provided, inject into Essential Properties
            var propertyUpdated = false;
            if (captionText && importedItem && importedItem.components) {
                try {
                    for (var c = 0; c < importedItem.components.numItems; c++) {
                        var comp = importedItem.components[c];
                        if (comp && comp.properties) {
                            for (var p = 0; p < comp.properties.numItems; p++) {
                                var prop = comp.properties[p];
                                var name = prop.displayName || "";
                                if (name === "Source Text" || name === "Text" || name === "TextLayer" || name.indexOf("Text") !== -1) {
                                    prop.setValue(captionText, true);
                                    propertyUpdated = true;
                                }
                            }
                        }
                    }
                } catch (propErr) { }
            }

            // Adjust duration if specified in options
            if (options.durationSeconds && importedItem) {
                try {
                    var startSec = this.ticksToSeconds(targetTicks);
                    var newEndTicks = this.secondsToTicks(startSec + options.durationSeconds);
                    importedItem.end = newEndTicks;
                } catch (durErr) { }
            }

            return JSON.stringify({
                success: true,
                message: "Caption applied successfully at " + (this.ticksToSeconds(targetTicks).toFixed(2)) + "s on track V" + (targetTrackIndex + 1),
                track: targetTrackIndex,
                timeTicks: targetTicks,
                textUpdated: propertyUpdated
            });
        } catch (globalErr) {
            return JSON.stringify({
                success: false,
                message: "Engine Error: " + globalErr.toString()
            });
        }
    },

    // Apply bulk captions parsed from SRT or Multi-line transcript
    applyBulkCaptions: function (captionsArrayJsonStr, mogrtFullPath, optionsJsonStr) {
        try {
            if (!app.project || !app.project.activeSequence) {
                return JSON.stringify({ success: false, message: "No active sequence found." });
            }
            var seq = app.project.activeSequence;

            var captions = [];
            try {
                captions = JSON.parse(captionsArrayJsonStr);
            } catch (e) {
                return JSON.stringify({ success: false, message: "Invalid captions JSON array: " + e.toString() });
            }

            if (!captions || captions.length === 0) {
                return JSON.stringify({ success: false, message: "No caption cues provided." });
            }

            var options = {};
            if (optionsJsonStr) {
                try { options = JSON.parse(optionsJsonStr); } catch (e) { }
            }

            var f = new File(mogrtFullPath);
            if (!f.exists) {
                return JSON.stringify({ success: false, message: "MOGRT file not found: " + mogrtFullPath });
            }

            var targetTrackIndex = this.getTargetVideoTrackIndex(options.trackIndex);
            var appliedCount = 0;
            var errors = [];

            for (var i = 0; i < captions.length; i++) {
                var cue = captions[i];
                var startSec = parseFloat(cue.startSeconds || 0);
                var endSec = parseFloat(cue.endSeconds || (startSec + 2.0));
                var duration = Math.max(0.5, endSec - startSec);
                var text = cue.text || "";

                var startTicks = this.secondsToTicks(startSec);

                try {
                    var item = null;
                    if (typeof seq.importMGT === "function") {
                        item = seq.importMGT(f.fsName, startTicks, targetTrackIndex, 0);
                    } else if (typeof seq.importMOGRT === "function") {
                        item = seq.importMOGRT(f.fsName, startTicks, targetTrackIndex, 0);
                    }
                    if (item) {
                        // Update text property
                        if (text && item.components) {
                            for (var c = 0; c < item.components.numItems; c++) {
                                var comp = item.components[c];
                                if (comp && comp.properties) {
                                    for (var p = 0; p < comp.properties.numItems; p++) {
                                        var prop = comp.properties[p];
                                        var name = prop.displayName || "";
                                        if (name === "Source Text" || name === "Text" || name === "TextLayer" || name.indexOf("Text") !== -1) {
                                            prop.setValue(text, true);
                                        }
                                    }
                                }
                            }
                        }

                        // Adjust duration
                        try {
                            item.end = this.secondsToTicks(endSec);
                        } catch (e) { }

                        appliedCount++;
                    }
                } catch (cueErr) {
                    errors.push("Cue #" + (i + 1) + ": " + cueErr.toString());
                }
            }

            return JSON.stringify({
                success: appliedCount > 0,
                appliedCount: appliedCount,
                totalRequested: captions.length,
                trackIndex: targetTrackIndex,
                errors: errors,
                message: "Applied " + appliedCount + " of " + captions.length + " caption cues to Track V" + (targetTrackIndex + 1)
            });
        } catch (bulkErr) {
            return JSON.stringify({
                success: false,
                message: "Bulk Import Error: " + bulkErr.toString()
            });
        }
    }
};
