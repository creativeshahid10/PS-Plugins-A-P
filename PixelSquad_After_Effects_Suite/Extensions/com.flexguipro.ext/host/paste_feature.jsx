



$.global.getPasteImagePath_FlexGUI = function() {
    try {
        var proj = app.project;
        var targetFolder = null;
        if (proj && proj.file) {
            var parentFolder = proj.file.parent;
            if (parentFolder) {
                targetFolder = new Folder(parentFolder.fsName + "/Flex Pasted");
            }
        }

        
        if (!targetFolder) {
            var desktop = Folder.desktop;
            if (desktop && desktop.exists) {
                targetFolder = new Folder(desktop.fsName + "/Flex Pasted");
            }
        }

        
        if (!targetFolder) {
            var myDocuments = Folder.myDocuments;
            if (myDocuments && myDocuments.exists) {
                targetFolder = new Folder(myDocuments.fsName + "/Flex Pasted");
            }
        }

        
        if (!targetFolder) {
            var temp = Folder.temp;
            if (temp) {
                targetFolder = new Folder(temp.fsName + "/Flex Pasted");
            }
        }

        if (!targetFolder) {
            return "ERR:Could not resolve a target folder for pasted images.";
        }

        if (!targetFolder.exists) {
            var created = targetFolder.create();
            if (!created) {
                targetFolder = Folder.temp;
            }
        }

        var randomNumber = Math.floor(100 + Math.random() * 9000);
        var targetPath = targetFolder.fsName + "/flex_img_" + randomNumber + ".png";
        return targetPath.replace(new RegExp("\\\\", "g"), "/");
    } catch (e) {
        return "ERR:getPasteImagePath failed: " + e.toString();
    }
}

$.global.getDownloadFolder_FlexGUI = function() {
    var proj = app.project;
    var targetFolder;
    if (proj && proj.file) {
        var parentFolder = proj.file.parent;
        targetFolder = new Folder(parentFolder.fsName + "/Flex Downloads");
    } else {
        targetFolder = new Folder(Folder.desktop.fsName + "/Flex Downloads");
    }
    if (!targetFolder.exists) {
        targetFolder.create();
    }
    return targetFolder.fsName.replace(new RegExp("\\\\", "g"), "/");
}

$.global.selectDownloadFolder_FlexGUI = function() {
    var picked = Folder.selectDialog("Choose Download Folder");
    if (picked) {
        return picked.fsName.replace(new RegExp("\\\\", "g"), "/");
    }
    return "";
}

$.global.pasteImageFromFile_FlexGUI = function(filePath, appName, toShapes) {
    if ($._flex && $._flex.isLocked) return "Extension is locked.";
    if (appName === "AEFT") {
        var item;
        var xfile = File(filePath);
        try {
            if (!xfile.exists) return "ERR: Source image does not exist: " + filePath;
            if (!app.project || !app.project.activeItem || !(app.project.activeItem instanceof CompItem)) {
                return "ERR: Open an active composition before importing an image or icon.";
            }
            app.beginUndoGroup("Paste Image");
            item = app.project.importFile(new ImportOptions(xfile));
            if (item && app.project.activeItem && app.project.activeItem instanceof CompItem) {
                var comp = app.project.activeItem;
                var sel = comp.selectedLayers;
                var newLayer = comp.layers.add(item);
                
                
                if (sel.length > 0) {
                    var minIn = 99999, maxOut = -99999, topIndex = 99999;
                    for (var i = 0; i < sel.length; i++) {
                        if (sel[i].inPoint < minIn) minIn = sel[i].inPoint;
                        if (sel[i].outPoint > maxOut) maxOut = sel[i].outPoint;
                        if (sel[i].index < topIndex) topIndex = sel[i].index;
                    }
                    newLayer.inPoint = minIn;
                    newLayer.outPoint = maxOut;
                    newLayer.moveBefore(comp.layers[topIndex]);
                }
                
                
                if (toShapes === true || toShapes === "true" || toShapes === 1 || toShapes === "1") {
                    for (var j = 1; j <= comp.numLayers; j++) {
                        comp.layer(j).selected = false;
                    }
                    newLayer.selected = true;
                    var cmdId = app.findMenuCommandId("Create Shapes from Vector Layer");
                    if (cmdId) {
                        app.executeCommand(cmdId);
                        try {
                            newLayer.remove();
                        } catch (remErr) {}
                    }
                }
            } else {
                app.endUndoGroup();
                return "ERR: After Effects imported no usable footage item.";
            }
            app.endUndoGroup();
            return "SUCCESS";
        } catch (e) {
            app.endUndoGroup();
            return "ERR: " + e.toString();
        }
    }
    return "Not AEFT";
}

$.global.alignLayers_FlexGUI = function(directionModeStr) {
    if ($._flex && $._flex.isLocked) return "Extension is locked.";
    var c = app.project.activeItem;
    if (!c || !(c instanceof CompItem) || c.selectedLayers.length < 1) return;

    
    function getPos(l) {
        try {
            var tForm = l.property("ADBE Transform Group");
            var posProp = tForm.property("ADBE Position");
            if (posProp.dimensionsSeparated) {
                var x = tForm.property("ADBE Position_0").value;
                var y = tForm.property("ADBE Position_1").value;
                var z = tForm.property("ADBE Position_2") ? tForm.property("ADBE Position_2").value : 0;
                return [x, y, z];
            } else {
                var val = posProp.value;
                return [val[0], val[1], val.length > 2 ? val[2] : 0];
            }
        } catch (e) {
            return [0, 0, 0];
        }
    }

    
    function setPos(l, val) {
        try {
            var tForm = l.property("ADBE Transform Group");
            var posProp = tForm.property("ADBE Position");
            if (posProp.dimensionsSeparated) {
                tForm.property("ADBE Position_0").setValue(val[0]);
                tForm.property("ADBE Position_1").setValue(val[1]);
                if (tForm.property("ADBE Position_2") && val.length > 2) {
                    tForm.property("ADBE Position_2").setValue(val[2]);
                }
            } else {
                posProp.setValue(val);
            }
        } catch (e) { }
    }

    
    function getLayerWorldPos(layer, time) {
        try {
            var tForm = layer.property("ADBE Transform Group");
            if (!tForm) return getPos(layer);
            var anchorProp = tForm.property("ADBE Anchor Point");
            if (!anchorProp) return getPos(layer);
            
            var hasExpr = anchorProp.expressionEnabled;
            var origExpr = anchorProp.expression;
            
            anchorProp.expression = "toComp(anchorPoint)";
            var val = anchorProp.valueAtTime(time, false);
            
            anchorProp.expression = origExpr;
            anchorProp.expressionEnabled = hasExpr;
            
            return [val[0], val[1], val.length > 2 ? val[2] : 0];
        } catch (e) {
            return getPos(layer);
        }
    }

    
    var parts = directionModeStr.split("|");
    var direction = parts[0];
    var alignTo = parts.length > 1 ? parts[1] : "comp";
    if (direction === "hcenter") direction = "center";
    if (direction === "vcenter") direction = "middle";
    if (alignTo === "group" || direction === "distH" || direction === "distV") return $.global.flexArrangeLayers_FlexGUI(direction, alignTo);

    app.beginUndoGroup("Align Layers " + direction);
    try {
        var layers = [];
        for (var _selSnap = c.selectedLayers, i = 0; i < _selSnap.length; i++) {
            var l = _selSnap[i];
            if (l.property("ADBE Transform Group") && l.property("ADBE Transform Group").property("ADBE Position")) {
                layers.push(l);
            }
        }
        if (layers.length === 0) { app.endUndoGroup(); return; }
        if ((alignTo === "selection" || alignTo === "key") && layers.length < 2) alignTo = "comp";

        
        var compLeft = 0;
        var compRight = c.width;
        var compTop = 0;
        var compBottom = c.height;
        var compCenterX = c.width / 2;
        var compCenterY = c.height / 2;

        if (alignTo === "selection" || alignTo === "key") {
            var minLeft = 999999;
            var maxRight = -999999;
            var minTop = 999999;
            var maxBottom = -999999;

            var refLayers = layers;
            
            if (alignTo === "key" && layers.length >= 1) {
                refLayers = [layers[layers.length - 1]];
            }

            for (var k = 0; k < refLayers.length; k++) {
                var rl = refLayers[k];
                var rRect = rl.sourceRectAtTime(c.time, false);
                var rTForm = rl.property("ADBE Transform Group");
                var rAnchor = rTForm.property("ADBE Anchor Point").value;
                var rScale = rTForm.property("ADBE Scale").value;
                var rPos = getPos(rl);

                
                var rParentScaleX = 1;
                var rParentScaleY = 1;
                var rp = rl.parent;
                while (rp) {
                    try {
                        var rpTForm = rp.property("ADBE Transform Group");
                        if (rpTForm) {
                            var rpScaleProp = rpTForm.property("ADBE Scale");
                            if (rpScaleProp) {
                                var rpScale = rpScaleProp.value;
                                rParentScaleX *= (rpScale[0] / 100);
                                rParentScaleY *= (rpScale[1] / 100);
                            }
                        }
                    } catch (parentScaleErr) {}
                    rp = rp.parent;
                }

                var rEffScaleX = (rScale[0] / 100) * rParentScaleX;
                var rEffScaleY = (rScale[1] / 100) * rParentScaleY;

                var rWorldX, rWorldY;
                if (rl.parent) {
                    var rWorldPt = getLayerWorldPos(rl, c.time);
                    rWorldX = rWorldPt[0];
                    rWorldY = rWorldPt[1];
                } else {
                    rWorldX = rPos[0];
                    rWorldY = rPos[1];
                }

                var rLeft = rWorldX + (rRect.left - rAnchor[0]) * rEffScaleX;
                var rRight = rLeft + rRect.width * rEffScaleX;
                var rTop = rWorldY + (rRect.top - rAnchor[1]) * rEffScaleY;
                var rBottom = rTop + rRect.height * rEffScaleY;

                if (rLeft < minLeft) minLeft = rLeft;
                if (rRight > maxRight) maxRight = rRight;
                if (rTop < minTop) minTop = rTop;
                if (rBottom > maxBottom) maxBottom = rBottom;
            }

            if (minLeft !== 999999) {
                compLeft = minLeft;
                compRight = maxRight;
                compTop = minTop;
                compBottom = maxBottom;
                compCenterX = (compLeft + compRight) / 2;
                compCenterY = (compTop + compBottom) / 2;
            }
        }

        for (var j = 0; j < layers.length; j++) {
            var l = layers[j];
            
            if (alignTo === "key" && j === layers.length - 1) continue;

            var rect = l.sourceRectAtTime(c.time, false);
            var tForm = l.property("ADBE Transform Group");
            var pos = getPos(l);
            var anchor = tForm.property("ADBE Anchor Point").value;
            var scale = tForm.property("ADBE Scale").value;

            var parentScaleX = 1;
            var parentScaleY = 1;
            var p = l.parent;
            while (p) {
                try {
                    var pTForm = p.property("ADBE Transform Group");
                    if (pTForm) {
                        var pScaleProp = pTForm.property("ADBE Scale");
                        if (pScaleProp) {
                            var pScale = pScaleProp.value;
                            parentScaleX *= (pScale[0] / 100);
                            parentScaleY *= (pScale[1] / 100);
                        }
                    }
                } catch (parentScaleErr) {}
                p = p.parent;
            }

            var effScaleX = (scale[0] / 100) * parentScaleX;
            var effScaleY = (scale[1] / 100) * parentScaleY;

            var worldX, worldY;
            if (l.parent) {
                var worldPt = getLayerWorldPos(l, c.time);
                worldX = worldPt[0];
                worldY = worldPt[1];
            } else {
                worldX = pos[0];
                worldY = pos[1];
            }

            var layerLeft = worldX + (rect.left - anchor[0]) * effScaleX;
            var layerRight = layerLeft + rect.width * effScaleX;
            var layerTop = worldY + (rect.top - anchor[1]) * effScaleY;
            var layerBottom = layerTop + rect.height * effScaleY;
            var layerCenterX = (layerLeft + layerRight) / 2;
            var layerCenterY = (layerTop + layerBottom) / 2;

            var deltaX = 0;
            var deltaY = 0;

            if (direction === "left") {
                deltaX = compLeft - layerLeft;
            } else if (direction === "center") {
                deltaX = compCenterX - layerCenterX;
            } else if (direction === "right") {
                deltaX = compRight - layerRight;
            } else if (direction === "top") {
                deltaY = compTop - layerTop;
            } else if (direction === "middle") {
                deltaY = compCenterY - layerCenterY;
            } else if (direction === "bottom") {
                deltaY = compBottom - layerBottom;
            }

            if (l.parent) {
                var localDeltaX = deltaX / parentScaleX;
                var localDeltaY = deltaY / parentScaleY;
                setPos(l, [
                    pos[0] + localDeltaX,
                    pos[1] + localDeltaY,
                    pos.length > 2 ? pos[2] : 0
                ]);
            } else {
                setPos(l, [
                    pos[0] + deltaX,
                    pos[1] + deltaY,
                    pos.length > 2 ? pos[2] : 0
                ]);
            }
        }
    } catch (e) {
        app.endUndoGroup();
        return "ERR:" + e.toString();
    }
    app.endUndoGroup();
    return "SUCCESS";
}



$.global.alignLayers_FlexGUI_v2_disabled = function (directionModeStr) {
    if ($._flex && $._flex.isLocked) return "ERR:Extension is locked.";

    var comp = app.project.activeItem;
    if (!comp || !(comp instanceof CompItem)) return "ERR:Open a composition first.";
    if (!comp.selectedLayers || comp.selectedLayers.length < 1) return "ERR:Select at least one layer.";

    var parts = String(directionModeStr || "").split("|");
    var direction = parts[0] || "";
    var alignTo = parts.length > 1 ? parts[1] : "comp";
    if (direction !== "left" && direction !== "center" && direction !== "right" && direction !== "top" && direction !== "middle" && direction !== "bottom") {
        return "ERR:Unknown alignment direction.";
    }
    if (alignTo !== "comp" && alignTo !== "selection" && alignTo !== "key") alignTo = "comp";

    function valueNow(prop) {
        try { return prop.valueAtTime(comp.time, false); } catch (e) { return prop.value; }
    }

    function setNow(prop, value) {
        if (!prop) return false;
        try {
            if (prop.numKeys && prop.numKeys > 0) prop.setValueAtTime(comp.time, value);
            else prop.setValue(value);
            return true;
        } catch (e) { return false; }
    }

    function getPosition(layer) {
        var transform = layer.property("ADBE Transform Group");
        var position = transform ? transform.property("ADBE Position") : null;
        if (!position) return null;
        if (position.dimensionsSeparated) {
            var xProp = transform.property("ADBE Position_0");
            var yProp = transform.property("ADBE Position_1");
            var zProp = transform.property("ADBE Position_2");
            return [valueNow(xProp), valueNow(yProp), zProp ? valueNow(zProp) : 0];
        }
        var value = valueNow(position);
        return [value[0], value[1], value.length > 2 ? value[2] : 0];
    }

    function setPosition(layer, value) {
        var transform = layer.property("ADBE Transform Group");
        var position = transform ? transform.property("ADBE Position") : null;
        if (!position) return false;
        if (position.dimensionsSeparated) {
            var okX = setNow(transform.property("ADBE Position_0"), value[0]);
            var okY = setNow(transform.property("ADBE Position_1"), value[1]);
            var zProp = transform.property("ADBE Position_2");
            if (zProp) setNow(zProp, value[2]);
            return okX && okY;
        }
        var original = valueNow(position);
        if (original.length > 2) return setNow(position, [value[0], value[1], value[2]]);
        return setNow(position, [value[0], value[1]]);
    }

    function pointToComp(layer, point) {
        try {
            var result = layer.sourcePointToComp([point[0], point[1]]);
            if (result && result.length >= 2) return [result[0], result[1]];
        } catch (e) { }
        try {
            var transform = layer.property("ADBE Transform Group");
            var anchor = valueNow(transform.property("ADBE Anchor Point"));
            var scale = valueNow(transform.property("ADBE Scale"));
            var position = getPosition(layer);
            if (position) return [position[0] + (point[0] - anchor[0]) * scale[0] / 100, position[1] + (point[1] - anchor[1]) * scale[1] / 100];
        } catch (fallbackError) { }
        return null;
    }

    function getBounds(layer) {
        var transform = layer.property("ADBE Transform Group");
        if (!transform) return null;
        var anchorProp = transform.property("ADBE Anchor Point");
        var anchor = anchorProp ? valueNow(anchorProp) : [0, 0, 0];
        var rect = null;
        try { rect = layer.sourceRectAtTime(comp.time, false); } catch (e) { rect = null; }

        var points = [];
        if (rect && isFinite(rect.left) && isFinite(rect.top) && isFinite(rect.width) && isFinite(rect.height)) {
            points.push([rect.left, rect.top, 0]);
            points.push([rect.left + rect.width, rect.top, 0]);
            points.push([rect.left, rect.top + rect.height, 0]);
            points.push([rect.left + rect.width, rect.top + rect.height, 0]);
        } else {
            points.push([anchor[0], anchor[1], anchor.length > 2 ? anchor[2] : 0]);
        }

        var minX = 999999999;
        var maxX = -999999999;
        var minY = 999999999;
        var maxY = -999999999;
        for (var i = 0; i < points.length; i++) {
            var compPoint = pointToComp(layer, points[i]);
            if (!compPoint) continue;
            if (compPoint[0] < minX) minX = compPoint[0];
            if (compPoint[0] > maxX) maxX = compPoint[0];
            if (compPoint[1] < minY) minY = compPoint[1];
            if (compPoint[1] > maxY) maxY = compPoint[1];
        }

        if (minX === 999999999) {
            var position = getPosition(layer);
            if (!position) return null;
            minX = maxX = position[0];
            minY = maxY = position[1];
        }
        return { left: minX, right: maxX, top: minY, bottom: maxY, centerX: (minX + maxX) / 2, centerY: (minY + maxY) / 2 };
    }

    function unionBounds(layers) {
        var result = null;
        for (var i = 0; i < layers.length; i++) {
            var bounds = getBounds(layers[i]);
            if (!bounds) continue;
            if (!result) result = { left: bounds.left, right: bounds.right, top: bounds.top, bottom: bounds.bottom };
            else {
                if (bounds.left < result.left) result.left = bounds.left;
                if (bounds.right > result.right) result.right = bounds.right;
                if (bounds.top < result.top) result.top = bounds.top;
                if (bounds.bottom > result.bottom) result.bottom = bounds.bottom;
            }
        }
        if (result) {
            result.centerX = (result.left + result.right) / 2;
            result.centerY = (result.top + result.bottom) / 2;
        }
        return result;
    }

    function compDeltaToPositionDelta(layer, deltaX, deltaY) {
        if (!layer.parent) return [deltaX, deltaY];
        try {
            var transform = layer.property("ADBE Transform Group");
            var anchorProp = transform ? transform.property("ADBE Anchor Point") : null;
            var anchor = anchorProp ? valueNow(anchorProp) : [0, 0, 0];
            var worldAnchor = pointToComp(layer, anchor);
            var localA = layer.parent.compPointToSource([worldAnchor[0], worldAnchor[1]]);
            var localB = layer.parent.compPointToSource([worldAnchor[0] + deltaX, worldAnchor[1] + deltaY]);
            return [localB[0] - localA[0], localB[1] - localA[1]];
        } catch (e) { return [deltaX, deltaY]; }
    }

    var layers = [];
    for (var _selSnap = comp.selectedLayers, i = 0; i < _selSnap.length; i++) {
        var selected = _selSnap[i];
        if (!selected.locked && getPosition(selected)) layers.push(selected);
    }
    if (layers.length < 1) return "ERR:No movable selected layers.";
    if (alignTo === "key" && layers.length < 2) return "ERR:Select at least two layers for Key Object alignment.";

    var keyLayer = alignTo === "key" ? layers[layers.length - 1] : null;
    var target = null;
    if (alignTo === "comp") {
        target = { left: 0, right: comp.width, top: 0, bottom: comp.height, centerX: comp.width / 2, centerY: comp.height / 2 };
    } else if (alignTo === "key") {
        target = getBounds(keyLayer);
    } else {
        target = unionBounds(layers);
    }
    if (!target) return "ERR:Unable to calculate alignment bounds.";

    var moved = 0;
    app.beginUndoGroup("Flex Align Layers");
    try {
        for (var j = 0; j < layers.length; j++) {
            var layer = layers[j];
            if (layer === keyLayer) continue;
            var bounds = getBounds(layer);
            var position = getPosition(layer);
            if (!bounds || !position) continue;

            var dx = 0;
            var dy = 0;
            if (direction === "left") dx = target.left - bounds.left;
            else if (direction === "center") dx = target.centerX - bounds.centerX;
            else if (direction === "right") dx = target.right - bounds.right;
            else if (direction === "top") dy = target.top - bounds.top;
            else if (direction === "middle") dy = target.centerY - bounds.centerY;
            else if (direction === "bottom") dy = target.bottom - bounds.bottom;

            var localDelta = compDeltaToPositionDelta(layer, dx, dy);
            if (setPosition(layer, [position[0] + localDelta[0], position[1] + localDelta[1], position[2]])) moved++;
        }
    } catch (error) {
        try { app.endUndoGroup(); } catch (endError) { }
        return "ERR:" + error.toString();
    }
    
    
    try { comp.time = comp.time; } catch (refreshError) { }
    app.endUndoGroup();
    return "SUCCESS:" + moved;
};











$.global.FLEX_ALIGN_VERSION = 3;
$.global.flexArrangeLayers_FlexGUI = function (direction, mode) {
    if ($._flex && $._flex.isLocked) return "ERR:Extension is locked.";
    var comp = app.project.activeItem;
    if (!comp || !(comp instanceof CompItem)) return "ERR:Open a composition first.";
    var distribute = (direction === "distH" || direction === "distV");
    var sel = comp.selectedLayers;
    if (!sel || sel.length < 1) return distribute ? "ERR:Select 3 or more layers to distribute." : "ERR:Select the layers to align.";
    if (!distribute && direction !== "left" && direction !== "center" && direction !== "right" && direction !== "top" && direction !== "middle" && direction !== "bottom") return "ERR:Unknown alignment direction.";
    var t = comp.time, DEG = Math.PI / 180, EPS = 0.001, TOL = 0.01, notes = [];
    var IDENT = { a: 1, b: 0, c: 0, d: 1, e: 0, f: 0 };
    var compPar = 1; try { if (comp.pixelAspect > 0) compPar = comp.pixelAspect; } catch (ePar) { }

    function tform(l) { try { return l.property("ADBE Transform Group"); } catch (e) { return null; } }
    function prop(tf, name) { try { return tf ? tf.property(name) : null; } catch (e) { return null; } }
    function now(p, dflt) { if (!p) return dflt; try { return p.valueAtTime(t, false); } catch (e) { try { return p.value; } catch (e2) { return dflt; } } }
    function isArr(v) { return v !== null && typeof v === "object" && typeof v.length === "number"; }
    function pair(v, d) { if (isArr(v)) return [v[0], v.length > 1 ? v[1] : d]; return [v, d]; }
    function parentOf(l) { try { return l.parent; } catch (e) { return null; } }
    function isCamLight(l) { try { return (l instanceof CameraLayer) || (l instanceof LightLayer); } catch (e) { return false; } }
    function is3D(l) { try { return l.threeDLayer === true; } catch (e) { return false; } }
    
    function parOf(l) {
        if (isCamLight(l)) return compPar;
        try { var src = l.source; if (src && src.pixelAspect > 0) return src.pixelAspect; } catch (e) { }
        return compPar;
    }
    
    function localMatrix(l) {
        var tf = tform(l); if (!tf) return IDENT;
        var pos = prop(tf, "ADBE Position"), P = [0, 0], A = [0, 0], S = [100, 100], R = 0, cam = isCamLight(l);
        if (pos && pos.dimensionsSeparated) P = [now(prop(tf, "ADBE Position_0"), 0), now(prop(tf, "ADBE Position_1"), 0)];
        else if (pos) P = pair(now(pos, [0, 0]), 0);
        if (!cam) { A = pair(now(prop(tf, "ADBE Anchor Point"), [0, 0]), 0); S = pair(now(prop(tf, "ADBE Scale"), [100, 100]), 100); }
        R = now(prop(tf, "ADBE Rotate Z"), 0);
        if (cam || is3D(l)) { var o = now(prop(tf, "ADBE Orientation"), null); if (isArr(o) && o.length > 2) R += o[2]; }
        var up = parentOf(l), outer = up ? parOf(up) : compPar, inner = parOf(l);
        var cs = Math.cos(R * DEG), sn = Math.sin(R * DEG), sx = S[0] / 100, sy = S[1] / 100;
        var a = cs * sx * inner / outer, b = sn * sx * inner, c = -sn * sy / outer, d = cs * sy;
        return { a: a, b: b, c: c, d: d, e: P[0] - (a * A[0] + c * A[1]), f: P[1] - (b * A[0] + d * A[1]) };
    }
    function mul(m, n) { return { a: m.a * n.a + m.c * n.b, b: m.b * n.a + m.d * n.b, c: m.a * n.c + m.c * n.d, d: m.b * n.c + m.d * n.d, e: m.a * n.e + m.c * n.f + m.e, f: m.b * n.e + m.d * n.f + m.f }; }
    function parentMatrix(l) {
        var m = IDENT, p = parentOf(l);
        while (p) { m = mul(localMatrix(p), m); p = parentOf(p); }
        return m;
    }
    function mathMeasure(l) {
        var r = null; try { r = l.sourceRectAtTime(t, false); } catch (e) { return null; }
        if (!r) return null;
        var pm = parentMatrix(l), m = mul(pm, localMatrix(l));
        var xs = [r.left, r.left + r.width, r.left + r.width, r.left], ys = [r.top, r.top, r.top + r.height, r.top + r.height];
        var bb = { l: Infinity, r: -Infinity, t: Infinity, b: -Infinity };
        for (var i = 0; i < 4; i++) {
            var X = m.a * xs[i] + m.c * ys[i] + m.e, Y = m.b * xs[i] + m.d * ys[i] + m.f;
            if (X < bb.l) bb.l = X; if (X > bb.r) bb.r = X; if (Y < bb.t) bb.t = Y; if (Y > bb.b) bb.b = Y;
        }
        return { bb: bb, J: { a: pm.a, b: pm.b, c: pm.c, d: pm.d } };
    }
    
    var camOn = false;
    try { camOn = !!comp.activeCamera; } catch (eCam) { for (var ci = 1; ci <= comp.numLayers; ci++) { var CL = comp.layer(ci); try { if (CL instanceof CameraLayer && CL.enabled && CL.inPoint <= t && CL.outPoint > t) { camOn = true; break; } } catch (eC) { } } }
    function nonZero(v, i) { if (isArr(v)) return v.length > i && Math.abs(v[i]) > EPS; return i === 0 && Math.abs(v) > EPS; }
    function lyingFlat(l) {
        var tf = tform(l), pos = prop(tf, "ADBE Position");
        if (pos && pos.dimensionsSeparated) { if (nonZero(now(prop(tf, "ADBE Position_2"), 0), 0)) return false; }
        else if (nonZero(now(pos, [0, 0, 0]), 2)) return false;
        if (nonZero(now(prop(tf, "ADBE Anchor Point"), [0, 0, 0]), 2)) return false;
        if (nonZero(now(prop(tf, "ADBE Rotate X"), 0), 0) || nonZero(now(prop(tf, "ADBE Rotate Y"), 0), 0)) return false;
        var o = now(prop(tf, "ADBE Orientation"), [0, 0, 0]);
        return !(nonZero(o, 0) || nonZero(o, 1));
    }
    function needsAE(l) {
        var x = l;
        while (x) {
            if (isCamLight(x)) return true;
            try { if (x.autoOrient !== AutoOrientType.NO_AUTO_ORIENT) return true; } catch (eAo) { }
            if (is3D(x) && (camOn || !lyingFlat(x))) return true;
            x = parentOf(x);
        }
        return false;
    }
    
    function aeExpr(d3, k) {
        var pt = d3 ? "[x, y, 0]" : "[x, y]", ux = d3 ? "[1, 0, 0]" : "[1, 0]", uy = d3 ? "[0, 1, 0]" : "[0, 1]";
        return "var r = sourceRectAtTime(time, false);\n" +
            "function pt(x, y) { return " + pt + "; }\n" +
            "var q = [toComp(pt(r.left, r.top)), toComp(pt(r.left + r.width, r.top)), toComp(pt(r.left + r.width, r.top + r.height)), toComp(pt(r.left, r.top + r.height))];\n" +
            "var A = transform.anchorPoint;\n" +
            "var s0 = toComp(A);\n" +
            "var w0 = toWorld(A);\n" +
            "var ex = " + ux + ";\n" +
            "var ey = " + uy + ";\n" +
            "if (hasParent) { ex = parent.toWorldVec(ex); ey = parent.toWorldVec(ey); }\n" +
            "var sx = toComp(fromWorld(add(w0, ex)));\n" +
            "var sy = toComp(fromWorld(add(w0, ey)));\n" +
            "var o = [Math.min(q[0][0], q[1][0], q[2][0], q[3][0]), Math.max(q[0][0], q[1][0], q[2][0], q[3][0]), Math.min(q[0][1], q[1][1], q[2][1], q[3][1]), Math.max(q[0][1], q[1][1], q[2][1], q[3][1]), sx[0] - s0[0], sx[1] - s0[1], sy[0] - s0[0], sy[1] - s0[1]];\n" +
            "[o[" + k + "], o[" + (k + 1) + "]]";
    }
    
    var probes = [];
    function aeMeasure(it) {
        var out = [], d3 = is3D(it.layer);
        try {
            if (!it.probe) { it.probe = it.layer.property("ADBE Effect Parade").addProperty("ADBE Point Control"); probes.push(it.probe); }
            var ctl = it.probe.property(1);
            for (var k = 0; k < 8; k += 2) {
                ctl.expression = aeExpr(d3, k);
                var v = ctl.valueAtTime(t, false), err = "";
                try { err = ctl.expressionError; } catch (eE) { err = ""; }
                if (err || !isArr(v)) { out = null; break; }
                out.push(v[0], v[1]);
            }
        } catch (e) { out = null; }
        if (!out || out.length < 8) return null;
        for (var n = 0; n < 8; n++) { if (typeof out[n] !== "number" || !isFinite(out[n])) return null; }
        return { bb: { l: out[0], r: out[1], t: out[2], b: out[3] }, J: { a: out[4], b: out[5], c: out[6], d: out[7] } };
    }
    function removeProbes() { for (var i = probes.length - 1; i >= 0; i--) { try { probes[i].remove(); } catch (e) { } } probes = []; }
    

    function shift(p, delta) {
        var n = 0; try { n = p.numKeys; } catch (e) { n = 0; }
        if (n > 0) {
            for (var k = 1; k <= n; k++) {
                var kv = p.keyValue(k);
                if (isArr(kv)) { var nv = []; for (var q = 0; q < kv.length; q++) nv.push(kv[q] + (q < delta.length ? delta[q] : 0)); p.setValueAtKey(k, nv); }
                else p.setValueAtKey(k, kv + delta[0]);
            }
        } else {
            var v = null; try { v = p.valueAtTime(t, true); } catch (eV) { v = p.value; }
            if (isArr(v)) { var nv2 = []; for (var q2 = 0; q2 < v.length; q2++) nv2.push(v[q2] + (q2 < delta.length ? delta[q2] : 0)); p.setValue(nv2); }
            else p.setValue(v + delta[0]);
        }
    }
    function moveLocal(l, dx, dy) {
        var tf = tform(l), pos = prop(tf, "ADBE Position");
        if (pos.dimensionsSeparated) {
            if (Math.abs(dx) > 0) shift(prop(tf, "ADBE Position_0"), [dx]);
            if (Math.abs(dy) > 0) shift(prop(tf, "ADBE Position_1"), [dy]);
        } else shift(pos, [dx, dy]);
    }

    
    var items = [], skipped = 0;
    for (var s = 0; s < sel.length; s++) {
        var L = sel[s], ok = false;
        try { ok = !!prop(tform(L), "ADBE Position") && !isCamLight(L); } catch (eOk) { ok = false; }
        try { if (ok && L.hasVideo === false && !L.nullLayer) ok = false; } catch (eAv) { }
        if (!ok) { skipped++; continue; }
        items.push({ layer: L, idx: L.index, viaAE: needsAE(L) });
    }
    if (!items.length) return "ERR:None of the selected layers can be moved (cameras, lights and sound layers have no position to align).";
    if (distribute && items.length < 3) return "ERR:Select 3 or more layers to distribute.";
    for (var lk = 0; lk < items.length; lk++) { var lkL = false; try { lkL = items[lk].layer.locked; } catch (eLk) { } if (lkL) return "ERR:Unlock \"" + items[lk].layer.name + "\" first: moving the others without it would change the spacing."; }

    var fellBack = 0;
    function measure(it) {
        if (it.viaAE) { var m = aeMeasure(it); if (m) return m; it.viaAE = false; fellBack++; }
        return mathMeasure(it.layer);
    }

    app.beginUndoGroup(distribute ? "Distribute Layers" : "Align as Group");
    var moved = 0, stuck = [], gap = 0, kept = [];
    try {
        for (var mi = 0; mi < items.length; mi++) { var mm = measure(items[mi]); if (mm) { items[mi].bb = mm.bb; kept.push(items[mi]); } else skipped++; }
        items = kept;
        if (!items.length || (distribute && items.length < 3)) {
            removeProbes();
            app.endUndoGroup();
            return distribute ? "ERR:Select 3 or more layers to distribute." : "ERR:None of the selected layers can be moved.";
        }

        


        var order = items.slice(0), horiz = (direction === "distH"), i2, anyAE = false;
        for (i2 = 0; i2 < items.length; i2++) { if (items[i2].viaAE) anyAE = true; items[i2].cur = items[i2].bb; }
        if (distribute) {
            order.sort(function (p, q) {
                var cp = p.bb.t + p.bb.b;
                var cq = q.bb.t + q.bb.b;
                if (horiz) { cp = p.bb.l + p.bb.r; cq = q.bb.l + q.bb.r; }
                if (Math.abs(cp - cq) > EPS) return cp - cq;
                return p.idx - q.idx;
            });
        }
        var U0 = { l: Infinity, r: -Infinity, t: Infinity, b: -Infinity };
        for (i2 = 0; i2 < items.length; i2++) { var b0 = items[i2].bb; if (b0.l < U0.l) U0.l = b0.l; if (b0.r > U0.r) U0.r = b0.r; if (b0.t < U0.t) U0.t = b0.t; if (b0.b > U0.b) U0.b = b0.b; }
        function plan() {
            var U = { l: Infinity, r: -Infinity, t: Infinity, b: -Infinity }, k;
            for (k = 0; k < items.length; k++) { var cb = items[k].cur; if (cb.l < U.l) U.l = cb.l; if (cb.r > U.r) U.r = cb.r; if (cb.t < U.t) U.t = cb.t; if (cb.b > U.b) U.b = cb.b; }
            for (k = 0; k < items.length; k++) { items[k].goalL = items[k].cur.l; items[k].goalT = items[k].cur.t; }
            if (!distribute) {
                var gx = 0, gy = 0;
                if (direction === "left") gx = -U.l;
                else if (direction === "center") gx = comp.width / 2 - (U.l + U.r) / 2;
                else if (direction === "right") gx = comp.width - U.r;
                else if (direction === "top") gy = -U.t;
                else if (direction === "middle") gy = comp.height / 2 - (U.t + U.b) / 2;
                else if (direction === "bottom") gy = comp.height - U.b;
                for (k = 0; k < items.length; k++) { items[k].goalL += gx; items[k].goalT += gy; }
                return;
            }
            
            var start = U0.t, end = U0.b, total = 0;
            if (horiz) { start = U0.l; end = U0.r; }
            for (k = 0; k < order.length; k++) {
                if (horiz) total += order[k].cur.r - order[k].cur.l;
                else total += order[k].cur.b - order[k].cur.t;
            }
            gap = (end - start - total) / (order.length - 1);
            var cursor = start;
            for (k = 0; k < order.length; k++) {
                var ob = order[k].cur;
                if (horiz) { order[k].goalL = cursor; cursor += (ob.r - ob.l) + gap; }
                else { order[k].goalT = cursor; cursor += (ob.b - ob.t) + gap; }
            }
        }

        

        function depth(l) { var n = 0, p = parentOf(l); while (p) { n++; p = parentOf(p); } return n; }
        for (i2 = 0; i2 < items.length; i2++) items[i2].depth = depth(items[i2].layer);
        var work = items.slice(0);
        work.sort(function (p, q) { if (p.depth !== q.depth) return p.depth - q.depth; return p.idx - q.idx; });
        var rounds = anyAE ? 4 : 1, touchedBy = {};
        for (var round = 0; round < rounds; round++) {
            if (round > 0) {
                var settled = true;
                for (i2 = 0; i2 < items.length; i2++) { var re = measure(items[i2]); if (re) items[i2].cur = re.bb; }
                plan();
                for (i2 = 0; i2 < items.length; i2++) { if (Math.abs(items[i2].goalL - items[i2].cur.l) > TOL || Math.abs(items[i2].goalT - items[i2].cur.t) > TOL) { settled = false; break; } }
                if (settled) break;
            } else plan();
            for (var w = 0; w < work.length; w++) {
                var W = work[w];
                for (var pass = 0; pass < 3; pass++) {
                    var cur = measure(W);
                    if (!cur) break;
                    W.cur = cur.bb;
                    var rx = W.goalL - cur.bb.l, ry = W.goalT - cur.bb.t;
                    if (Math.abs(rx) < TOL && Math.abs(ry) < TOL) break;
                    var J = cur.J, det = J.a * J.d - J.b * J.c;
                    if (Math.abs(det) < 1e-9) break;
                    moveLocal(W.layer, (J.d * rx - J.c * ry) / det, (-J.b * rx + J.a * ry) / det);
                    touchedBy[W.idx] = true;
                }
            }
        }
        for (var w2 = 0; w2 < work.length; w2++) {
            var W2 = work[w2], fin = measure(W2);
            if (!fin || Math.abs(W2.goalL - fin.bb.l) > 0.5 || Math.abs(W2.goalT - fin.bb.t) > 0.5) stuck.push(W2.layer.name);
            if (touchedBy[W2.idx]) moved++;
        }
    } catch (err) {
        removeProbes();
        try { app.endUndoGroup(); } catch (endErr) { }
        return "ERR:" + err.toString();
    }
    removeProbes();
    try { comp.time = comp.time; } catch (refreshError) { }
    app.endUndoGroup();

    if (stuck.length) notes.push((stuck.length === 1 ? "\"" + stuck[0] + "\" could not be moved into place" : stuck.length + " layers could not be moved into place") + " (a position expression or a parent scaled to 0 holds it)");
    if (skipped) notes.push(skipped + (skipped === 1 ? " camera, light or sound layer was" : " camera, light or sound layers were") + " left out");
    if (fellBack) notes.push("3D layers were measured from the front");
    var head;
    if (distribute) head = "Distributed " + items.length + " layers, " + Math.round(gap * 10) / 10 + " px apart";
    else head = (items.length === 1 ? "Aligned 1 layer" : "Aligned " + items.length + " layers as a group");
    return "OK:" + head + (notes.length ? " · " + notes.join(" · ") : "");
};
