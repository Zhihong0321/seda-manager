/**
 * SEDA Application Mapper - Content Script
 */

console.log("SEDA Mapper: Content script loaded.");

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "fillForm") {
        const data = request.data;
        const stats = fillSedaForm(data);
        sendResponse({ success: true, stats: stats });
    } else if (request.action === "getMyKad") {
        // 1. Try input field
        let mykad = document.getElementById('mykad_passport')?.value;

        // 2. Try to find IC/MyKad in the text of the page (especially Step 1 headers)
        if (!mykad) {
            const bodyText = document.body.innerText;
            // Look for 12-digit numbers
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

function fillSedaForm(data) {
    console.log("SEDA Mapper: Filling form with data:", data);
    let fieldsFilled = 0;
    let fieldsTotal = Object.keys(data).length;

    for (const [key, value] of Object.entries(data)) {
        if (value === undefined || value === null || value === "") continue;

        let element = document.getElementById(key) || document.querySelector(`[name="${key}"]`);

        if (element) {
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
            fieldsFilled++;

            element.style.backgroundColor = "rgba(34, 197, 94, 0.2)";
            element.style.outline = "2px solid #22C55E";
            setTimeout(() => {
                element.style.backgroundColor = "";
                element.style.outline = "";
            }, 3000);
        }
    }

    return { filled: fieldsFilled, total: fieldsTotal };
}
