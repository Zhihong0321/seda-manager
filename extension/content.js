/**
 * SEDA Application Mapper - Content Script
 */

console.log("SEDA Mapper: Content script active.");

// --- Auto-fill Complete Application Form on load ---
chrome.storage.local.get(['auto_app_flag', 'auto_app_data', 'seda_defaults'], (res) => {
    if (res.auto_app_flag && res.auto_app_data && window.location.href.includes("applications/")) {
        // Clear flag immediately to prevent repeat execution on refresh
        chrome.storage.local.set({ auto_app_flag: false });

        const data = res.auto_app_data;
        const defaults = res.seda_defaults || {};

        // Wait a brief moment to ensure dynamic framework rendering is complete
        setTimeout(() => {
            console.log("SEDA Mapper: Auto-filling NEW application directly from memory payload...", data);
            const stats = fillSedaForm(data.mapped_to_seda, data.system_details, defaults);
            console.log(`SEDA Mapper: Instantly filled ${stats.filled} fields without Popup.`);
        }, 1500);
    }
});


// --- Auto-fill Individual Profile on load ---
chrome.storage.local.get(['auto_profile_flag', 'auto_profile_data'], (res) => {
    if (res.auto_profile_flag && res.auto_profile_data && window.location.href.includes("profiles/individuals")) {
        // Clear flag immediately to prevent repeat execution on refresh
        chrome.storage.local.set({ auto_profile_flag: false });

        const mapping = {
            'salutation': 'salutation',
            'name': 'name',
            'citizenship': 'citizenship',
            'ic_number': 'mykad_passport',
            'email': 'email',
            'address_line_1': 'address_line_1',
            'address_line_2': 'address_line_2',
            'address_line_3': 'address_line_3',
            'postcode': 'postcode',
            'town': 'town',
            'state': 'state',
            'phone': 'phone',
            'mobile': 'mobile',
            'emergency_salutation': 'contact_salutation',
            'emergency_name': 'contact_name',
            'emergency_ic_number': 'contact_mykad_passport',
            'emergency_citizenship': 'contact_citizenship',
            'emergency_relationship': 'contact_relationship',
            'emergency_email': 'contact_email',
            'emergency_phone': 'contact_phone',
            'emergency_mobile': 'contact_mobile'
        };

        // Wait a brief moment to ensure dynamic framework rendering is complete
        setTimeout(() => {
            let filled = 0;
            const payload = res.auto_profile_data;
            for (const [cleanKey, htmlName] of Object.entries(mapping)) {
                if (payload[cleanKey]) {
                    const el = document.getElementById(htmlName) || document.querySelector(`[name="${htmlName}"]`);
                    if (el) {
                        setValue(el, payload[cleanKey]);
                        filled++;
                    }
                }
            }
            console.log("SEDA Mapper: Auto-filled " + filled + " individual profile fields from payload.");
        }, 1500);
    }
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "ping") {
        sendResponse({ success: true });
    } else if (request.action === "fillForm") {
        const { mapped_to_seda, system_details, admin_defaults } = request.data;
        const stats = fillSedaForm(mapped_to_seda, system_details, admin_defaults);
        sendResponse({ success: true, stats: stats });
    } else if (request.action === "getMyKad") {
        let mykad = null;

        // 1. Primary: Direct input field (Profile Page)
        mykad = document.getElementById('mykad_passport')?.value;

        // 2. Secondary: Search for text display with context check
        if (!mykad) {
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
            let node;
            while (node = walker.nextNode()) {
                const text = node.textContent.trim();
                const match = text.match(/\b\d{12}\b/);
                if (match) {
                    const ic = match[0];
                    // Look back at the label or nearby text context
                    // We check the parent and its sibling or the overall container
                    const container = node.parentElement?.closest('div, tr, td, .form-group') || node.parentElement;
                    const contextText = (container?.innerText || "").toLowerCase();

                    // If it's a contact person or engineer, skip it
                    if (contextText.includes("contact person") || contextText.includes("engineer")) {
                        continue;
                    }

                    // If it's explicitly an applicant or MyKad field, we found it!
                    if (contextText.includes("applicant") || contextText.includes("mykad") || contextText.includes("passport")) {
                        mykad = ic;
                        break;
                    }

                    // Otherwise, keep it as a weak candidate
                    if (!mykad) mykad = ic;
                }
            }
        }

        sendResponse({ mykad: mykad || null });
    }
    return true;
});

function fillSedaForm(data, systemDetails, adminDefaults) {
    let fieldsFilled = 0;

    // 1. Fill Licensee first (Pre-requisite for many portal triggers)
    const licensee = document.getElementById('distribution_licence_id');
    if (licensee && data.distribution_licence_id) {
        setValue(licensee, data.distribution_licence_id);
    }

    // 2. Fill Standard Fields (Applicant, Finance, Engineer)
    for (const [key, value] of Object.entries(data)) {
        if (!value || typeof value === 'object') continue;
        if (key === 'account_number' || key === 'distribution_licence_id') continue;

        const element = document.getElementById(key) || document.querySelector(`[name="${key}"]`);
        if (element) {
            setValue(element, value);
            fieldsFilled++;
        }
    }

    // 2. Handle Dynamic Modules Section
    const moduleQty = systemDetails.panel_qty || 0;
    if (moduleQty > 0) {
        const addModuleBtn = document.getElementById('add-module');
        if (addModuleBtn) {
            let row = document.querySelector('.module-row');
            if (!row) { addModuleBtn.click(); row = document.querySelector('.module-row'); }

            if (row) {
                const modData = systemDetails.module_details || {};
                let brand = "21"; // Default Jinko
                let brandOther = "";
                let model = modData.model || "Tiger Neo";
                let cap = modData.capacity || "620";

                const parsedBrand = (modData.brand || "").toUpperCase();
                if (parsedBrand.includes("JINKO")) {
                    brand = "21";
                } else if (parsedBrand.includes("ASTRONERGY")) {
                    brand = "51";
                    brandOther = "ASTRONERGY";
                } else if (parsedBrand.includes("TRINA")) {
                    brand = "51";
                    brandOther = "TRINA SOLAR";
                } else if (parsedBrand) {
                    brand = "51";
                    brandOther = parsedBrand;
                }

                const type = adminDefaults.mod_type || "123";  // Default Monocrystalline

                setValue(row.querySelector('select[name$="[equipment_id]"]'), brand);
                if (brand === "51" && brandOther) {
                    const otherInp = row.querySelector('input[name$="[brand_other]"]');
                    if (otherInp) setValue(otherInp, brandOther);
                }

                setValue(row.querySelector('select[name$="[module_type_id]"]'), type);
                setValue(row.querySelector('input[name$="[model]"]'), model);
                setValue(row.querySelector('input[name$="[capacity]"]'), cap);
                setValue(row.querySelector('input[name$="[count]"]'), moduleQty);

                fieldsFilled += 5;
                applyHighlight(row, "purple");
            }
        }
    }

    // 3. Handle Dynamic Inverter Section
    const addInverterBtn = document.getElementById('add-inverter');
    if (addInverterBtn) {
        let invRow = document.querySelector('.inverter-row');
        if (!invRow) { addInverterBtn.click(); invRow = document.querySelector('.inverter-row'); }

        if (invRow) {
            const invData = systemDetails.inverter_details || {};
            let iBrand = "63"; // Default Huawei
            let iBrandOther = "";
            let iModel = invData.model || "SUN2000-5KTL";
            let iCap = invData.capacity || "5";

            const parsedInvBrand = (invData.brand || "").toUpperCase();
            if (parsedInvBrand.includes("HUAWEI")) {
                iBrand = "63";
            } else if (parsedInvBrand.includes("SAJ")) {
                iBrand = "93";
                iBrandOther = "SAJ";
            } else if (parsedInvBrand.includes("SOLIS")) {
                iBrand = "93";
                iBrandOther = "SOLIS";
            } else if (parsedInvBrand) {
                iBrand = "93";
                iBrandOther = parsedInvBrand;
            }

            setValue(invRow.querySelector('select[name$="[equipment_id]"]'), iBrand);
            if (iBrand === "93" && iBrandOther) {
                const otherInvInp = invRow.querySelector('input[name$="[brand_other]"]');
                if (otherInvInp) setValue(otherInvInp, iBrandOther);
            }

            setValue(invRow.querySelector('input[name$="[model]"]'), iModel);
            setValue(invRow.querySelector('input[name$="[capacity]"]'), iCap);
            setValue(invRow.querySelector('input[name$="[count]"]'), invData.quantity || "1");

            fieldsFilled += 4;
            applyHighlight(invRow, "blue");
        }
    }

    // 4. Fill Costs from Admin Defaults (Overriding calc if provided)
    const insPremium = document.getElementById('financing_information[insurance_premium]');
    const omCost = document.getElementById('financing_information[operation_and_maintenance_cost]');

    if (insPremium && adminDefaults.cost_ins !== undefined && adminDefaults.cost_ins !== "0") {
        setValue(insPremium, adminDefaults.cost_ins);
        fieldsFilled++;
    }
    if (omCost && adminDefaults.cost_om !== undefined && adminDefaults.cost_om !== "0") {
        setValue(omCost, adminDefaults.cost_om);
        fieldsFilled++;
    }

    // 5. Fill Geo Location (Handle Readonly fields)
    const latInp = document.getElementById('latitude');
    const lngInp = document.getElementById('longitude');

    if (latInp && lngInp) {
        const finalLat = data.latitude || adminDefaults.geo_lat;
        const finalLng = data.longitude || adminDefaults.geo_lng;

        if (finalLat && finalLng) {
            latInp.removeAttribute('readonly');
            lngInp.removeAttribute('readonly');

            setValue(latInp, finalLat);
            setValue(lngInp, finalLng);

            fieldsFilled += 2;
        }
    }

    // 6. Technical Summary & Financing
    const detInp = document.getElementById('plant_deterioration');
    if (detInp) {
        setValue(detInp, adminDefaults.deterioration || "0.80");
        fieldsFilled++;
    }

    const finModel = document.getElementById('financing_information[financial_model]');
    if (finModel) {
        setValue(finModel, adminDefaults.fin_model || "1");
        fieldsFilled++;
    }

    // 7. Electricity Account Number (Trigger portal AJAX)
    const tnbInp = document.getElementById('account_number') || document.querySelector('[name="account_number"]');
    if (tnbInp && data.account_number) {
        console.log("SEDA Mapper: Forcing TNB Account injection:", data.account_number);
        tnbInp.removeAttribute('readonly');
        tnbInp.removeAttribute('disabled');

        tnbInp.focus();
        // Mimic real typing to trigger JS listeners
        try {
            document.execCommand('selectAll', false, null);
            document.execCommand('insertText', false, data.account_number);
        } catch (e) {
            console.log("execCommand failed, using standard value assignment.");
            tnbInp.value = data.account_number;
        }

        // Force lookup triggers
        tnbInp.dispatchEvent(new Event('input', { bubbles: true }));
        tnbInp.dispatchEvent(new Event('change', { bubbles: true }));
        tnbInp.dispatchEvent(new Event('blur', { bubbles: true }));

        fieldsFilled++;
        applyHighlight(tnbInp, "green");
    } else {
        if (!tnbInp) console.warn("SEDA Mapper: Could not find element with ID 'account_number'");
        if (!data.account_number) console.warn("SEDA Mapper: No account_number found in data packet:", data);
    }

    return { filled: fieldsFilled };
}

function setValue(element, value) {
    if (!element) return;
    if (element.tagName === "SELECT") {
        element.value = value;
        element.dispatchEvent(new Event('change', { bubbles: true }));
    } else {
        element.focus();
        element.value = value;
        element.dispatchEvent(new Event('input', { bubbles: true }));
        element.dispatchEvent(new Event('change', { bubbles: true }));
        element.dispatchEvent(new Event('blur', { bubbles: true }));
    }
    applyHighlight(element, "green");
}

function applyHighlight(el, color) {
    const colors = {
        green: "rgba(34, 197, 94, 0.2)",
        purple: "rgba(147, 51, 234, 0.1)",
        blue: "rgba(56, 189, 248, 0.1)"
    };
    el.style.backgroundColor = colors[color] || colors.green;
    el.style.outline = `2px solid ${color === 'green' ? '#22C55E' : (color === 'purple' ? '#9333ea' : '#38BDF8')}`;
    setTimeout(() => { el.style.backgroundColor = ""; el.style.outline = ""; }, 4000);
}

// --- Inject Mapper Check Buttons in Profiles List ---
function injectProfileListButtons() {
    // Only run on the list page
    if (!window.location.href.includes('/profiles') || window.location.href.includes('/create') || window.location.href.includes('/edit')) {
        return;
    }

    // Find all table rows
    const rows = document.querySelectorAll('tr');

    rows.forEach(row => {
        // Skip if we already injected the button
        if (row.querySelector('.seda-mapper-check-btn')) return;

        // Find the "New Application" button usually in the last col
        const interactables = row.querySelectorAll('a, button');
        let newAppBtn = null;
        for (let el of interactables) {
            if (el.textContent && (el.textContent.includes('New Application') || el.innerText.includes('New Application'))) {
                newAppBtn = el;
                break;
            }
        }

        if (!newAppBtn) return;

        // Extract registration number (MyKad is ~12 digits)
        const rowText = row.innerText || row.textContent;
        const icMatch = rowText.match(/\b\d{12}\b/);
        let regNoText = icMatch ? icMatch[0] : "";

        if (!regNoText) {
            // Fallback: look at column 3 text
            const cols = row.querySelectorAll('td');
            if (cols.length >= 3) {
                regNoText = cols[2].textContent.trim();
            }
            if (!regNoText) return;
        }

        // Create the Check Button
        const checkBtn = document.createElement('button');
        checkBtn.className = 'btn btn-sm seda-mapper-check-btn';
        checkBtn.style.marginLeft = '8px';
        checkBtn.style.padding = '5px 10px';
        checkBtn.style.fontSize = '12px';
        checkBtn.style.fontWeight = 'bold';
        checkBtn.style.backgroundColor = '#FF8C00';
        checkBtn.style.color = '#fff';
        checkBtn.style.border = '1px solid #e07b00';
        checkBtn.style.borderRadius = '4px';
        checkBtn.style.cursor = 'pointer';
        checkBtn.style.display = 'inline-flex';
        checkBtn.style.alignItems = 'center';
        checkBtn.innerHTML = '&#128269; Check DB';
        checkBtn.title = 'Check SEDA Manager Database for ' + regNoText;

        // Insert next to the "New Application" button
        if (newAppBtn.parentNode) {
            newAppBtn.parentNode.insertBefore(checkBtn, newAppBtn.nextSibling);

            // Adjust parent display if needed to ensure they line up perfectly
            newAppBtn.parentNode.style.display = 'flex';
            newAppBtn.parentNode.style.gap = '5px';
            newAppBtn.parentNode.style.alignItems = 'center';
        }

        checkBtn.onclick = async (e) => {
            e.preventDefault();
            e.stopPropagation();

            const originalText = checkBtn.innerHTML;
            checkBtn.innerHTML = '&#8987; Checking...';
            checkBtn.disabled = true;

            try {
                // Fetch from our local backend
                const url = `https://seda-manager-production.up.railway.app/api/v1/mapper/by-mykad/${regNoText}`;
                const response = await fetch(url, { method: 'GET', mode: 'cors', headers: { 'Accept': 'application/json' } });

                if (response.ok) {
                    const data = await response.json();
                    if (data && data.success) {
                        checkBtn.innerHTML = '&#9989; Found!';
                        checkBtn.style.backgroundColor = '#22C55E';
                        checkBtn.style.border = '1px solid #16a34a';

                        // Completely bypass popup dependency, store directly to memory
                        chrome.storage.local.set({
                            last_mykad: regNoText,
                            auto_app_flag: true,
                            auto_app_data: data
                        });

                        // Wait a sec before clicking New Application automatically
                        setTimeout(() => {
                            newAppBtn.click();
                        }, 500);
                        return; // Exit
                    }
                }

                // If not found or API failed
                throw new Error("Not found");
            } catch (err) {
                console.error("SEDA Mapper: IC check failed:", err);
                checkBtn.innerHTML = '&#10060; Not Found';
                checkBtn.style.backgroundColor = '#ef4444';
                checkBtn.style.border = '1px solid #dc2626';

                // Reset button after 3 seconds so they can try again if they want
                setTimeout(() => {
                    checkBtn.disabled = false;
                    checkBtn.innerHTML = '&#128269; Check DB';
                    checkBtn.style.backgroundColor = '#FF8C00';
                    checkBtn.style.border = '1px solid #e07b00';
                }, 3000);
            }
        };
    });
}

// Repeatedly try to inject, just in case the table handles dynamic AJAX pagination or Vue rendering
setInterval(injectProfileListButtons, 1500);
