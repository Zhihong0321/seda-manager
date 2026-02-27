/**
 * SEDA Application Mapper - Popup Logic
 */

const SERVER_BASE = "https://seda-manager-production.up.railway.app";

// --- Auto-Split Screen Logic ---
chrome.windows.getCurrent({ populate: false }, (win) => {
    // If we're already running in a popup window, don't split again.
    if (win.type === 'popup') return;

    // Calculate 70% / 30% dimensions
    const screenWidth = window.screen.availWidth;
    const screenHeight = window.screen.availHeight;
    const pageTargetWidth = Math.floor(screenWidth * 0.70);
    const extTargetWidth = screenWidth - pageTargetWidth;

    // Resize the main window to 70%
    chrome.windows.update(win.id, {
        state: "normal",
        left: 0,
        top: 0,
        width: pageTargetWidth,
        height: screenHeight
    });

    // Spawn the extension in a new popup window taking the right 30%
    chrome.windows.create({
        url: chrome.runtime.getURL("popup.html"),
        type: "popup",
        left: pageTargetWidth,
        top: 0,
        width: extTargetWidth,
        height: screenHeight
    });

    // Close this initial small popup
    window.close();
});

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

    // Listen for extension messages
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
        if (request.action === "mapperAutoLoad") {
            // Switch to Mapper tab if not active
            const mapperTabBtn = document.querySelector('.tab-btn[data-tab="mapper"]');
            if (mapperTabBtn) mapperTabBtn.click();

            appIdInput.value = request.mykad;
            fetchBtn.click();
            sendResponse({ received: true });
        }
    });

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

    // --- Database Tab Logic ---
    const refreshRegsBtn = document.getElementById('refresh-regs-btn');
    const registrationsList = document.getElementById('registrations-list');

    async function loadRegistrations() {
        if (!refreshRegsBtn || !registrationsList) return;

        refreshRegsBtn.disabled = true;
        registrationsList.innerHTML = '<div style="text-align:center; padding: 20px; color: var(--accent);">Fetching from API...</div>';

        try {
            const url = `${SERVER_BASE}/api/v1/mapper/registrations?limit=50`;
            const response = await fetch(url, { method: 'GET', mode: 'cors' });

            if (!response.ok) throw new Error("Failed to fetch registrations");
            const data = await response.json();

            registrationsList.innerHTML = '';

            if (data.registrations && data.registrations.length > 0) {
                data.registrations.forEach(reg => {
                    const card = document.createElement('div');
                    card.style.background = 'var(--card)';
                    card.style.borderRadius = '8px';
                    card.style.padding = '10px';
                    card.style.border = '1px solid #ffffff1a';
                    card.style.display = 'flex';
                    card.style.flexDirection = 'column';
                    card.style.gap = '6px';

                    const dt = new Date(reg.created_at);
                    const dateStr = !isNaN(dt) ? dt.toLocaleDateString() : '';

                    const header = document.createElement('div');
                    header.style.display = 'flex';
                    header.style.justifyContent = 'space-between';
                    header.style.fontWeight = 'bold';
                    header.style.fontSize = '12px';

                    const titleName = reg.customer_name || reg.bubble_id || 'Unknown Customer';
                    const dbIdHtml = reg.bubble_id ? `<span style="font-size:9px; color:var(--text-dim); display:block; font-weight:normal;">ID: ${reg.bubble_id}</span>` : '';

                    header.innerHTML = `
                        <div>
                            <span style="color:var(--primary); font-size:13px;">${titleName}</span>
                            ${dbIdHtml}
                        </div>
                        <span style="font-size:10px; color:var(--text-dim); white-space: nowrap;">${dateStr}</span>
                    `;

                    const details = document.createElement('div');
                    details.style.fontSize = '11px';
                    details.innerHTML = `
                        <div><span class="data-label">MyKad:</span> <span style="font-weight:bold">${reg.ic_no || '-'}</span></div>
                        <div><span class="data-label">TNB:</span> ${reg.tnb_account_no || '-'}</div>
                        <div><span class="data-label">State:</span> ${reg.state || '-'}</div>
                    `;

                    const btnGroup = document.createElement('div');
                    btnGroup.style.display = 'flex';
                    btnGroup.style.gap = '6px';
                    btnGroup.style.marginTop = '4px';

                    const actionBtn = document.createElement('button');
                    actionBtn.className = 'btn-primary';
                    actionBtn.style.padding = '6px';
                    actionBtn.style.fontSize = '11px';
                    actionBtn.style.flex = '1';
                    actionBtn.innerText = 'Use in Mapper';

                    actionBtn.onclick = () => {
                        // Switch back to mapper tab
                        const mapperTabBtn = document.querySelector('.tab-btn[data-tab="mapper"]');
                        if (mapperTabBtn) mapperTabBtn.click();

                        if (appIdInput) {
                            appIdInput.value = reg.ic_no;
                            showStatus("MyKad set to: " + reg.ic_no, "success");
                            if (fetchBtn) fetchBtn.click();
                        }
                    };

                    const createProfileBtn = document.createElement('button');
                    createProfileBtn.className = 'btn-primary';
                    createProfileBtn.style.padding = '6px';
                    createProfileBtn.style.fontSize = '11px';
                    createProfileBtn.style.background = 'var(--success)';
                    createProfileBtn.style.flex = '1';
                    createProfileBtn.innerText = 'Auto Create Profile';

                    createProfileBtn.onclick = async () => {
                        createProfileBtn.disabled = true;
                        createProfileBtn.innerText = 'Opening...';
                        try {
                            const res = await fetch(`${SERVER_BASE}/api/v1/mapper/profile-payload/${reg.ic_no}`);
                            const data = await res.json();
                            if (res.ok && data.success) {
                                await chrome.storage.local.set({
                                    auto_profile_flag: true,
                                    auto_profile_data: data.payload
                                });
                                chrome.tabs.create({ url: "https://atap.seda.gov.my/profiles/individuals" });
                                showStatus("Opening profile creation page...", "success");
                            } else {
                                showStatus("Failed to get profile data: " + (data.detail || data.message), "error");
                            }
                        } catch (e) {
                            showStatus("Error: " + e.message, "error");
                        } finally {
                            createProfileBtn.disabled = false;
                            createProfileBtn.innerText = 'Auto Create Profile';
                        }
                    };

                    btnGroup.appendChild(actionBtn);
                    btnGroup.appendChild(createProfileBtn);

                    card.appendChild(header);
                    card.appendChild(details);
                    card.appendChild(btnGroup);
                    registrationsList.appendChild(card);
                });
            } else {
                registrationsList.innerHTML = '<div style="text-align:center; padding: 20px; color: var(--text-dim);">No recent registrations found</div>';
            }
        } catch (e) {
            registrationsList.innerHTML = `<div style="text-align:center; padding: 20px; color: #ef4444;">Error: ${e.message}</div>`;
        } finally {
            refreshRegsBtn.disabled = false;
        }
    }

    if (refreshRegsBtn) {
        refreshRegsBtn.addEventListener('click', loadRegistrations);
    }

    const dbTabBtn = document.querySelector('.tab-btn[data-tab="registrations"]');
    if (dbTabBtn) {
        dbTabBtn.addEventListener('click', () => {
            if (registrationsList && registrationsList.innerHTML.includes('Click Refresh')) {
                loadRegistrations();
            }
        });
    }

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
                    if (storage.auto_fetch) {
                        chrome.storage.local.set({ auto_fetch: false });
                        setTimeout(() => fetchBtn.click(), 500);
                    }
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

    // --- Cookie Sync Logic ---
    const syncCookieBtn = document.getElementById('sync-cookie-btn');
    if (syncCookieBtn) {
        syncCookieBtn.addEventListener('click', async () => {
            syncCookieBtn.disabled = true;
            showStatus("Syncing cookies...", "");

            try {
                // Get ALL cookies associated with the domain and its subdomain
                const atapCookies = await chrome.cookies.getAll({ domain: "atap.seda.gov.my" });
                const baseCookies = await chrome.cookies.getAll({ domain: "seda.gov.my" });
                const cookies = Array.from(new Map([...atapCookies, ...baseCookies].map(c => [c.name, c])).values());

                if (cookies.length === 0) {
                    showStatus("No SEDA cookies found. Are you logged in?", "error");
                    syncCookieBtn.disabled = false;
                    return;
                }

                showStatus(`Sending ${cookies.length} cookies to server...`, "");

                const response = await fetch(`${SERVER_BASE}/api/v1/system/update-cookies`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(cookies)
                });

                if (!response.ok) {
                    throw new Error(`Server returned ${response.status}`);
                }

                const data = await response.json();

                if (data.success && data.valid) {
                    showStatus("Session synced successfully!", "success");
                    // Update LED directly
                    const led = document.getElementById('cookie-led');
                    if (led) {
                        led.className = 'led synced';
                        led.title = 'Cookies Synced with Server';
                    }
                } else if (data.success && !data.valid) {
                    showStatus(data.message, "error");
                } else {
                    throw new Error(data.message || "Failed to sync");
                }
            } catch (err) {
                console.error("Cookie sync failed:", err);
                showStatus(`Sync failed: ${err.message}`, "error");
            } finally {
                syncCookieBtn.disabled = false;
            }
        });
    }

    // --- Auto-detect Background Status Check ---
    async function checkServerStatus() {
        const led = document.getElementById('cookie-led');
        if (led) {
            led.className = 'led checking';
            led.title = 'Checking server status...';
        }

        try {
            const response = await fetch(`${SERVER_BASE}/api/v1/system/status`);
            if (response.ok) {
                const data = await response.json();
                const isHealthy = data.checks && data.checks.seda_session && data.checks.seda_session.status === 'healthy';

                if (isHealthy) {
                    if (led) {
                        led.className = 'led synced';
                        led.title = 'Cookies Synced with Server';
                    }
                } else {
                    if (led) {
                        led.className = 'led';
                        led.title = 'Cookies Not Synced!';
                    }
                    if (syncCookieBtn) {
                        const statusText = document.createElement('div');
                        statusText.style.fontSize = '10px';
                        statusText.style.color = '#ef4444';
                        statusText.style.marginTop = '4px';
                        statusText.innerText = "Server needs active SEDA session! Please Sync.";
                        syncCookieBtn.parentNode.insertBefore(statusText, syncCookieBtn.nextSibling);
                    }
                }
            } else {
                if (led) {
                    led.className = 'led';
                    led.title = 'Server Error!';
                }
            }
        } catch (e) {
            console.warn("Failed to check server status natively");
            if (led) {
                led.className = 'led';
                led.title = 'Cannot connect to server';
            }
        }
    }
    checkServerStatus();

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
