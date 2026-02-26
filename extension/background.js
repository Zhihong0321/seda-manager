const SERVER_BASE = "https://seda-manager-production.up.railway.app";

// Monitor whenever tabs are updated
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
    // Check if the page finished loading and it's on SEDA portal
    if (changeInfo.status === 'complete' && tab.url && tab.url.includes("atap.seda.gov.my")) {

        // Skip login and logout pages
        if (tab.url.includes("/login") || tab.url.includes("/logout")) {
            return;
        }

        // Auto-detect login: If they are on any other page on the portal, assume logged in
        try {
            const atapCookies = await chrome.cookies.getAll({ domain: "atap.seda.gov.my" });
            const baseCookies = await chrome.cookies.getAll({ domain: "seda.gov.my" });
            const cookies = Array.from(new Map([...atapCookies, ...baseCookies].map(c => [c.name, c])).values());

            if (cookies.length === 0) {
                console.log("Auto-Sync: No cookies found for SEDA.");
                return;
            }

            // Adding a small delay to ensure cookies are fully set
            setTimeout(async () => {
                try {
                    console.log("Auto-Sync: Syncing " + cookies.length + " cookies...");
                    const response = await fetch(`${SERVER_BASE}/api/v1/system/update-cookies`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(cookies)
                    });

                    const data = await response.json();
                    if (data.success && data.valid) {
                        console.log("Auto-Sync: Cookies successfully synced.");
                    } else {
                        console.log("Auto-Sync: Server rejected cookies: ", data.message);
                    }
                } catch (e) {
                    console.error("Auto-Sync: Failed to send cookies.", e);
                }
            }, 1000);

        } catch (err) {
            console.error("Auto-Sync: Failed getting cookies from Chrome", err);
        }
    }
});
