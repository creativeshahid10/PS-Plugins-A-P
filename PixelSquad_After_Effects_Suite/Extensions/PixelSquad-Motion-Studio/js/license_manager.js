/**
 * PixelSquad License & Student Whitelist Manager
 * Author: Mohammed Shahid <hello@pixelsquad.in>
 * Copyright (C) 2026 PixelSquad. All Rights Reserved.
 */

(function() {
    'use strict';

    var LM = {
        STORAGE_KEY: "pixelsquad_license_cache_v1",
        TRIAL_KEY: "pixelsquad_trial_start_v1",

        getMachineId: function() {
            var mid = localStorage.getItem("pixelsquad_machine_id");
            if (!mid) {
                var nav = window.navigator || {};
                var scr = window.screen || {};
                var raw = [
                    nav.userAgent,
                    nav.platform,
                    scr.width + "x" + scr.height,
                    scr.colorDepth,
                    Math.random().toString(36).substring(2, 10)
                ].join("###");
                
                mid = "PS-" + Math.abs(this.hashCode(raw)).toString(16).toUpperCase() + "-" + Date.now().toString(36).toUpperCase();
                localStorage.setItem("pixelsquad_machine_id", mid);
            }
            return mid;
        },

        hashCode: function(str) {
            var hash = 0;
            for (var i = 0; i < str.length; i++) {
                var char = str.charCodeAt(i);
                hash = ((hash << 5) - hash) + char;
                hash |= 0;
            }
            return hash;
        },

        init: function() {
            this.createModalUI();
            this.checkStatus();
            this.startHeartbeat();
        },

        createModalUI: function() {
            if (document.getElementById("ps-license-modal")) return;

            var modal = document.createElement("div");
            modal.id = "ps-license-modal";
            modal.style.cssText = "position:fixed;inset:0;background:rgba(8,11,18,0.96);z-index:999999;display:none;align-items:center;justify-content:center;padding:16px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;";

            modal.innerHTML = [
                '<div style="background:#131b2e;border:1px solid #1e293b;border-radius:12px;max-width:330px;width:100%;padding:20px;box-shadow:0 20px 40px rgba(0,0,0,0.8);color:#f1f5f9;text-align:center;">',
                '  <div style="font-size:24px;margin-bottom:6px;">⚡</div>',
                '  <h2 style="font-size:15px;font-weight:800;color:#38bdf8;margin:0 0 4px 0;">PIXELSQUAD SUITE</h2>',
                '  <div style="font-size:10px;color:#94a3b8;margin-bottom:12px;">Author: Mohammed Shahid • 2026 Edition</div>',
                '  <div id="ps-modal-banner" style="background:#1e293b;border-left:3px solid #38bdf8;padding:8px 10px;font-size:11px;border-radius:4px;margin-bottom:12px;text-align:left;color:#cbd5e1;">Activate with License Key or Student Email.</div>',
                
                '  <div style="text-align:left;font-size:10.5px;color:#94a3b8;margin-bottom:4px;font-weight:600;">License Key (For Buyers):</div>',
                '  <input id="ps-key-input" type="text" placeholder="PS-XXXX-XXXX-XXXX" style="width:100%;box-sizing:border-box;background:#090d16;border:1px solid #334155;color:#fff;padding:8px 10px;border-radius:6px;font-size:11.5px;margin-bottom:8px;outline:none;" />',
                
                '  <div style="text-align:left;font-size:10.5px;color:#94a3b8;margin-bottom:4px;font-weight:600;">Registered Email (Buyers & Students):</div>',
                '  <input id="ps-email-input" type="email" placeholder="name@domain.com" style="width:100%;box-sizing:border-box;background:#090d16;border:1px solid #334155;color:#fff;padding:8px 10px;border-radius:6px;font-size:11.5px;margin-bottom:12px;outline:none;" />',
                
                '  <button id="ps-btn-activate" style="width:100%;background:linear-gradient(135deg,#0284c7,#2563eb);color:#fff;border:none;padding:9px;border-radius:6px;font-weight:700;font-size:11.5px;cursor:pointer;margin-bottom:6px;">Activate License Key</button>',
                '  <button id="ps-btn-student" style="width:100%;background:#065f46;color:#a7f3d0;border:1px solid #059669;padding:8px;border-radius:6px;font-weight:700;font-size:11px;cursor:pointer;margin-bottom:8px;">🎓 Student Instant Login (Free Access)</button>',
                '  <button id="ps-btn-trial" style="width:100%;background:#1e293b;color:#94a3b8;border:1px solid #334155;padding:7px;border-radius:6px;font-weight:600;font-size:10.5px;cursor:pointer;">Continue with 1-Hr Free Trial</button>',
                '  <div style="margin-top:12px;font-size:10px;color:#64748b;">Official Support: <a href="mailto:hello@pixelsquad.in" style="color:#38bdf8;text-decoration:none;">hello@pixelsquad.in</a></div>',
                '</div>'
            ].join("");

            document.body.appendChild(modal);

            var self = this;
            // Activate with Key
            document.getElementById("ps-btn-activate").onclick = function() {
                var key = document.getElementById("ps-key-input").value.trim();
                var email = document.getElementById("ps-email-input").value.trim();
                if (!key) {
                    alert("Please enter your License Key.");
                    return;
                }
                self.activate(key, email, false);
            };

            // Student Instant Activation
            document.getElementById("ps-btn-student").onclick = function() {
                var email = document.getElementById("ps-email-input").value.trim();
                if (!email) {
                    alert("Please enter your PixelSquad registered student email address.");
                    return;
                }
                self.activate("STUDENT_FREE", email, true);
            };

            // 1-Hour Trial
            document.getElementById("ps-btn-trial").onclick = function() {
                self.startOrCheckTrial(true);
            };
        },

        showModal: function(bannerText, isError) {
            var modal = document.getElementById("ps-license-modal");
            var banner = document.getElementById("ps-modal-banner");
            if (modal) modal.style.display = "flex";
            if (banner) {
                banner.innerText = bannerText;
                banner.style.borderLeftColor = isError ? "#ef4444" : "#38bdf8";
                banner.style.color = isError ? "#f87171" : "#cbd5e1";
            }
        },

        hideModal: function() {
            var modal = document.getElementById("ps-license-modal");
            if (modal) modal.style.display = "none";
        },

        checkStatus: function() {
            var cached = localStorage.getItem(this.STORAGE_KEY);
            if (cached) {
                try {
                    var data = JSON.parse(cached);
                    if (data && data.status === "active") {
                        this.hideModal();
                        this.showUnlockedBadge(data.tier || "Licensed", data.buyer);
                        return;
                    }
                } catch(e) {}
            }
            this.startOrCheckTrial(false);
        },

        startOrCheckTrial: function(userTriggered) {
            var trialStart = localStorage.getItem(this.TRIAL_KEY);
            var now = Date.now();
            var durationMs = (window.PIXELSQUAD_CONFIG.TRIAL_DURATION_MINUTES || 60) * 60 * 1000;

            if (!trialStart) {
                trialStart = now;
                localStorage.setItem(this.TRIAL_KEY, trialStart);
                this.pingTelemetry("trial_started");
            }

            var elapsed = now - parseInt(trialStart, 10);
            var remaining = durationMs - elapsed;

            if (remaining > 0) {
                var remainingMins = Math.ceil(remaining / 60000);
                this.hideModal();
                this.showTrialBadge(remainingMins);
                var self = this;
                setTimeout(function() {
                    self.showModal("Your Free Trial has expired. Enter license key or student email to continue.", true);
                }, remaining);
            } else {
                this.showModal("Your Free Trial has expired (" + (window.PIXELSQUAD_CONFIG.TRIAL_DURATION_MINUTES || 60) + "m limit reached). Enter License Key or Student Email.", true);
            }
        },

        showTrialBadge: function(minsLeft) {
            var el = document.getElementById("ps-license-badge");
            if (!el) {
                el = document.createElement("div");
                el.id = "ps-license-badge";
                el.style.cssText = "font-size:9.5px;color:#f59e0b;background:#1e293b;padding:3px 8px;border-radius:4px;display:inline-block;margin-top:6px;border:1px solid #f59e0b;";
                var header = document.querySelector(".header");
                if (header) header.appendChild(el);
            }
            el.innerText = "⏳ Trial Active: " + minsLeft + "m left";
        },

        showUnlockedBadge: function(tier, buyer) {
            var el = document.getElementById("ps-license-badge");
            if (!el) {
                el = document.createElement("div");
                el.id = "ps-license-badge";
                el.style.cssText = "font-size:9.5px;color:#10b981;background:#064e3b;padding:3px 8px;border-radius:4px;display:inline-block;margin-top:6px;border:1px solid #10b981;";
                var header = document.querySelector(".header");
                if (header) header.appendChild(el);
            }
            el.innerText = "✓ " + (tier === "STUDENT" ? "🎓 Student: " : "Licensed: ") + (buyer || "Active");
        },

        activate: function(key, email, isStudent) {
            var banner = document.getElementById("ps-modal-banner");
            if (banner) banner.innerText = isStudent ? "Verifying Student Whitelist..." : "Verifying License Key...";

            var cfg = window.PIXELSQUAD_CONFIG;
            if (!cfg.SUPABASE_URL || cfg.SUPABASE_URL.indexOf("YOUR_PROJECT_ID") !== -1) {
                // Standalone local offline fallback
                var mockData = {
                    key: key,
                    buyer: email || "Active User",
                    status: "active",
                    tier: isStudent ? "STUDENT" : "COMMERCIAL",
                    activated_at: Date.now()
                };
                localStorage.setItem(this.STORAGE_KEY, JSON.stringify(mockData));
                this.hideModal();
                this.showUnlockedBadge(mockData.tier, mockData.buyer);
                alert(isStudent ? "Welcome PixelSquad Student! Full Access Unlocked." : "License Activated Successfully!");
                return;
            }

            var mid = this.getMachineId();
            var payload = {
                p_license_key: key,
                p_email: email,
                p_machine_id: mid,
                p_machine_name: window.navigator.platform || "Desktop Workstation",
                p_is_student: isStudent
            };

            var url = cfg.SUPABASE_URL + "/rest/v1/rpc/activate_pixelsquad_license";
            var self = this;

            fetch(url, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "apikey": cfg.SUPABASE_ANON_KEY,
                    "Authorization": "Bearer " + cfg.SUPABASE_ANON_KEY
                },
                body: JSON.stringify(payload)
            })
            .then(function(res) { return res.json(); })
            .then(function(data) {
                if (data && data.success) {
                    var sessionData = {
                        key: key,
                        buyer: data.buyer || email,
                        status: "active",
                        tier: data.tier || (isStudent ? "STUDENT" : "COMMERCIAL")
                    };
                    localStorage.setItem(self.STORAGE_KEY, JSON.stringify(sessionData));
                    self.hideModal();
                    self.showUnlockedBadge(sessionData.tier, sessionData.buyer);
                    alert(data.message || "PixelSquad Suite Unlocked Successfully!");
                } else {
                    self.showModal(data.message || "Invalid license key or email.", true);
                }
            })
            .catch(function(err) {
                self.showModal("Connection error. Check internet or contact hello@pixelsquad.in", true);
            });
        },

        startHeartbeat: function() {
            var self = this;
            setInterval(function() {
                self.pingTelemetry("heartbeat");
            }, 15 * 60 * 1000);
        },

        pingTelemetry: function(event) {
            var cfg = window.PIXELSQUAD_CONFIG;
            if (!cfg.SUPABASE_URL || cfg.SUPABASE_URL.indexOf("YOUR_PROJECT_ID") !== -1) return;

            var mid = this.getMachineId();
            var cached = localStorage.getItem(this.STORAGE_KEY);
            var key = "none";
            if (cached) {
                try { key = JSON.parse(cached).key || "none"; } catch(e){}
            }

            var payload = {
                machine_id: mid,
                event: event,
                license_key: key,
                platform: window.navigator.platform,
                last_ping: new Date().toISOString()
            };

            fetch(cfg.SUPABASE_URL + "/rest/v1/pixelsquad_telemetry", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "apikey": cfg.SUPABASE_ANON_KEY,
                    "Authorization": "Bearer " + cfg.SUPABASE_ANON_KEY,
                    "Prefer": "return=minimal"
                },
                body: JSON.stringify(payload)
            }).catch(function(){});
        }
    };

    window.PixelSquadLicenseManager = LM;
    window.addEventListener("DOMContentLoaded", function() {
        LM.init();
    });
})();