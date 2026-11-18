




(function() {
    'use strict';

    var State = PreviewEngine.State;
    var Utils = PreviewEngine.Utils;
    var M = PreviewEngine.FormulaMath;
    var F = PreviewEngine.Formulas;
    var CS = M.CS;

    
    
    

    F['sine wave'] = {
        category: 'effects',
        run: function(time, p) {
            var freq = p.freq || 2;
            var amp = p.amp || 30;

            var elapsed = (time - State.startTime) / 1000;
            var wave = Math.sin(elapsed * freq * M.PI2);

            var t = M.getTargets(p);

            if (!t || t.pos) {
                State.text.x = wave * amp * CS;
            }
            if (t && t.rot) {
                State.text.rotation = wave * amp;
            }
            if (t && t.opacity) {
                var oAmp = amp > 1 ? amp / 100 : amp;
                State.text.opacity = Math.max(0, Math.min(1, 1 + wave * oAmp));
            }
            if (t && t.scale) {
                var sAmp = amp;
                if (sAmp > 1) sAmp = sAmp / 100;
                State.text.scale = 1 + wave * sAmp;
            }
        }
    };

    
    
    

    F['square wave'] = {
        category: 'effects',
        run: function(time, p) {
            var freq = p.freq || 2;
            var amp = p.amp || 30;
            var duty = p.duty || 0.5;

            var elapsed = (time - State.startTime) / 1000;
            var phase = (elapsed * freq) % 1;
            var wave = phase < duty ? 1 : -1;

            var t = M.getTargets(p);

            if (!t || t.pos) {
                State.text.x = wave * amp * CS;
            }
            if (t && t.rot) {
                State.text.rotation = wave * amp;
            }
            if (t && t.opacity) {
                var oAmp = amp > 1 ? amp / 100 : amp;
                State.text.opacity = Math.max(0, Math.min(1, 1 + wave * oAmp));
            }
            if (t && t.scale) {
                var sAmp = amp;
                if (sAmp > 1) sAmp = sAmp / 100;
                State.text.scale = 1 + wave * sAmp;
            }
        }
    };

    
    
    

    F['float / hover'] = {
        category: 'effects',
        run: function(time, p) {
            var freq = p.freq || 0.5;
            var amp = p.amp || 15;

            var elapsed = (time - State.startTime) / 1000;

            
            var y = Math.sin(elapsed * freq * M.PI2) * amp;

            State.text.y = y * CS;
        }
    };

    
    
    

    F['pendulum'] = {
        category: 'effects',
        run: function(time, p) {
            var freq = p.freq || 1;
            var amp = p.amp || 30;
            var decay = (p.decay != null) ? p.decay : 0.5;

            var elapsed = (time - State.startTime) / 1000;

            if (decay > 0) {
                
                var animDur = Math.min(8, 4.6 / Math.max(decay, 0.1));
                var holdDur = 1;
                var cycleDuration = animDur + holdDur;
                var cycleTime = elapsed % cycleDuration;

                if (cycleTime < animDur) {
                    var swing = Math.sin(cycleTime * freq * M.PI2);
                    var envelope = Math.exp(-decay * cycleTime);
                    State.text.rotation = amp * swing * envelope;
                }
                
            } else {
                
                State.text.rotation = amp * Math.sin(elapsed * freq * M.PI2);
            }
        }
    };

    
    
    

    F['throb'] = {
        category: 'effects',
        run: function(time, p) {
            var freq = p.freq || 1;
            var amp = p.amp || 15;

            var elapsed = (time - State.startTime) / 1000;
            var phase = (elapsed * freq) % 1;

            
            var pulse = Math.pow(Math.max(0, 1 - phase * 3), 0.5);

            
            var sAmp = amp;
            if (sAmp > 1) sAmp = sAmp / 100;
            State.text.scale = 1 + pulse * sAmp;

            
            State.text.opacity = 1 - pulse * sAmp * 2;
        }
    };

    
    
    

    F['sine drift'] = {
        category: 'effects',
        run: function(time, p) {
            var speed = p.freq || 0.5;
            var amp = p.amp || 30;

            var elapsed = (time - State.startTime) / 1000;

            
            var x = Math.sin(elapsed * speed * 1.7) * amp * 0.5
                  + Math.sin(elapsed * speed * 3.1) * amp * 0.3
                  + Math.sin(elapsed * speed * 5.3) * amp * 0.2;
            var y = Math.sin(elapsed * speed * 2.3 + 1.5) * amp * 0.5
                  + Math.sin(elapsed * speed * 4.1 + 0.7) * amp * 0.3
                  + Math.sin(elapsed * speed * 6.7 + 2.1) * amp * 0.2;

            State.text.x = x * CS;
            State.text.y = y * CS;
        }
    };

    
    
    

    F['triangle wave'] = {
        category: 'effects',
        run: function(time, p) {
            var freq = p.freq || 1;
            var amp = p.amp || 50;

            var elapsed = (time - State.startTime) / 1000;

            
            var phase = (elapsed * freq) % 1;
            var triangle = Math.abs(phase * 2 - 1) * 2 - 1; 

            var t = M.getTargets(p);

            if (!t || t.rot) {
                State.text.rotation = triangle * amp;
            }
            if (t && t.pos) {
                State.text.x = triangle * amp * CS;
            }
            if (t && t.scale) {
                var sAmp = amp;
                if (sAmp > 1) sAmp = sAmp / 100;
                State.text.scale = 1 + triangle * sAmp;
            }
        }
    };

    
    
    

    F['sawtooth wave'] = {
        category: 'effects',
        run: function(time, p) {
            var freq = p.freq || 1;
            var amp = p.amp || 100;

            var elapsed = (time - State.startTime) / 1000;

            
            var saw = (elapsed * freq) % 1;

            var t = M.getTargets(p);

            if (!t || t.rot) {
                State.text.rotation = saw * amp;
            }
            if (t && t.pos) {
                State.text.x = (saw * 2 - 1) * amp * 0.5 * CS;
            }
            if (t && t.scale) {
                var sAmp = amp;
                if (sAmp > 1) sAmp = sAmp / 100;
                State.text.scale = 1 + saw * sAmp;
            }
        }
    };

    
    
    

    F['fade in'] = {
        category: 'effects',
        run: function(time, p) {
            var duration = p.duration || p.dur || 0.5;
            var elapsed = (time - State.startTime) / 1000;
            var hold = 2;
            var cycle = duration + hold;
            var cycleTime = elapsed % cycle;

            if (cycleTime < duration) {
                var t = cycleTime / duration;
                State.text.opacity = t * t * (3 - 2 * t);
            } else {
                State.text.opacity = 1;
            }
        }
    };



    
    
    

    F['auto fade'] = {
        category: 'effects',
        run: function(time, p) {
            var fi = p.fadeIn || p.duration || p.dur || 0.5;
            var fo = p.fadeOut || p.duration || p.dur || 0.5;
            var hold = 1;
            var total = fi + hold + fo + 0.8;
            var elapsed = ((time - State.startTime) / 1000) % total;

            if (elapsed < fi) {
                var t = elapsed / fi;
                State.text.opacity = t * t * (3 - 2 * t);
            } else if (elapsed < fi + hold) {
                State.text.opacity = 1;
            } else if (elapsed < fi + hold + fo) {
                var t = (elapsed - fi - hold) / fo;
                State.text.opacity = 1 - t * t * (3 - 2 * t);
            } else {
                State.text.opacity = 0;
            }
        }
    };

    
    
    

    F['flicker'] = {
        category: 'effects',
        run: function(time, p) {
            var speed = p.speed || p.freq || 15;
            var minOp = p.minOp || p.minOpacity || 50;
            var maxOp = p.maxOp || p.maxOpacity || 100;

            
            if (minOp > 1) minOp = minOp / 100;
            if (maxOp > 1) maxOp = maxOp / 100;

            var elapsed = (time - State.startTime) / 1000;
            var segment = Math.floor(elapsed * speed);

            
            var flicker = M.segRange(minOp, maxOp, segment, 0);

            
            State.text.opacity = flicker;
        }
    };

    
    

    F['flash'] = {
        category: 'effects',
        run: function(time, p) {
            var freq = p.freq || 1;
            var intensity = p.amp || 100;
            if (intensity > 1) intensity = intensity / 100;

            var elapsed = (time - State.startTime) / 1000;
            var period = 1 / freq;
            var phase = (elapsed % period) / period;

            
            var flash = Math.pow(Math.max(0, 1 - phase * 5), 3);
            var minOp = 1 - intensity;

            State.text.opacity = minOp + flash * intensity;
        }
    };

    
    
    

    F['strobe'] = {
        category: 'effects',
        run: function(time, p) {
            var freq = p.freq || 15;

            var elapsed = (time - State.startTime) / 1000;

            
            var on = Math.floor(elapsed * freq) % 2 === 0;

            State.text.opacity = on ? 1 : 0;
        }
    };

    
    
    

    F['pulse opacity'] = {
        category: 'effects',
        run: function(time, p) {
            var freq = p.freq || p.speed || 1;
            var minOp = p.minOp || p.minOpacity || 60;
            var maxOp = p.maxOp || p.maxOpacity || 100;

            if (minOp > 1) minOp = minOp / 100;
            if (maxOp > 1) maxOp = maxOp / 100;

            var elapsed = (time - State.startTime) / 1000;
            var pulse = (Math.sin(elapsed * freq * M.PI2) + 1) / 2;

            State.text.opacity = minOp + pulse * (maxOp - minOp);
        }
    };

    
    
    

    F['rainbow cycle'] = {
        category: 'effects',
        run: function(time, p) {
            var speed = p.speed || p.freq || 1;
            var offset = p.offset || 0;

            var elapsed = (time - State.startTime) / 1000;

            
            State.text.hue = (((elapsed * speed + offset) * 360) % 360 + 360) % 360;
        }
    };

    
    
    

    F['color pulse'] = {
        category: 'effects',
        run: function(time, p) {
            var freq = p.freq || 1;
            var hue1 = p.hue1 !== undefined ? p.hue1 : 0;
            var hue2 = p.hue2 !== undefined ? p.hue2 : 0.66;

            var elapsed = (time - State.startTime) / 1000;
            var t = (Math.sin(elapsed * freq * M.PI2) + 1) / 2;

            
            var h = hue1 + (hue2 - hue1) * t;
            State.text.hue = ((h % 1) + 1) % 1 * 360;
        }
    };

    
    
    

    F['random color'] = {
        category: 'effects',
        run: function(time, p) {
            var seed = p.seed || 0;

            
            var elapsed = (time - State.startTime) / 1000;
            var segment = Math.floor(elapsed * 1.4);
            var h = ((segment * 0.618 + seed * 0.01) % 1);

            State.text.hue = h * 360;
        }
    };

    
    
    

    F['hue shift by index'] = {
        category: 'effects',
        run: function(time, p) {
            var hueStep = p.hueStep || 0.1;
            var baseHue = p.baseHue || 0;

            var elapsed = (time - State.startTime) / 1000;

            
            State.text.hue = ((elapsed * hueStep + baseHue) * 360) % 360;
        }
    };

    
    
    

    F['saturation pulse'] = {
        category: 'effects',
        run: function(time, p) {
            var hue = p.hue !== undefined ? p.hue : 0.6;
            var freq = p.freq || 1;

            var elapsed = (time - State.startTime) / 1000;

            
            var sat = 0.5 + Math.sin(elapsed * freq * M.PI2) * 0.4;

            
            State.text.hue = hue * 360;
            State.text.saturation = sat * 100;
        }
    };

    
    
    

    F['heat shimmer'] = {
        category: 'effects',
        run: function(time, p) {
            var intensity = p.intensity || p.amp || 8;
            var speed = p.speed || p.freq || 2;

            var elapsed = (time - State.startTime) / 1000;

            
            var shimmer = Math.sin(elapsed * speed * 10) * intensity;

            State.text.x = shimmer * CS;
        }
    };

    
    
    

    F['light flicker'] = {
        category: 'effects',
        run: function(time, p) {
            var minOpacity = p.minOpacity || 70;
            var speed = p.speed || p.freq || 10;

            if (minOpacity > 1) minOpacity = minOpacity / 100;

            var elapsed = (time - State.startTime) / 1000;

            
            
            var freq1 = speed * 0.3;
            var interval1 = 1 / freq1;
            var seg1 = Math.floor(elapsed / interval1);
            var frac1 = (elapsed % interval1) / interval1;
            var smooth1 = (1 - Math.cos(frac1 * Math.PI)) / 2;
            var r1a = M.segRange(-1, 1, seg1, 0);
            var r1b = M.segRange(-1, 1, seg1 + 1, 0);
            var base = r1a + (r1b - r1a) * smooth1;

            
            var freq2 = speed * 0.7;
            var interval2 = 1 / freq2;
            var seg2 = Math.floor(elapsed / interval2);
            var frac2 = (elapsed % interval2) / interval2;
            var smooth2 = (1 - Math.cos(frac2 * Math.PI)) / 2;
            var r2a = M.segRange(-1, 1, seg2 + 200, 0);
            var r2b = M.segRange(-1, 1, seg2 + 201, 0);
            var mid = r2a + (r2b - r2a) * smooth2;

            
            var freq3 = speed * 1.5;
            var seg3 = Math.floor(elapsed * freq3);
            var jitter = M.segRange(-1, 1, seg3 + 500, 0);

            
            var flicker = 0.7 + base * 0.2 + mid * 0.15 + jitter * 0.1;

            
            var dipChance = M.segRandom(seg3 * 3.7, 0);
            if (dipChance > 0.9) flicker -= 0.25;

            State.text.opacity = Math.max(minOpacity, Math.min(1, flicker));
        }
    };

    
    
    

    F['depth fade'] = {
        category: 'effects',
        run: function(time, p) {
            var str = p.amp || 50;
            var freq = p.freq || 0.4;

            if (str > 1) str = str / 100;

            var elapsed = (time - State.startTime) / 1000;

            
            var d = 0.5; 
            var w = Math.sin(elapsed * freq * M.PI2) * 0.3;
            var v = 1 - d * str + w * str * 0.5;

            if (v < 0.1) v = 0.1;
            if (v > 1) v = 1;

            State.text.opacity = v;
            State.text.scale = v;
        }
    };

    
    
    

    F['electrify'] = {
        category: 'effects',
        run: function(time, p) {
            var intensity = p.amp || 5;
            var rate = p.freq || 30;

            var elapsed = (time - State.startTime) / 1000;
            var seg = Math.floor(elapsed * rate);

            
            var rx = M.segRandom(seg * 1.23, 0) * 2 - 1;
            var ry = M.segRandom(seg * 4.56, 0) * 2 - 1;
            var bx = rx * intensity;
            var by = ry * intensity * 0.5;

            
            var spike = M.segRandom(seg * 7.89, 0);
            if (spike > 0.85) {
                bx *= 3;
                by *= 3;
            }

            State.text.x = bx * CS;
            State.text.y = by * CS;
        }
    };

    
    
    

    F['parallax shift'] = {
        category: 'effects',
        run: function(time, p) {
            var depthMultiplier = p.depthMultiplier || p.depth || 0.5;
            var baseMovement = p.baseMovement || p.amp || 100;

            var elapsed = (time - State.startTime) / 1000;

            
            var parallax = Math.sin(elapsed * 0.5) * baseMovement * depthMultiplier;

            State.text.x = parallax * CS;
        }
    };

})();
