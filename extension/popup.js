/**
 * SEDA Application Mapper - Popup Logic
 */

const SERVER_BASE = "https://seda-manager-production.up.railway.app";

document.addEventListener('DOMContentLoaded', async () => {
    const fetchBtn = document.getElementById('fetch-btn');
    const fillBtn = document.getElementById('fill-btn');
    const appIdInput = document.getElementById('app-id');
    const statusDiv = document.getElementById('status');
    const previewDiv = document.getElementById('data-preview');
    const saveSettingsBtn = document.getElementById('save-settings-btn');
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    let allResultData = null;

    // --- Tab Switching ---
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.getAttribute('data-tab');
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById(`${tabId}-tab`).classList.add('active');
        });
    });

    // --- Settings Persistence ---
    async function loadSettings() {
        const settings = await chrome.storage.local.get(['seda_defaults']);
        if (settings.seda_defaults) {
            const d = settings.seda_defaults;
            document.getElementById('def-mod-brand').value = d.mod_brand || "21";
            document.getElementById('def-mod-brand-custom').value = d.mod_brand_custom || "";
            document.getElementById('def-mod-type').value = d.mod_type || "123";
            document.getElementById('def-mod-model').value = d.mod_model || "";
            document.getElementById('def-mod-cap').value = d.mod_cap || "620";
            document.getElementById('def-inv-brand').value = d.inv_brand || "63";
            document.getElementById('def-inv-brand-custom').value = d.inv_brand_custom || "";
            document.getElementById('def-inv-model').value = d.inv_model || "";
            document.getElementById('def-inv-cap').value = d.inv_cap || "5";
            document.getElementById('def-cost-ins').value = d.cost_ins || "0";
            document.getElementById('def-cost-om').value = d.cost_om || "0";
            // New Split Settings
            document.getElementById('def-split-pv').value = d.split_pv || "30";
            document.getElementById('def-split-inv').value = d.split_inv || "4500";
            document.getElementById('def-split-bos').value = d.split_bos || "15";
            document.getElementById('def-split-intercon').value = d.split_intercon || "15";

            document.getElementById('def-geo-lat').value = d.geo_lat || "";
            document.getElementById('def-geo-lng').value = d.geo_lng || "";
            document.getElementById('def-deterioration').value = d.deterioration || "0.80";
            document.getElementById('def-fin-model').value = d.fin_model || "1";

            toggleCustomFields();
        }
    }

    function toggleCustomFields() {
        const modBrand = document.getElementById('def-mod-brand').value;
        const invBrand = document.getElementById('def-inv-brand').value;
        document.getElementById('mod-custom-grp').style.display = (modBrand === "51") ? "flex" : "none";
        document.getElementById('inv-custom-grp').style.display = (invBrand === "93") ? "flex" : "none";
    }

    document.getElementById('def-mod-brand').addEventListener('change', toggleCustomFields);
    document.getElementById('def-inv-brand').addEventListener('change', toggleCustomFields);

    async function saveSettings() {
        const settings = {
            mod_brand: document.getElementById('def-mod-brand').value,
            mod_brand_custom: document.getElementById('def-mod-brand-custom').value,
            mod_type: document.getElementById('def-mod-type').value,
            mod_model: document.getElementById('def-mod-model').value,
            mod_cap: document.getElementById('def-mod-cap').value,
            inv_brand: document.getElementById('def-inv-brand').value,
            inv_brand_custom: document.getElementById('def-inv-brand-custom').value,
            inv_model: document.getElementById('def-inv-model').value,
            inv_cap: document.getElementById('def-inv-cap').value,
            cost_ins: document.getElementById('def-cost-ins').value,
            cost_om: document.getElementById('def-cost-om').value,
            // New Split Settings
            split_pv: document.getElementById('def-split-pv').value,
            split_inv: document.getElementById('def-split-inv').value,
            split_bos: document.getElementById('def-split-bos').value,
            split_intercon: document.getElementById('def-split-intercon').value,

            geo_lat: document.getElementById('def-geo-lat').value,
            geo_lng: document.getElementById('def-geo-lng').value,
            deterioration: document.getElementById('def-deterioration').value,
            fin_model: document.getElementById('def-fin-model').value
        };
        await chrome.storage.local.set({ seda_defaults: settings });
        showStatus("Admin Defaults Saved!", "success");
    }

    saveSettingsBtn.addEventListener('click', saveSettings);
    loadSettings();

    // --- Helper to check if content script is ready ---
    async function ensureContentScriptReady(tabId, url) {
        if (!url || (!url.includes("applications/") && !url.includes("profiles/"))) {
            return { ready: false, reason: "NOT_FORM_PAGE" };
        }
        try {
            const response = await chrome.tabs.sendMessage(tabId, { action: "ping" }).catch(() => null);
            if (response) return { ready: true };
            return { ready: false, reason: "SCRIPT_MISSING" };
        } catch (e) {
            return { ready: false, reason: "ERROR", detail: e.message };
        }
    }

    // --- Auto-detect MyKad ---
    async function autoDetect() {
        try {
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            if (!tab || !tab.url || !tab.url.includes("atap.seda.gov.my")) return;

            const storage = await chrome.storage.local.get(['last_mykad']);
            const lastMyKad = storage.last_mykad;

            // IS THIS A PROFILE PAGE? (Active detection allowed)
            if (tab.url.includes("/profiles/")) {
                const status = await ensureContentScriptReady(tab.id, tab.url);
                if (!status.ready) return;

                chrome.tabs.sendMessage(tab.id, { action: "getMyKad" }, (response) => {
                    if (chrome.runtime.lastError) return;
                    if (response && response.mykad) {
                        appIdInput.value = response.mykad;
                        showStatus("Detected MyKad: " + response.mykad, "success");
                        chrome.storage.local.set({ last_mykad: response.mykad });
                    } else if (lastMyKad) {
                        appIdInput.value = lastMyKad;
                        showStatus("Using last used MyKad: " + lastMyKad, "success");
                    }
                });
            }
            // IS THIS AN APPLICATION PAGE? (Strictly NO active detection, use persistence only)
            else if (tab.url.includes("/applications/")) {
                if (lastMyKad) {
                    appIdInput.value = lastMyKad;
                    showStatus("Restored MyKad from Profile: " + lastMyKad, "success");
                } else {
                    showStatus("Please capture MyKad on Profile page first.", "");
                }
            }
        } catch (e) { console.error("Auto-detect failed", e); }
    }

    autoDetect();

    // --- Financial Recalculation Helper ---
    function recalculateFinancials(data, settings) {
        if (!data.system_details || !data.system_details.invoice_amount) return;

        const totalAmount = parseFloat(data.system_details.invoice_amount) || 0;
        if (totalAmount <= 0) return;

        // Get percentages/values from settings or defaults
        const pvPct = parseFloat(settings.split_pv) || 30.0;
        const bosPct = parseFloat(settings.split_bos) || 15.0;
        const interconPct = parseFloat(settings.split_intercon) || 15.0;
        const invFixed = parseFloat(settings.split_inv) || 4500.00;

        // Calculate
        const pvCost = parseFloat((totalAmount * (pvPct / 100)).toFixed(2));
        const bosCost = parseFloat((totalAmount * (bosPct / 100)).toFixed(2));
        const interconCost = parseFloat((totalAmount * (interconPct / 100)).toFixed(2));
        const invCost = invFixed; // Fixed amount

        // Consultancy is remainder
        const sumKnown = pvCost + bosCost + interconCost + invCost;
        let consultCost = parseFloat((totalAmount - sumKnown).toFixed(2));
        if (consultCost < 0) consultCost = 0;

        // Update mapped_to_seda
        data.mapped_to_seda["financing_information[pv_modules_cost]"] = pvCost.toFixed(2);
        data.mapped_to_seda["financing_information[inverter_cost]"] = invCost.toFixed(2);
        data.mapped_to_seda["financing_information[balance_of_system]"] = bosCost.toFixed(2);
        data.mapped_to_seda["financing_information[interconnection_cost]"] = interconCost.toFixed(2);
        data.mapped_to_seda["financing_information[design_and_consultancy_cost]"] = consultCost.toFixed(2);

        // Update system_details breakdown for preview
        data.system_details.financial_breakdown = {
            [`PV (${pvPct}%)`]: pvCost,
            "Inverter": invCost,
            [`BOS (${bosPct}%)`]: bosCost,
            [`Intercon (${interconPct}%)`]: interconCost,
            "Consultancy": consultCost
        };
    }

    // --- Fetch Logic ---
    fetchBtn.addEventListener('click', async () => {
        const mykad = appIdInput.value.trim();
        if (!mykad) {
            showStatus("Please enter a MyKad number.", "error");
            return;
        }

        showStatus("Syncing with Railway...", "");
        fetchBtn.disabled = true;

        try {
            const url = `${SERVER_BASE}/api/v1/mapper/by-mykad/${mykad}`;
            const response = await fetch(url, {
                method: 'GET',
                mode: 'cors',
                headers: { 'Accept': 'application/json' }
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: "Not found" }));
                throw new Error(errorData.detail || `Server Error (${response.status})`);
            }

            allResultData = await response.json();

            // Save this MyKad as successfully verified
            chrome.storage.local.set({ last_mykad: mykad });

            // RECALCULATE FINANCIALS BASED ON LOCAL SETTINGS
            const settingsRes = await chrome.storage.local.get(['seda_defaults']);
            const defaults = settingsRes.seda_defaults || {};
            recalculateFinancials(allResultData, defaults);

            showPreview(allResultData.mapped_to_seda, allResultData.system_details);
            showStatus("Data synced from SEDA DB!", "success");
            fillBtn.disabled = false;
        } catch (err) {
            console.error("Fetch error:", err);
            showStatus("Error: " + err.message, "error");
        } finally {
            fetchBtn.disabled = false;
        }
    });

    // --- Fill Logic ---
    fillBtn.addEventListener('click', async () => {
        if (!allResultData) return;
        fillBtn.disabled = true;
        showStatus("Executing Automated Mapping...", "");

        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

        const status = await ensureContentScriptReady(tab.id, tab.url);
        if (!status.ready) {
            if (status.reason === "NOT_FORM_PAGE") {
                showStatus("Please go to a SEDA Application/Profile form page (Create or Edit).", "error");
            } else {
                showStatus("Connection Lost. Please REFRESH the SEDA browser page.", "error");
            }
            fillBtn.disabled = false;
            return;
        }

        // Load custom defaults to merge/override
        const settingsRes = await chrome.storage.local.get(['seda_defaults']);
        const defaults = settingsRes.seda_defaults || {};

        // Ensure financials are fresh based on current settings (in case user changed settings after fetch)
        recalculateFinancials(allResultData, defaults);

        const messageBody = {
            action: "fillForm",
            data: {
                mapped_to_seda: allResultData.mapped_to_seda,
                // Pass both the invoice-detected details and the user-configured defaults
                system_details: allResultData.system_details,
                admin_defaults: defaults
            }
        };

        console.log("SEDA Mapper: Sending fill data:", messageBody.data);

        chrome.tabs.sendMessage(tab.id, messageBody, (response) => {
            if (chrome.runtime.lastError) {
                showStatus("Communication error. Refresh SEDA page.", "error");
            } else if (response && response.success) {
                showStatus(`Done! Mapped ${response.stats.filled} fields.`, "success");
            }
            fillBtn.disabled = false;
        });
    });

    function showStatus(msg, type) {
        statusDiv.textContent = msg;
        statusDiv.className = "status " + (type || "");
        statusDiv.style.display = "block";
    }

    function showPreview(data, details) {
        previewDiv.innerHTML = '';

        if (details) {
            const detailsHtml = `
                <div style="background: rgba(255,140,0,0.1); border: 1px solid var(--primary); border-radius: 8px; padding: 10px; margin-bottom: 12px;">
                    <div style="font-weight:700; font-size:12px; color:var(--primary); margin-bottom:6px;">SYSTEM DETAILS</div>
                    <div class="data-item"><span class="data-label">Invoice:</span> <span>${details.invoice_no || 'N/A'}</span></div>
                    <div class="data-item"><span class="data-label">Package:</span> <span>${details.package_name || 'N/A'}</span></div>
                    <div class="data-item"><span class="data-label">Panel Qty:</span> <span style="font-weight:bold; color:var(--accent)">${details.panel_qty || '0'}</span></div>
                    <div class="data-item"><span class="data-label">System Size:</span> <span style="font-weight:bold; color:var(--primary)">${details.calculated_kwp || '0'} kWp</span></div>
                    <div class="data-item"><span class="data-label">TNB Account:</span> <span style="font-weight:bold; color:var(--success)">${data.account_number || 'N/A'}</span></div>
                </div>
            `;
            previewDiv.innerHTML += detailsHtml;
        }

        if (details && details.financial_breakdown) {
            let finHtml = `
                <div style="background: rgba(34,197,94,0.1); border: 1px solid #22c55e; border-radius: 8px; padding: 10px; margin-bottom: 12px;">
                    <div style="font-weight:700; font-size:12px; color:#15803d; margin-bottom:6px;">FINANCIAL TRACING (RM ${details.invoice_amount})</div>
            `;
            const breakdown = details.financial_breakdown;

            // Loop through all keys (PV, Inverter, BOS, Intercon, Consultancy)
            Object.entries(breakdown).forEach(([label, cost]) => {
                finHtml += `<div class="data-item"><span class="data-label">${label}:</span> <span style="font-weight:bold;">${cost.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span></div>`;
            });

            finHtml += `</div>`;
            previewDiv.innerHTML += finHtml;
        }

        previewDiv.innerHTML += '<div style="font-weight:600; margin-bottom:8px; font-size:11px; color:var(--accent)">READY TO MAP TO SEDA:</div>';
        previewDiv.style.display = "block";

        Object.entries(data).forEach(([key, val]) => {
            if (!val || typeof val === 'object') return;
            const item = document.createElement('div');
            item.className = "data-item";
            item.innerHTML = `
                <span class="data-label">${key}</span>
                <span class="data-value" style="color:var(--primary)">${val}</span>
            `;
            previewDiv.appendChild(item);
        });
    }
});
