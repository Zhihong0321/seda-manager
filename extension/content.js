/**
 * SEDA Application Mapper - Content Script
 */

console.log("SEDA Mapper: Content script active.");

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
