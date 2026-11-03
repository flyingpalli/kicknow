# KickNow

KickNow is a mobile web app for finding football pitches in Munich. It maps 132 pitches and Bolzplätze in the city and the Landkreis, and shows which slots are free, booked for club training, or used for league games. You can reserve slots, join pickup games, chat, and rate pitches. This repo holds a demo that runs fully in the browser and keeps its data on the phone.

## Running the demo on Windows + iPhone

Your PC serves the app, and your iPhone opens it in Safari over the same Wi-Fi. Nothing to install. You need admin rights on the PC and internet on both devices, since the map tiles load from the web.

### 1. Download

Go to <https://github.com/flyingpalli/kicknow>, click the green **Code** button and pick **Download ZIP**. Extract it (right-click > Extract All) and open the inner `kicknow` folder, the one with `index.html` and two `.bat` files.

If you get a 404, the repo is private. Ask the owner for access or just the ZIP.

### 2. One-time network setup

Double-click `Netzwerk einrichten (einmalig).bat` and confirm the admin prompt. Wait for "Fertig!", then press Enter. This lets devices on your local network reach port 8080. It doesn't expose anything to the internet.

If SmartScreen complains, click **More info** > **Run anyway**.

### 3. Start the server

Double-click `KickNow starten.bat`. The window shows an address like `http://192.168.178.23:8080/` next to "Am iPhone". Leave the window open while you use the app. Closing it stops the server.

If you see a yellow warning instead of an iPhone address, step 2 didn't go through. Run it again and restart the server.

### 4. Open it on the iPhone

Connect the iPhone to the same Wi-Fi, open Safari, and type in the exact address from step 3, including `http://` and `:8080`. For an app-like feel, tap Share > **Add to Home Screen**.

Next time, just repeat steps 3 and 4.

### If something's off

**Page won't load on the iPhone.** Check both devices are on the same network and the server window is still open. Uni or guest Wi-Fi (eduroam etc.) often blocks device-to-device traffic. In that case turn on the iPhone's Personal Hotspot, connect the PC to it, and restart the server.

**Map is blank.** One of the devices has no internet.

**Location is only approximate.** iOS only gives exact GPS to `https://` sites, so the demo falls back to a rough position.

**Address changed.** That happens after a reboot or network switch. Restart the server and use the new one.

**Reset demo data.** Profile tab > "Demo zurücksetzen".

**Undo step 2.** In an admin PowerShell inside `kicknow\server`, run `powershell -ExecutionPolicy Bypass -File setup-network.ps1 -Remove`.
