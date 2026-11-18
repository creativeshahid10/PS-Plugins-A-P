/**
 * ====================================================================
 * PixelSquad Creative Suite
 * Copyright (C) 2026 PixelSquad. All Rights Reserved.
 * Author: Mohammed Shahid <hello@pixelsquad.in>
 * Proprietary & Confidential. Unauthorized copying, distribution,
 * modification, or reverse engineering is strictly prohibited.
 * ====================================================================
 */

/* ============================================================================
   TXTFX MASTER LOGIC
   ============================================================================ */

var csInterface = new CSInterface(); 

/* ---------------- HELPER FUNCTIONS ---------------- */
const $ = id => document.getElementById(id);
const show = el => { if (el) el.style.display = 'block'; };
const hide = el => { if (el) el.style.display = 'none'; };

function showToast(message, type = "success") {
    const toast = document.getElementById("successToast");
    if (!toast) return;
    toast.textContent = message;
    toast.className = `success-toast ${type} show`;
    setTimeout(() => {
        toast.classList.remove("show");
    }, 2200);
}

/* ---------------- SHOW APP ON LOAD (NO LICENSE) ---------------- */
document.addEventListener('DOMContentLoaded', () => {
    const app = $('appUI');
    if (app) app.style.display = 'block';
});

/* ================== ORIGINAL TXTFX LOGIC ================== */

window.onload = () => {
    const body = document.body;
    const tabTXT = $("tabTXT");
    const tab3D = $("tab3D");
    const tabTXT2 = $("tabTXT2");
    const tab3D2 = $("tab3D2");
    const scrollContainer = $("txtfxContent");
    let txtfxScrollTop = 0;

    // Подключаем JSX
    var EXT_PATH = csInterface.getSystemPath(SystemPath.EXTENSION);
    csInterface.evalScript('$.evalFile("' + EXT_PATH + '/js/jsx/applyTextFX.jsx")');

    function moveUnderline(tab) {
        if (!tab) return;
        const rect = tab.getBoundingClientRect();
        const parentRect = tab.parentElement.getBoundingClientRect();
        const underline = tab.parentElement.querySelector('.tab-underline');
        if (underline) {
            underline.style.transform = `translateX(${rect.left - parentRect.left + rect.width / 2 - 16}px)`;
        }
    }

    function switchToTXTFX() {
        body.classList.remove("app--3d");
        body.classList.add("app--txtfx");
        if(tabTXT) tabTXT.classList.add("active");
        if(tab3D) tab3D.classList.remove("active");
        moveUnderline(tabTXT);
        setTimeout(() => { if(scrollContainer) scrollContainer.scrollTop = txtfxScrollTop; }, 0);
    }

    function switchTo3D() {
        if(scrollContainer) txtfxScrollTop = scrollContainer.scrollTop;
        body.classList.remove("app--txtfx");
        body.classList.add("app--3d");
        if(tab3D) tab3D.classList.add("active");
        if(tabTXT) tabTXT.classList.remove("active");
        moveUnderline(tab3D);
    }

    if(tabTXT) tabTXT.onclick = switchToTXTFX;
    if(tab3D) tab3D.onclick = switchTo3D;
    if(tabTXT2) tabTXT2.onclick = switchToTXTFX;
    if(tab3D2) tab3D2.onclick = switchTo3D;

    // Back to top
    if($("goTopBtn")) $("goTopBtn").onclick = () => {
        scrollContainer.scrollTo({ top: 0, behavior: "smooth" });
    };

    // 3D Tracker buttons
    if ($("addTrackerBtn")) {
        $("addTrackerBtn").onclick = function () {
            csInterface.evalScript("add3DCameraTrackerToSelectedLayer()", () => {
                showToast("3D tracker added!");
            });
        };
    }
    if ($("buildFromSolidBtn")) {
        $("buildFromSolidBtn").onclick = function () {
            csInterface.evalScript("buildLyricsFromTrackedSolid()", () => {
                showToast("Built from tracking!");
            });
        };
    }

    // Обработка кликов по карточкам
    document.querySelectorAll(".fx-card").forEach(function (card) {
        card.addEventListener("click", function () {
            var fx = card.getAttribute("data-fx");
            if (!fx) return;

            var lyricsInput = $("lyricsInput");
            var lyrics = lyricsInput ? lyricsInput.value : "";
            csInterface.evalScript(
                'applyTextFX("' + fx + '","' + lyrics.replace(/"/g, '\\"') + '")',
                function (res) {
                    if(res !== "cancel") showToast("Applied!");
                }
            );
        });
    });

    
    // Category pill filtering
    const catPills = document.querySelectorAll('.cat-pill');
    catPills.forEach(pill => {
        pill.addEventListener('click', () => {
            catPills.forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
            const targetCat = pill.dataset.cat;
            
            document.querySelectorAll('.fx-card-wrap').forEach(wrap => {
                const cardCat = wrap.dataset.cat;
                if (targetCat === 'all' || cardCat === targetCat) {
                    wrap.style.display = '';
                } else {
                    wrap.style.display = 'none';
                }
            });
        });
    });

    setTimeout(() => { moveUnderline(tabTXT); }, 500);
};
