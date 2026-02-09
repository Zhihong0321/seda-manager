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

    let fetchedData = null;

    // Auto-detect MyKad
    async function autoDetect() {
        try {
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            if (tab && tab.url.includes("atap.seda.gov.my")) {
                chrome.tabs.sendMessage(tab.id, { action: "getMyKad" }, (response) => {
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

        showStatus("Connecting to " + SERVER_BASE + "...", "");
        fetchBtn.disabled = true;

        try {
            const url = `${SERVER_BASE}/api/v1/mapper/by-mykad/${mykad}`;
            console.log("Fetching from:", url);

            const response = await fetch(url, {
                method: 'GET',
                mode: 'cors',
                headers: { 'Accept': 'application/json' }
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: "Network Error" }));
                throw new Error(errorData.detail || `Server Error (${response.status})`);
            }

            const result = await response.json();
            fetchedData = result.mapped_to_seda;
            const systemDetails = result.system_details;

            showPreview(fetchedData, systemDetails);
            showStatus("Data synced from SEDA DB!", "success");
            fillBtn.disabled = false;
        } catch (err) {
            console.error("Fetch error:", err);
            let msg = err.message;
            if (msg === "Failed to fetch") {
                msg = "Failed to fetch (Check if local server is running on port 8000)";
            }
            showStatus("Error: " + msg, "error");
        } finally {
            fetchBtn.disabled = false;
        }
    });

    fillBtn.addEventListener('click', async () => {
        if (!fetchedData) return;
        fillBtn.disabled = true;
        showStatus("Mapping data...", "");

        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        chrome.tabs.sendMessage(tab.id, { action: "fillForm", data: fetchedData }, (response) => {
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
                    <div class="data-item"><span class="data-label">Panel Qty:</span> <span style="font-weight:bold; color:var(--accent)">${details.panel_qty || 'N/A'}</span></div>
                    <div class="data-item"><span class="data-label">Amount:</span> <span>${details.total_amount ? 'RM ' + details.total_amount : 'N/A'}</span></div>
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
