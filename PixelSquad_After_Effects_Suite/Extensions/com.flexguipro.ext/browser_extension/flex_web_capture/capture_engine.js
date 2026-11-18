


















(function (root) {
    'use strict';

    var VERSION = 1;

    
    var SKIP_TAGS = {
        SCRIPT: 1, STYLE: 1, NOSCRIPT: 1, LINK: 1, META: 1, HEAD: 1, TITLE: 1,
        TEMPLATE: 1, SOURCE: 1, TRACK: 1, PARAM: 1, BASE: 1, MAP: 1, AREA: 1,
        BR: 1, WBR: 1, COL: 1, COLGROUP: 1
    };

    


    var BLOCKISH = /^(block|flex|grid|table|list-item|flow-root|table-row|table-cell|table-row-group|table-header-group|table-footer-group|-webkit-box|grid-template)/;

    var WEIGHT_STYLE = {
        100: 'Thin', 200: 'ExtraLight', 300: 'Light', 400: 'Regular',
        500: 'Medium', 600: 'SemiBold', 700: 'Bold', 800: 'ExtraBold', 900: 'Black'
    };

    




    var probeCtx = null;

    function probe() {
        if (probeCtx) return probeCtx;
        var c = document.createElement('canvas');
        c.width = c.height = 1;
        probeCtx = c.getContext('2d', { willReadFrequently: true });
        return probeCtx;
    }

    function parseColor(str) {
        if (!str) return null;
        str = String(str).trim();
        if (!str || str === 'none' || str === 'transparent') return null;
        var ctx = probe();
        if (!ctx) return null;
        try {
            ctx.clearRect(0, 0, 1, 1);
            ctx.fillStyle = '#000000';
            ctx.fillStyle = str;               
            if (ctx.fillStyle === '#000000' && !/^(#0{3,8}|black|rgba?\(\s*0\s*,\s*0\s*,\s*0)/i.test(str)) return null;
            ctx.globalCompositeOperation = 'copy';
            ctx.fillRect(0, 0, 1, 1);
            ctx.globalCompositeOperation = 'source-over';
            var d = ctx.getImageData(0, 0, 1, 1).data;
            if (d[3] === 0) return null;
            return { r: d[0], g: d[1], b: d[2], a: d[3] / 255 };
        } catch (e) { return null; }
    }

    function hex(c) {
        if (!c) return '';
        function h(n) { n = Math.max(0, Math.min(255, Math.round(n))).toString(16); return n.length < 2 ? '0' + n : n; }
        return '#' + h(c.r) + h(c.g) + h(c.b);
    }

    

    function num(v) { var n = parseFloat(v); return isFinite(n) ? n : 0; }
    function round(n, p) { var m = Math.pow(10, p == null ? 2 : p); return Math.round(n * m) / m; }

    function rectOf(el) {
        var r = el.getBoundingClientRect();
        return { x: r.left, y: r.top, w: r.width, h: r.height, r: r.right, b: r.bottom };
    }

    function intersects(a, b) {
        return !(a.x > b.x + b.w || a.x + a.w < b.x || a.y > b.y + b.h || a.y + a.h < b.y);
    }

    function clipRect(a, b) {
        var x = Math.max(a.x, b.x), y = Math.max(a.y, b.y);
        var r = Math.min(a.x + a.w, b.x + b.w), bt = Math.min(a.y + a.h, b.y + b.h);
        return { x: x, y: y, w: Math.max(0, r - x), h: Math.max(0, bt - y) };
    }

    


    function visibleFraction(a, b) {
        var area = a.w * a.h;
        if (area <= 0) return 1;
        var c = clipRect(a, b);
        return (c.w * c.h) / area;
    }

    

    function radii(cs, w, h) {
        function one(v) {
            if (!v) return 0;
            var parts = String(v).split(/\s+/);
            var p = parts[0];
            if (/%$/.test(p)) return num(p) / 100 * Math.min(w, h);
            return num(p);
        }
        var tl = one(cs.borderTopLeftRadius), tr = one(cs.borderTopRightRadius);
        var br = one(cs.borderBottomRightRadius), bl = one(cs.borderBottomLeftRadius);
        
        var f = 1;
        [[tl + tr, w], [bl + br, w], [tl + bl, h], [tr + br, h]].forEach(function (p) {
            if (p[0] > p[1] && p[0] > 0) f = Math.min(f, p[1] / p[0]);
        });
        return [tl * f, tr * f, br * f, bl * f].map(function (n) { return round(n, 2); });
    }

    function border(cs) {
        var sides = ['Top', 'Right', 'Bottom', 'Left'];
        var widths = [], colors = [], styles = [];
        for (var i = 0; i < 4; i++) {
            var s = cs['border' + sides[i] + 'Style'];
            var w = num(cs['border' + sides[i] + 'Width']);
            widths.push(s === 'none' || s === 'hidden' ? 0 : w);
            colors.push(parseColor(cs['border' + sides[i] + 'Color']));
            styles.push(s);
        }
        var max = Math.max.apply(null, widths);
        if (max <= 0) return null;
        

        var uniform = widths[0] === widths[1] && widths[1] === widths[2] && widths[2] === widths[3] && widths[0] > 0;
        var c = colors[widths.indexOf(max)] || colors[0];
        if (!c) return null;
        return {
            width: round(max, 2),
            color: hex(c),
            alpha: round(c.a, 3),
            uniform: uniform,
            sides: widths.map(function (w) { return round(w, 2); }),
            dashed: styles[widths.indexOf(max)] === 'dashed' || styles[widths.indexOf(max)] === 'dotted'
        };
    }

    




    function screenReaderOnly(el, cs, w, h) {
        var clipped = (cs.clip && cs.clip !== 'auto') ||
            /hidden|clip/.test(String(cs.overflow) + cs.overflowX + cs.overflowY);
        if ((w <= 2 || h <= 2) && clipped) {
            var t = el.textContent;
            if (t && t.replace(/\s+/g, '')) return true;
        }
        if (cs.clipPath && /inset\(\s*(50|100)%/.test(cs.clipPath)) return true;
        return false;
    }

    function shadow(cs) {
        var s = cs.boxShadow;
        if (!s || s === 'none') return null;
        
        var first = splitTop(s)[0];
        if (!first) return null;
        var inset = /inset/.test(first);
        var col = first.match(/(rgba?\([^)]*\)|#[0-9a-f]{3,8}|color\([^)]*\)|oklch\([^)]*\)|hsla?\([^)]*\))/i);
        var nums = first.replace(/(rgba?|hsla?|color|oklch|oklab|lab|lch)\([^)]*\)/gi, '').match(/-?[\d.]+px/g) || [];
        var c = parseColor(col ? col[0] : 'rgba(0,0,0,.2)');
        if (!c) return null;
        return {
            x: round(num(nums[0]), 2), y: round(num(nums[1]), 2),
            blur: round(num(nums[2]), 2), spread: round(num(nums[3]), 2),
            color: hex(c), alpha: round(c.a, 3), inset: inset
        };
    }

    
    function splitTop(s) {
        var out = [], depth = 0, cur = '';
        for (var i = 0; i < s.length; i++) {
            var ch = s[i];
            if (ch === '(') depth++;
            else if (ch === ')') depth--;
            if (ch === ',' && depth === 0) { out.push(cur.trim()); cur = ''; continue; }
            cur += ch;
        }
        if (cur.trim()) out.push(cur.trim());
        return out;
    }

    function gradient(cs, w, h) {
        var bg = cs.backgroundImage;
        if (!bg || bg === 'none' || bg.indexOf('gradient') < 0) return null;
        var first = splitTop(bg)[0] || bg;
        var m = first.match(/^(repeating-)?(linear|radial|conic)-gradient\((.*)\)$/i);
        if (!m) return null;
        var kind = m[2].toLowerCase();
        if (kind === 'conic') return null;                 
        var parts = splitTop(m[3]);
        var angle = 180, head = parts[0];

        if (kind === 'linear') {
            if (/deg|rad|turn|to\s/i.test(head) && !/(rgba?|#|color|oklch|hsla?)/i.test(head)) {
                if (/deg/.test(head)) angle = num(head);
                else if (/rad/.test(head)) angle = num(head) * 180 / Math.PI;
                else if (/turn/.test(head)) angle = num(head) * 360;
                else {
                    var dir = { 'to top': 0, 'to right': 90, 'to bottom': 180, 'to left': 270 };
                    var key = head.trim().toLowerCase();
                    angle = dir[key] != null ? dir[key] : (
                        /top\s+right|right\s+top/.test(key) ? 45 :
                            /bottom\s+right|right\s+bottom/.test(key) ? 135 :
                                /bottom\s+left|left\s+bottom/.test(key) ? 225 :
                                    /top\s+left|left\s+top/.test(key) ? 315 : 180);
                }
                parts = parts.slice(1);
            }
        } else if (/(circle|ellipse|at\s|closest|farthest)/i.test(head) && !/(rgba?|#|color|oklch|hsla?)/i.test(head)) {
            parts = parts.slice(1);
        }

        var stops = [];
        parts.forEach(function (p, i) {
            var cm = p.match(/^(rgba?\([^)]*\)|hsla?\([^)]*\)|color\([^)]*\)|oklch\([^)]*\)|oklab\([^)]*\)|lab\([^)]*\)|lch\([^)]*\)|#[0-9a-fA-F]{3,8}|[a-z]+)/);
            if (!cm) return;
            var c = parseColor(cm[0]);
            if (!c) return;
            var posM = p.slice(cm[0].length).trim().match(/(-?[\d.]+)(%|px)?/);
            var pos = null;
            if (posM) {
                pos = posM[2] === 'px' ? num(posM[1]) / Math.max(1, kind === 'linear' ? h : Math.max(w, h)) : num(posM[1]) / 100;
            }
            stops.push({ c: hex(c), a: round(c.a, 3), p: pos });
        });
        if (stops.length < 2) return null;
        
        if (stops[0].p == null) stops[0].p = 0;
        if (stops[stops.length - 1].p == null) stops[stops.length - 1].p = 1;
        for (var i = 1; i < stops.length - 1; i++) {
            if (stops[i].p != null) continue;
            var prev = i - 1; while (stops[prev].p == null) prev--;
            var next = i + 1; while (next < stops.length && stops[next].p == null) next++;
            var span = next - prev;
            for (var k = prev + 1; k < next; k++) {
                stops[k].p = stops[prev].p + (stops[next].p - stops[prev].p) * ((k - prev) / span);
            }
        }
        stops.forEach(function (s) { s.p = round(Math.max(0, Math.min(1, s.p)), 4); });
        return { type: kind, angle: round(angle, 1), stops: stops };
    }

    function bgImageUrl(cs) {
        var bg = cs.backgroundImage;
        if (!bg || bg === 'none') return '';
        var m = splitTop(bg)[0].match(/url\((['"]?)(.*?)\1\)/);
        return m ? m[2] : '';
    }

    

    function decompose(cs) {
        var t = cs.transform;
        if (!t || t === 'none') return null;
        var m = t.match(/matrix(3d)?\(([^)]+)\)/);
        if (!m) return null;
        var v = m[2].split(',').map(num);
        var a, b, c, d;
        if (m[1]) { a = v[0]; b = v[1]; c = v[4]; d = v[5]; }
        else { a = v[0]; b = v[1]; c = v[2]; d = v[3]; }
        var sx = Math.sqrt(a * a + b * b), sy = Math.sqrt(c * c + d * d);
        var rot = Math.atan2(b, a) * 180 / Math.PI;
        if (Math.abs(rot) < 0.01 && Math.abs(sx - 1) < 0.001 && Math.abs(sy - 1) < 0.001) return null;
        return { rotate: round(rot, 2), sx: round(sx, 4), sy: round(sy, 4) };
    }

    

    function normText(s) {
        return String(s == null ? '' : s).replace(/ /g, ' ').replace(/[ \t]+/g, ' ').replace(/\s*\n\s*/g, '\n').trim();
    }

    function hasOwnText(el) {
        for (var i = 0; i < el.childNodes.length; i++) {
            var n = el.childNodes[i];
            if (n.nodeType === 3 && n.nodeValue && n.nodeValue.trim()) return true;
        }
        return false;
    }

    function isTextLeaf(el) {
        if (!hasOwnText(el) && !(el.children.length && !hasBlockChild(el) && normText(el.innerText))) return false;
        return !hasBlockChild(el);
    }

    

    function typeSig(cs) {
        return [cs.fontFamily, cs.fontSize, cs.fontWeight, cs.fontStyle,
            cs.color, cs.letterSpacing, cs.textTransform, cs.lineHeight].join('|');
    }

    







    function uniformType(el, cs) {
        var sig = typeSig(cs);
        var kids = el.children;
        var seen = 0;
        for (var i = 0; i < kids.length; i++) {
            var ch = kids[i];
            if (SKIP_TAGS[ch.tagName]) continue;
            if (!ch.textContent || !ch.textContent.replace(/\s+/g, '')) continue;
            var ks;
            try { ks = getComputedStyle(ch); } catch (e) { continue; }
            if (ks.display === 'none') continue;
            if (typeSig(ks) !== sig) return false;
            
            if (++seen < 24 && ch.children.length && !uniformType(ch, ks)) return false;
        }
        return true;
    }

    

    function textNodeLines(node) {
        var words = [];
        try {
            var s = node.nodeValue, rg = document.createRange(), i = 0;
            while (i < s.length) {
                while (i < s.length && /\s/.test(s[i])) i++;
                var start = i;
                while (i < s.length && !/\s/.test(s[i])) i++;
                if (i <= start) break;
                rg.setStart(node, start); rg.setEnd(node, i);
                var r = rg.getBoundingClientRect();
                if (r.width <= 0 && r.height <= 0) continue;
                words.push({ t: s.slice(start, i), x: r.left, y: r.top, w: r.width, h: r.height, b: r.bottom });
                if (words.length > 2000) break;
            }
        } catch (e) { return []; }
        if (!words.length) return [];

        words.sort(function (a, b) { return (a.y - b.y) || (a.x - b.x); });
        var lines = [], cur = null;
        for (var w = 0; w < words.length; w++) {
            var wd = words[w];
            if (cur && Math.abs(wd.y - cur.y) < Math.max(4, cur.h * 0.6)) {
                cur.words.push(wd);
                cur.x = Math.min(cur.x, wd.x); cur.r = Math.max(cur.r, wd.x + wd.w);
                cur.y = Math.min(cur.y, wd.y); cur.b = Math.max(cur.b, wd.b);
            } else {
                cur = { words: [wd], x: wd.x, r: wd.x + wd.w, y: wd.y, b: wd.b, h: wd.h };
                lines.push(cur);
            }
        }
        return lines.map(function (l) {
            return {
                t: l.words.map(function (x) { return x.t; }).join(' '),
                x: l.x, y: l.y, w: l.r - l.x, h: l.b - l.y
            };
        });
    }

    

    function ownTextRuns(el) {
        var out = [];
        try {
            var rg = document.createRange();
            for (var i = 0; i < el.childNodes.length; i++) {
                var cn = el.childNodes[i];
                if (cn.nodeType !== 3) continue;
                if (!cn.nodeValue || !cn.nodeValue.replace(/\s+/g, '')) continue;
                rg.selectNodeContents(cn);
                var rects = rg.getClientRects();
                if (!rects || !rects.length) continue;
                if (rects.length === 1) {
                    out.push({ t: normText(cn.nodeValue), x: rects[0].left, y: rects[0].top, w: rects[0].width, h: rects[0].height });
                } else {
                    var lines = textNodeLines(cn);
                    for (var L = 0; L < lines.length; L++) out.push(lines[L]);
                }
            }
        } catch (e) { }
        return out;
    }

    function hasBlockChild(el) {
        for (var i = 0; i < el.children.length; i++) {
            var ch = el.children[i];
            if (SKIP_TAGS[ch.tagName]) continue;
            var d = getComputedStyle(ch).display;
            if (d === 'none') continue;
            if (BLOCKISH.test(d)) return true;
            
            if (ch.tagName === 'IMG' || ch.tagName === 'SVG' || ch.tagName === 'svg' ||
                ch.tagName === 'CANVAS' || ch.tagName === 'VIDEO') return true;
        }
        return false;
    }

    

    function inkBox(el) {
        try {
            var rg = document.createRange();
            rg.selectNodeContents(el);
            var rs = rg.getClientRects();
            if (!rs || !rs.length) return null;
            var x = Infinity, y = Infinity, r = -Infinity, b = -Infinity;
            for (var i = 0; i < rs.length; i++) {
                if (rs[i].width <= 0 && rs[i].height <= 0) continue;
                x = Math.min(x, rs[i].left); y = Math.min(y, rs[i].top);
                r = Math.max(r, rs[i].right); b = Math.max(b, rs[i].bottom);
            }
            if (!isFinite(x)) return null;
            return { x: x, y: y, w: r - x, h: b - y };
        } catch (e) { return null; }
    }

    

    function textLines(el, limit) {
        var out = [];
        try {
            var walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, null, false);
            var node, rg = document.createRange();
            while ((node = walker.nextNode())) {
                var s = node.nodeValue;
                if (!s || !s.trim()) continue;
                var i = 0;
                while (i < s.length) {
                    while (i < s.length && /\s/.test(s[i])) i++;
                    var start = i;
                    while (i < s.length && !/\s/.test(s[i])) i++;
                    if (i <= start) break;
                    rg.setStart(node, start); rg.setEnd(node, i);
                    var r = rg.getBoundingClientRect();
                    if (r.width <= 0 && r.height <= 0) continue;
                    out.push({ t: s.slice(start, i), x: r.left, y: r.top, w: r.width, h: r.height, b: r.bottom });
                    if (out.length > 4000) { i = s.length; break; }
                }
            }
        } catch (e) { return []; }
        if (!out.length) return [];

        out.sort(function (a, b) { return (a.y - b.y) || (a.x - b.x); });
        var lines = [], cur = null;
        out.forEach(function (w) {
            
            if (cur && Math.abs(w.y - cur.y) < Math.max(4, cur.h * 0.6)) {
                cur.words.push(w);
                cur.x = Math.min(cur.x, w.x);
                cur.r = Math.max(cur.r, w.x + w.w);
                cur.y = Math.min(cur.y, w.y);
                cur.b = Math.max(cur.b, w.b);
            } else {
                cur = { words: [w], x: w.x, r: w.x + w.w, y: w.y, b: w.b, h: w.h };
                lines.push(cur);
            }
        });
        if (limit && lines.length > limit) lines = lines.slice(0, limit);
        return lines.map(function (l) {
            return {
                t: l.words.map(function (w) { return w.t; }).join(' '),
                x: round(l.x, 2), y: round(l.y, 2),
                w: round(l.r - l.x, 2), h: round(l.b - l.y, 2)
            };
        });
    }

    function fontOf(cs) {
        var fam = splitTop(cs.fontFamily)[0] || 'sans-serif';
        fam = fam.replace(/^['"]|['"]$/g, '').trim();
        var weight = parseInt(cs.fontWeight, 10);
        if (!isFinite(weight)) weight = cs.fontWeight === 'bold' ? 700 : 400;
        weight = Math.max(100, Math.min(900, Math.round(weight / 100) * 100));
        var size = num(cs.fontSize);
        var lh = cs.lineHeight === 'normal' ? size * 1.2 : num(cs.lineHeight);
        var ls = cs.letterSpacing === 'normal' ? 0 : num(cs.letterSpacing);
        var italic = /italic|oblique/i.test(cs.fontStyle);
        var style = WEIGHT_STYLE[weight] || 'Regular';
        if (italic) style = style === 'Regular' ? 'Italic' : style + ' Italic';
        var col = parseColor(cs.color) || { r: 0, g: 0, b: 0, a: 1 };
        return {
            family: fam,
            weight: weight,
            style: style,
            italic: italic,
            size: round(size, 2),
            lineHeight: round(lh, 2),
            
            tracking: round(size ? ls / size * 1000 : 0, 1),
            align: /right/.test(cs.textAlign) ? 'right' : /center/.test(cs.textAlign) ? 'center' : /justify/.test(cs.textAlign) ? 'justify' : 'left',
            color: hex(col),
            alpha: round(col.a, 3),
            transform: cs.textTransform,
            decoration: /underline/.test(cs.textDecorationLine || cs.textDecoration) ? 'underline' : 'none'
        };
    }

    












    var metricCtx = null;

    function ascentRatio(f) {
        try {
            if (!metricCtx) metricCtx = document.createElement('canvas').getContext('2d');
            metricCtx.font = (f.italic ? 'italic ' : '') + f.weight + ' ' + f.size + 'px "' + f.family + '", sans-serif';
            var m = metricCtx.measureText('Hxdgp');
            var a = m.fontBoundingBoxAscent, d = m.fontBoundingBoxDescent;
            if (!isFinite(a) || !isFinite(d) || a + d <= 0) return 0.8;
            return a / (a + d);
        } catch (e) { return 0.8; }
    }

    


    function alignX(el, cs, f, firstLine, inkB, dx) {
        var align = f.align;
        var bw = num(cs.borderLeftWidth), pl = num(cs.paddingLeft), pr = num(cs.paddingRight);
        var cw = el.clientWidth ? el.clientWidth - pl - pr : 0;
        var cx0 = (inkB ? inkB.x : firstLine.x) + dx;
        if (cw > 0) {
            var boxLeft = el.getBoundingClientRect().left + bw + pl + dx;
            if (align === 'center') return boxLeft + cw / 2;
            if (align === 'right') return boxLeft + cw;
            return cx0;
        }
        if (align === 'center') return cx0 + (inkB ? inkB.w : firstLine.w) / 2;
        if (align === 'right') return cx0 + (inkB ? inkB.w : firstLine.w);
        return cx0;
    }

    










    function clipWidth(el, cs) {
        var ov = String(cs.overflowX || '') + ' ' + String(cs.overflow || '');
        if (!/hidden|clip|scroll|auto/.test(ov)) return 0;
        var avail = el.clientWidth - num(cs.paddingLeft) - num(cs.paddingRight);
        if (!(avail > 0)) return 0;
        
        if (el.scrollWidth <= el.clientWidth + 1) return 0;
        return avail;
    }

    

    function visibleText(el, avail, ellipsis) {
        try {
            var walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, null, false);
            var node = walker.nextNode();
            if (!node || !node.nodeValue) return null;
            var full = node.nodeValue;
            if (!full.replace(/\s+/g, '')) return null;

            var rg = document.createRange();
            var lo = 0, hi = full.length, best = 0;
            while (lo <= hi) {
                var mid = (lo + hi) >> 1;
                rg.setStart(node, 0);
                rg.setEnd(node, mid);
                if (rg.getBoundingClientRect().width <= avail) { best = mid; lo = mid + 1; }
                else hi = mid - 1;
            }
            if (best >= full.length) return null;         
            var keep = Math.max(0, best - (ellipsis ? 1 : 0));
            var cut = full.slice(0, keep).replace(/\s+$/, '');
            if (!cut) return null;
            return cut + (ellipsis ? '…' : '');
        } catch (e) { return null; }
    }

    function applyTransform(s, mode) {
        if (mode === 'uppercase') return s.toUpperCase();
        if (mode === 'lowercase') return s.toLowerCase();
        if (mode === 'capitalize') return s.replace(/\b\w/g, function (c) { return c.toUpperCase(); });
        return s;
    }

    

    function nameOf(el, kind, text) {
        var tag = el.tagName.toLowerCase();
        var cls = '';
        if (el.classList && el.classList.length) {
            for (var i = 0; i < el.classList.length; i++) {
                var c = el.classList[i];
                

                if (c.length > 24 || /^(css-|sc-|jsx-|_)/.test(c) || /^[a-z-]+-\d+$/.test(c) || /[A-Za-z]{2}\d{4,}/.test(c)) continue;
                cls = c; break;
            }
        }
        var base = el.id && el.id.length < 24 ? '#' + el.id : (cls ? tag + '.' + cls : tag);
        if (kind === 'text' && text) {
            var t = text.split('\n')[0].slice(0, 26).trim();
            if (t) return t + '  ·  ' + tag;
        }
        return base;
    }

    

    function capture(options) {
        var o = options || {};
        var scrollX = window.scrollX || window.pageXOffset || 0;
        var scrollY = window.scrollY || window.pageYOffset || 0;
        var docW = Math.max(document.documentElement.scrollWidth, document.body ? document.body.scrollWidth : 0, window.innerWidth);
        var docH = Math.max(document.documentElement.scrollHeight, document.body ? document.body.scrollHeight : 0, window.innerHeight);

        var area = o.viewportOnly
            ? { x: 0, y: 0, w: window.innerWidth, h: window.innerHeight }
            : { x: -scrollX, y: -scrollY, w: docW, h: docH };

        var minSize = o.minSize == null ? 2 : o.minSize;
        var maxNodes = o.maxNodes == null ? 1200 : o.maxNodes;
        var splitLines = !!o.splitLines;
        var wantImages = o.images !== false;

        var nodes = [];
        var assets = {};          
        var assetSeq = 0;
        var fonts = {};
        var truncated = false;

        var rootEl = document.body || document.documentElement;
        var seq = 0;

        function push(n) {
            if (nodes.length >= maxNodes) { truncated = true; return null; }
            n.id = nodes.length + 1;
            n.seq = seq++;
            nodes.push(n);
            return n;
        }

        function assetFor(url, kind) {
            if (!url) return '';
            if (url.indexOf('data:') === 0) {
                var name = 'a' + (++assetSeq) + '.' + (/(png|gif|webp|svg\+xml|jpeg|jpg)/.exec(url) || [, 'png'])[1].replace('svg+xml', 'svg').replace('jpeg', 'jpg');
                assets[name] = { data: url, kind: kind || 'image' };
                return name;
            }
            for (var k in assets) if (assets[k].url === url) return k;
            var ext = (/\.(png|jpg|jpeg|gif|webp|svg|avif)(\?|#|$)/i.exec(url) || [, 'png'])[1].toLowerCase();
            if (ext === 'jpeg') ext = 'jpg';
            var fn = 'a' + (++assetSeq) + '.' + ext;
            assets[fn] = { url: url, kind: kind || 'image' };
            return fn;
        }

        


        function zKeyOf(cs, parentKey) {
            var z = cs.zIndex;
            var positioned = cs.position !== 'static';
            var own = (positioned && z !== 'auto') ? (parseInt(z, 10) || 0) : 0;
            if (own === 0 && !positioned) return parentKey;
            return parentKey.concat([own]);
        }

        function walk(el, depth, parentId, clip, alpha, zkey, fixed) {
            if (!el || el.nodeType !== 1) return;
            var tag = el.tagName;
            if (SKIP_TAGS[tag]) return;
            if (el.getAttribute && el.getAttribute('data-flex-ignore') != null) return;

            var cs;
            try { cs = getComputedStyle(el); } catch (e) { return; }
            if (!cs || cs.display === 'none' || cs.visibility === 'hidden' || cs.visibility === 'collapse') return;

            




            try {
                if (el.checkVisibility && !el.checkVisibility({
                    checkOpacity: true, checkVisibilityCSS: true, contentVisibilityAuto: true
                })) return;
            } catch (eV) { }

            var op = cs.opacity === '' ? 1 : num(cs.opacity);
            if (op <= 0.001) return;
            var a = alpha * op;

            var isFixed = fixed || cs.position === 'fixed';
            var box = rectOf(el);
            if (screenReaderOnly(el, cs, box.w, box.h)) return;
            

            var dx = isFixed ? scrollX : 0, dy = isFixed ? scrollY : 0;

            var visible = { x: box.x + dx, y: box.y + dy, w: box.w, h: box.h };
            var hasSize = box.w >= 0.5 && box.h >= 0.5;

            


            var clipped = 0;
            if (hasSize && clip) {
                var frac = visibleFraction(visible, clip);
                if (frac < 0.4) {
                    

                    var ib = isTextLeaf(el) ? inkBox(el) : null;
                    if (!ib) return;
                    ib = { x: ib.x + dx, y: ib.y + dy, w: ib.w, h: ib.h };
                    if (visibleFraction(ib, clip) < 0.6) return;
                }
                clipped = frac < 0.95 ? 1 : 0;
            }
            if (hasSize && box.w > 0 && box.h > 0) {
                



                if (visibleFraction(visible, area) < 0.4) return;
            }

            var zk = zKeyOf(cs, zkey);
            var myClip = clip;
            var ov = cs.overflow + ' ' + cs.overflowX + ' ' + cs.overflowY;
            if (/hidden|clip|scroll|auto/.test(ov) && hasSize) {
                myClip = clip ? clipRect(clip, visible) : visible;
            }

            var tf = decompose(cs);
            

            var lw = tf ? (el.offsetWidth || box.w) : box.w;
            var lh = tf ? (el.offsetHeight || box.h) : box.h;
            var cx = visible.x + box.w / 2, cy = visible.y + box.h / 2;

            var base = {
                parent: parentId, depth: depth, tag: tag.toLowerCase(),
                x: round(cx - lw / 2, 2), y: round(cy - lh / 2, 2),
                w: round(lw, 2), h: round(lh, 2),
                opacity: round(a * 100, 1),
                z: zk.join('.'),
                fixed: isFixed || undefined,
                rotate: tf ? tf.rotate : undefined,
                sx: tf && tf.sx !== 1 ? tf.sx : undefined,
                sy: tf && tf.sy !== 1 ? tf.sy : undefined,
                
                clip: clipped ? {
                    x: round(clip.x, 2), y: round(clip.y, 2),
                    w: round(clip.w, 2), h: round(clip.h, 2)
                } : undefined
            };

            var myId = parentId;
            var rad = radii(cs, lw, lh);
            var hasRadius = rad[0] || rad[1] || rad[2] || rad[3];

            




            if (hasSize && lw >= 1 && lh >= 1 && Math.max(lw, lh) >= minSize) {
                var fill = parseColor(cs.backgroundColor);
                var grad = gradient(cs, lw, lh);
                var bord = border(cs);
                var shad = shadow(cs);
                var bgUrl = bgImageUrl(cs);

                if (fill || grad || bord || (shad && !shad.inset)) {
                    var n = push(Object.assign({}, base, {
                        kind: 'shape',
                        name: nameOf(el, 'shape'),
                        fill: fill ? hex(fill) : '',
                        fillAlpha: fill ? round(fill.a, 3) : 0,
                        gradient: grad || undefined,
                        stroke: bord || undefined,
                        shadow: shad && !shad.inset ? shad : undefined,
                        radius: hasRadius ? rad : undefined
                    }));
                    if (n) myId = n.id;
                }

                if (bgUrl && wantImages) {
                    var bn = push(Object.assign({}, base, {
                        kind: 'image',
                        name: nameOf(el, 'image'),
                        asset: assetFor(bgUrl, 'image'),
                        fit: cs.backgroundSize || 'auto',
                        radius: hasRadius ? rad : undefined
                    }));
                    if (bn && myId === parentId) myId = bn.id;
                }
            }

            
            if (tag === 'IMG' && hasSize) {
                if (wantImages) {
                    var src = el.currentSrc || el.src || '';
                    if (src) {
                        push(Object.assign({}, base, {
                            kind: /\.svg(\?|#|$)/i.test(src) ? 'svg' : 'image',
                            name: nameOf(el, 'image') + (el.alt ? '  ·  ' + el.alt.slice(0, 20) : ''),
                            asset: assetFor(src, 'image'),
                            fit: cs.objectFit || 'fill',
                            natural: [el.naturalWidth || 0, el.naturalHeight || 0],
                            radius: hasRadius ? rad : undefined
                        }));
                    }
                }
                return;
            }

            if (tag === 'svg' || tag === 'SVG') {
                if (wantImages && hasSize) {
                    var markup = serializeSvg(el, lw, lh);
                    if (markup) {
                        push(Object.assign({}, base, {
                            kind: 'svg',
                            name: nameOf(el, 'svg'),
                            asset: assetFor('data:image/svg+xml;base64,' + b64(markup), 'svg')
                        }));
                    }
                }
                return;
            }

            if (tag === 'CANVAS' && hasSize) {
                if (wantImages) {
                    var du = '';
                    try { du = el.toDataURL('image/png'); } catch (e) { du = ''; }
                    if (du) {
                        push(Object.assign({}, base, {
                            kind: 'image', name: nameOf(el, 'image'),
                            asset: assetFor(du, 'image'), radius: hasRadius ? rad : undefined
                        }));
                    }
                }
                return;
            }

            if (tag === 'VIDEO' && hasSize) {
                if (wantImages) {
                    var frame = videoFrame(el);
                    if (frame) {
                        push(Object.assign({}, base, {
                            kind: 'image', name: nameOf(el, 'video'),
                            asset: assetFor(frame, 'image'), radius: hasRadius ? rad : undefined
                        }));
                    }
                }
                return;
            }

            
            if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') {
                var val = tag === 'SELECT'
                    ? (el.options && el.options[el.selectedIndex] ? el.options[el.selectedIndex].text : '')
                    : (el.value || el.getAttribute('placeholder') || '');
                val = normText(val);
                if (val && hasSize) {
                    var fcs = fontOf(cs);
                    noteFont(fcs);
                    var padL = num(cs.paddingLeft) + num(cs.borderLeftWidth);
                    var ir = ascentRatio(fcs);
                    var contentH = fcs.size * 1.16;
                    push(Object.assign({}, base, {
                        kind: 'text',
                        name: nameOf(el, 'text', val),
                        text: applyTransform(val, cs.textTransform),
                        font: fcs,
                        parent: myId,
                        tx: round(visible.x + padL, 2),
                        ty: round(cy - contentH / 2, 2),
                        tw: round(lw - padL - num(cs.paddingRight), 2),
                        th: round(contentH, 2),
                        bx: round(fcs.align === 'center' ? cx : fcs.align === 'right'
                            ? visible.x + lw - num(cs.paddingRight) : visible.x + padL, 2),
                        

                        by: round(cy + contentH * (ir - 0.5), 2),
                        lines: 1
                    }));
                }
                return;
            }

            
            


            if (isTextLeaf(el) && !uniformType(el, cs)) {
                var mf = fontOf(cs);
                var mixedRuns = ownTextRuns(el);
                if (mixedRuns.length) {
                    noteFont(mf);
                    var mr = ascentRatio(mf);
                    for (var mi = 0; mi < mixedRuns.length; mi++) {
                        var R = mixedRuns[mi];
                        push(Object.assign({}, base, {
                            kind: 'text',
                            name: nameOf(el, 'text', R.t),
                            text: applyTransform(R.t, cs.textTransform),
                            font: mf, parent: myId,
                            tx: round(R.x + dx, 2), ty: round(R.y + dy, 2),
                            tw: round(R.w, 2), th: round(R.h, 2),
                            bx: round(mf.align === 'center' ? R.x + dx + R.w / 2
                                : mf.align === 'right' ? R.x + dx + R.w : R.x + dx, 2),
                            by: round(R.y + dy + R.h * mr, 2),
                            lines: 1
                        }));
                    }
                }
                
            }
            else if (isTextLeaf(el)) {
                var raw = normText(el.innerText != null ? el.innerText : el.textContent);
                if (raw) {
                    var f = fontOf(cs);
                    noteFont(f);
                    var ink = inkBox(el);
                    var ls = textLines(el, 80);
                    var lineCount = Math.max(1, ls.length);

                    var ratio = ascentRatio(f);
                    var first = ls[0] || (ink ? { x: ink.x, y: ink.y, w: ink.w, h: ink.h } : { x: box.x, y: box.y, w: box.w, h: box.h });

                    

                    var fullText = null, maxw = 0;
                    var avail = clipWidth(el, cs);
                    if (avail && lineCount === 1) {
                        var shown = visibleText(el, avail, /ellipsis/.test(cs.textOverflow || ''));
                        if (shown && shown !== raw) {
                            fullText = raw;
                            raw = shown;
                            maxw = avail;
                            if (ink && ink.w > avail) ink = { x: ink.x, y: ink.y, w: avail, h: ink.h };
                            first = { x: first.x, y: first.y, w: Math.min(first.w, avail), h: first.h };
                        }
                    }

                    if (splitLines && lineCount > 1) {
                        ls.forEach(function (L, i) {
                            push(Object.assign({}, base, {
                                kind: 'text',
                                name: nameOf(el, 'text', L.t) + (' [' + (i + 1) + ']'),
                                text: applyTransform(L.t, cs.textTransform),
                                font: f, parent: myId,
                                tx: round(L.x + dx, 2), ty: round(L.y + dy, 2),
                                tw: round(L.w, 2), th: round(L.h, 2),
                                bx: round(alignX(el, cs, f, L, { x: L.x, y: L.y, w: L.w, h: L.h }, dx), 2),
                                by: round(L.y + dy + L.h * ratio, 2),
                                lines: 1
                            }));
                        });
                    } else {
                        var tb = ink || { x: box.x, y: box.y, w: box.w, h: box.h };
                        push(Object.assign({}, base, {
                            kind: 'text',
                            name: nameOf(el, 'text', raw),
                            


                            text: applyTransform(lineCount > 1 ? ls.map(function (L) { return L.t; }).join('\n') : raw, cs.textTransform),
                            font: f, parent: myId,
                            tx: round(tb.x + dx, 2), ty: round(tb.y + dy, 2),
                            tw: round(maxw ? Math.min(tb.w, maxw) : tb.w, 2), th: round(tb.h, 2),
                            bx: round(alignX(el, cs, f, first, tb, dx), 2),
                            by: round(first.y + dy + first.h * ratio, 2),
                            

                            maxw: maxw ? round(maxw, 2) : undefined,
                            fullText: fullText || undefined,
                            
                            boxw: round(el.clientWidth - num(cs.paddingLeft) - num(cs.paddingRight), 2),
                            lines: lineCount,
                            lineBoxes: lineCount > 1 ? ls.map(function (L) {
                                return { t: L.t, x: round(L.x + dx, 2), y: round(L.y + dy, 2), w: L.w, h: L.h };
                            }) : undefined
                        }));
                    }
                }
                return;
            }

            
            var kids = el.children;
            for (var i = 0; i < kids.length; i++) {
                walk(kids[i], depth + 1, myId, myClip, a, zk, isFixed);
                if (nodes.length >= maxNodes) { truncated = true; break; }
            }
        }

        function noteFont(f) {
            var key = f.family + '|' + f.weight + '|' + (f.italic ? 'i' : 'n');
            if (!fonts[key]) fonts[key] = { family: f.family, weight: f.weight, italic: f.italic, style: f.style, count: 0 };
            fonts[key].count++;
        }

        walk(rootEl, 0, 0, null, 1, [], false);

        
        nodes.sort(function (p, q) {
            var A = p.z ? p.z.split('.').map(Number) : [];
            var B = q.z ? q.z.split('.').map(Number) : [];
            for (var i = 0; i < Math.max(A.length, B.length); i++) {
                var x = A[i] || 0, y = B[i] || 0;
                if (x !== y) return x - y;
            }
            return p.seq - q.seq;
        });
        nodes.forEach(function (n, i) { n.order = i; delete n.seq; });

        var pageBg = parseColor(getComputedStyle(document.body || document.documentElement).backgroundColor) ||
            parseColor(getComputedStyle(document.documentElement).backgroundColor) ||
            { r: 255, g: 255, b: 255, a: 1 };

        return {
            v: VERSION,
            url: location.href,
            title: document.title || location.hostname,
            host: location.hostname,
            captured: Date.now(),
            page: {
                width: Math.round(o.viewportOnly ? window.innerWidth : docW),
                height: Math.round(o.viewportOnly ? window.innerHeight : docH),
                dpr: window.devicePixelRatio || 1,
                bg: hex(pageBg)
            },
            origin: { x: Math.round(area.x), y: Math.round(area.y) },
            fonts: Object.keys(fonts).map(function (k) { return fonts[k]; })
                .sort(function (a, b) { return b.count - a.count; }),
            nodes: nodes,
            assets: assets,
            truncated: truncated,
            counts: nodes.reduce(function (m, n) { m[n.kind] = (m[n.kind] || 0) + 1; return m; }, {})
        };
    }

    

    function b64(s) {
        try { return btoa(unescape(encodeURIComponent(s))); }
        catch (e) { return btoa(s.replace(/[^\x00-\x7F]/g, '?')); }
    }

    

    function serializeSvg(el, w, h) {
        try {
            var clone = el.cloneNode(true);
            clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
            if (!clone.getAttribute('viewBox')) {
                var vb = el.viewBox && el.viewBox.baseVal;
                if (vb && vb.width) clone.setAttribute('viewBox', vb.x + ' ' + vb.y + ' ' + vb.width + ' ' + vb.height);
                else clone.setAttribute('viewBox', '0 0 ' + Math.max(1, Math.round(w)) + ' ' + Math.max(1, Math.round(h)));
            }
            clone.setAttribute('width', Math.max(1, Math.round(w)));
            clone.setAttribute('height', Math.max(1, Math.round(h)));

            
            var srcNodes = el.querySelectorAll('*'), dstNodes = clone.querySelectorAll('*');
            var rootColor = getComputedStyle(el).color;
            for (var i = 0; i < srcNodes.length && i < dstNodes.length; i++) {
                var scs = getComputedStyle(srcNodes[i]);
                var f = scs.fill, st = scs.stroke;
                if (f && f !== 'none') dstNodes[i].setAttribute('fill', f);
                if (st && st !== 'none') dstNodes[i].setAttribute('stroke', st);
                

                if (scs.strokeWidth) dstNodes[i].setAttribute('stroke-width', num(scs.strokeWidth));
                if (scs.opacity && scs.opacity !== '1') dstNodes[i].setAttribute('opacity', scs.opacity);
                dstNodes[i].removeAttribute('class');
            }
            if (rootColor) clone.setAttribute('color', rootColor);
            clone.removeAttribute('class');
            return new XMLSerializer().serializeToString(clone);
        } catch (e) { return ''; }
    }

    function videoFrame(el) {
        try {
            if (el.readyState >= 2 && el.videoWidth) {
                var c = document.createElement('canvas');
                c.width = el.videoWidth; c.height = el.videoHeight;
                c.getContext('2d').drawImage(el, 0, 0);
                return c.toDataURL('image/png');
            }
        } catch (e) { }
        return el.getAttribute('poster') || '';
    }

    

    

    function prepare(o, done) {
        o = o || {};
        if (o.viewportOnly || o.noScroll) { done(); return; }
        var startY = window.scrollY;
        var step = Math.round(window.innerHeight * 0.8);
        var docH = Math.max(document.documentElement.scrollHeight, document.body ? document.body.scrollHeight : 0);
        var y = 0;
        var guard = 0;

        function next() {
            if (y >= docH || ++guard > 60) {
                window.scrollTo(0, startY);
                
                setTimeout(done, 350);
                return;
            }
            window.scrollTo(0, y);
            y += step;
            setTimeout(next, 90);
        }
        next();
    }

    root.FlexWebCapture = {
        version: VERSION,
        capture: capture,
        prepare: prepare,
        parseColor: parseColor,
        _internals: { gradient: gradient, radii: radii, textLines: textLines, fontOf: fontOf, decompose: decompose }
    };
}(typeof window !== 'undefined' ? window : this));
