// JavaScript to run in Chrome Console (F12) to get SSID
// 1. Open https://market-qx.trade
// 2. Login
// 3. F12 -> Console
// 4. Paste this code:

(function getQuotexSession() {
    // Try localStorage
    let session = localStorage.getItem('session') || localStorage.getItem('ssid') || localStorage.getItem('quotex_session');
    
    // Try to get from cookies
    if (!session) {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name.toLowerCase().includes('session') || name.toLowerCase().includes('ssid')) {
                session = value;
                break;
            }
        }
    }
    
    if (session) {
        console.log('Session ID found:', session);
        console.log('Copy this value and paste it in the terminal');
        return session;
    } else {
        console.log('No session found in localStorage or cookies');
        console.log('Try logging in first');
        return null;
    }
})();
