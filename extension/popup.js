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

    let allResultData = null;

    // Helper to check if content script is ready
    async function ensureContentScriptReady(tabId) {
        try {
            const response = await chrome.tabs.sendMessage(tabId, { action: "ping" }).catch(() => null);
            return !!response;
        } catch (e) {
            return false;
        }
    }

    // Auto-detect MyKad
    async function autoDetect() {
        try {
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            if (tab && tab.url && tab.url.includes("atap.seda.gov.my")) {
                const isReady = await ensureContentScriptReady(tab.id);
                if (!isReady) {
                    console.warn("SEDA Mapper: Content script not ready on this page yet.");
                    return;
                }

                chrome.tabs.sendMessage(tab.id, { action: "getMyKad" }, (response) => {
                    if (chrome.runtime.lastError) {
                        console.log("Auto-detect suppressed error:", chrome.runtime.lastError.message);
                        return;
                    }
                    if (response && response.mykad) {
                        appIdInput.value = response.mykad;
                        showStatus("Auto-detected MyKad: " + response.mykad, "success");
                    }
                });
            }
        } catch (e) { console.error("Auto-detect failed", e); }
    }

    autoDetect();

    fetchBtn.addEventListener('click', async () => {
        const mykad = appIdInput.value.trim();
        if (!mykad) {
            showStatus("Please enter a MyKad number.", "error");
            return;
        }

        showStatus("Connecting to Railway...", "");
        fetchBtn.disabled = true;

        try {
            const url = `${SERVER_BASE}/api/v1/mapper/by-mykad/${mykad}`;
            const response = await fetch(url, {
                method: 'GET',
                mode: 'cors',
                headers: { 'Accept': 'application/json' }
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: "Network Error" }));
                throw new Error(errorData.detail || `Server Error (${response.status})`);
            }

            allResultData = await response.json();

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

    fillBtn.addEventListener('click', async () => {
        if (!allResultData) return;
        fillBtn.disabled = true;
        showStatus("Mapping data & Adding Modules...", "");

        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

        const isReady = await ensureContentScriptReady(tab.id);
        if (!isReady) {
            showStatus("Cant connect to SEDA page. Please REFRESH the SEDA page.", "error");
            fillBtn.disabled = false;
            return;
        }

        const messageBody = {
            action: "fillForm",
            data: {
                mapped_to_seda: allResultData.mapped_to_seda,
                module_details: allResultData.system_details.module_details
            }
        };

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
                    <div class="data-item" style="color:var(--accent); font-weight:bold;"><span class="data-label">Solar Module:</span> <span>JINKO 620W</span></div>
                    <div class="data-item"><span class="data-label">Panel Qty:</span> <span style="font-weight:bold; color:var(--accent)">${details.panel_qty || '0'}</span></div>
                    <div class="data-item"><span class="data-label">System Size:</span> <span style="font-weight:bold; color:var(--primary)">${details.calculated_kwp || '0'} kWp</span></div>
                    <div class="data-item" style="margin-top:4px; border-top:1px dotted #ccc; padding-top:4px;"><span class="data-label">TNB Account:</span> <span style="color:var(--primary)">${details.tnb_account || 'Missing'}</span></div>
                </div>
            `;
            previewDiv.innerHTML += detailsHtml;
        }

        previewDiv.innerHTML += '<div style="font-weight:600; margin-bottom:8px; font-size:11px; color:var(--accent)">READY TO MAP TO SEDA:</div>';
        previewDiv.style.display = "block";

        Object.entries(data).forEach(([key, val]) => {
            if (!val) return;
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
