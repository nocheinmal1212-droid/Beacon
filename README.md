# Beacon
Supports message + file transfer directly between two devices, encrypted end-to-end, with no server in the middle. Same local network is required.

**How it works:**
- Transport is a **WebRTC DataChannel** — a direct peer-to-peer link between the two devices, encrypted with DTLS.
- The usual privacy hole in WebRTC is the *signaling server* that helps peers find each other. Beacon removes it entirely: you exchange one connection code **by hand** (copy/paste). Nothing ever touches a third party, so there's nothing to log or inspect.
- On top of DTLS, a **shared passphrase** derives an AES-256-GCM key (PBKDF2, 210k iterations) that wraps every message and file chunk. Even a hypothetical man-in-the-middle on the signaling step can't read anything without the passphrase.

**Using it:**
1. Both people open the file and type the *same* passphrase (agree on it in person or aloud).
2. One taps **Send / start link → Generate invite**, sends that code to the other.
3. The other pastes it, taps **Generate reply**, sends the reply code back.
4. First person pastes the reply, taps **Connect**. Now drag files or chat.

**Deployment across platforms:**
- **macOS / Windows:** just double-click `beacon.html`. Local `file://` works.
- **iOS:** Safari won't easily open a loose local file, and WebRTC needs a secure context. Host the single file over HTTPS — the simplest is a free GitHub Pages repo (drop in `beacon.html`, enable Pages, open the URL). Both devices then load the same URL. That host only serves the static file; it never sees your traffic, which still goes peer-to-peer.

**Notes:**
- **Bluetooth isn't feasible from a browser.** Web Bluetooth is for talking to BLE *peripherals*, not peer-to-peer between two phones, and iOS Safari doesn't support it at all. True Bluetooth transfer would require a native app per platform (Swift + Windows/WinRT, or a framework like Flutter/Tauri).
