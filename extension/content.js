/**
 * SEDA Application Mapper - Content Script
 */

console.log("SEDA Mapper: Content script loaded.");

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    // Add ping handler to verify connection
    if (request.action === "ping") {
        sendResponse({ success: true, message: "pong" });
    } else if (request.action === "fillForm") {
        const { mapped_to_seda, module_details } = request.data;
        const stats = fillSedaForm(mapped_to_seda, module_details);
        sendResponse({ success: true, stats: stats });
    } else if (request.action === "getMyKad") {
        let mykad = document.getElementById('mykad_passport')?.value;
        if (!mykad) {
            const bodyText = document.body.innerText;
            const icMatch = bodyText.match(/\b\d{12}\b/) || bodyText.match(/\b\d{6}-\d{2}-\d{4}\b/);
            if (icMatch) {
                mykad = icMatch[0].replace(/-/g, "");
                console.log("SEDA Mapper: Detected MyKad from text:", mykad);
            }
        }
        sendResponse({ mykad: mykad || null });
    }
    return true;
});

function fillSedaForm(data, moduleDetails) {
    console.log("SEDA Mapper: Filling form with data:", data);
    let fieldsFilled = 0;

    // 1. Fill Standard Fields
    for (const [key, value] of Object.entries(data)) {
        if (value === undefined || value === null || value === "") continue;
        const element = document.getElementById(key) || document.querySelector(`[name="${key}"]`);
        if (element) {
            setValue(element, value);
            fieldsFilled++;
        }
    }

    // 2. Handle Dynamic Modules Section
    if (moduleDetails && moduleDetails.quantity > 0) {
        const addModuleBtn = document.getElementById('add-module');
        if (addModuleBtn) {
            let moduleRow = document.querySelector('.module-row');
            if (!moduleRow) {
                addModuleBtn.click();
                moduleRow = document.querySelector('.module-row');
            }

            if (moduleRow) {
                const brandSel = moduleRow.querySelector('select[name^="modules"][name$="[equipment_id]"]');
                const typeSel = moduleRow.querySelector('select[name^="modules"][name$="[module_type_id]"]');
                const modelInp = moduleRow.querySelector('input[name^="modules"][name$="[model]"]');
                const capInp = moduleRow.querySelector('input[name^="modules"][name$="[capacity]"]');
                const qtyInp = moduleRow.querySelector('input[name^="modules"][name$="[count]"]');

                if (brandSel) setValue(brandSel, moduleDetails.brand);
                if (typeSel) setValue(typeSel, moduleDetails.type);
                if (modelInp) setValue(modelInp, moduleDetails.model);
                if (capInp) setValue(capInp, moduleDetails.capacity);
                if (qtyInp) setValue(qtyInp, moduleDetails.quantity);

                fieldsFilled += 5;

                moduleRow.style.backgroundColor = "rgba(147, 51, 234, 0.1)";
                moduleRow.style.outline = "2px solid #9333ea";
            }
        }
    }

    return { filled: fieldsFilled };
}

function setValue(element, value) {
    if (!element) return;
    if (element.tagName === "SELECT") {
        element.value = value;
        element.dispatchEvent(new Event('change', { bubbles: true }));
    } else if (element.type === "checkbox") {
        element.checked = (value === true || value === 1 || value === "1");
        element.dispatchEvent(new Event('change', { bubbles: true }));
    } else {
        element.value = value;
        element.dispatchEvent(new Event('input', { bubbles: true }));
        element.dispatchEvent(new Event('blur', { bubbles: true }));
    }

    // UI Feedback
    element.style.backgroundColor = "rgba(34, 197, 94, 0.2)";
    element.style.outline = "2px solid #22C55E";
    setTimeout(() => {
        element.style.backgroundColor = "";
        element.style.outline = "";
    }, 3000);
}
