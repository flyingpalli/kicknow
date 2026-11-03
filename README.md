# KickNow

KickNow is a mobile web app for amateur football players in Munich. It shows 132 pitches and Bolzplätze in Munich and the surrounding Landkreis on a map. For each pitch you can see whether it is free, taken by club training, or used for a league match. You can reserve slots, join open pickup games, chat with other players, and rate pitches. This repository contains a demo version that runs in the browser and stores all data on the phone itself.

## Run the demo on Windows and open it on an iPhone

The PC acts as a small web server. The iPhone opens the app in Safari over your Wi-Fi. You do not need to install any software.

### What you need

- A Windows 10 or 11 PC with admin rights (you must be able to confirm "Allow this app to make changes").
- An iPhone.
- One Wi-Fi network that both devices use, with internet access (the map tiles load from the internet).

> **Note:** University, hotel, or guest Wi-Fi networks (for example eduroam) often block devices from talking to each other. If the iPhone cannot reach the PC later, turn on the iPhone's **Personal Hotspot** and connect the PC to it. Then repeat steps 4 to 6.

### Step 1: Download the project

1. Open the project page on GitHub in your browser: <https://github.com/flyingpalli/kicknow>
2. Click the green **Code** button near the top right.
3. Click **Download ZIP**. The file `kicknow-main.zip` lands in your **Downloads** folder.
4. Right-click the ZIP file and choose **Extract All...**, then click **Extract**.
5. Open the extracted folder. Inside it, open the subfolder that is also called **kicknow**. It contains `index.html` and two `.bat` files. This is the folder you work in from now on.

> If GitHub shows "404 Page not found", the repository is private. Ask the owner to add your GitHub account or to send you the ZIP file directly.

### Step 2: Allow network access (only once per PC)

1. Double-click **`Netzwerk einrichten (einmalig).bat`**.
2. Windows asks "Do you want to allow this app to make changes to your device?". Click **Yes**.
3. A blue window opens. Wait until it says **"Fertig!"** (Done), then press **Enter** to close it.

This step allows the demo server to accept connections from other devices in your local network on port 8080. It does not open the PC to the internet.

> **Windows SmartScreen:** If a blue box says "Windows protected your PC", click **More info**, then **Run anyway**. This happens because the file was downloaded from the internet.

### Step 3: Start the server

1. Double-click **`KickNow starten.bat`**.
2. A black window opens and shows **"KickNow-Server laeuft"** (server is running).
3. Below it you see one or more lines like this:

   ```
   Am iPhone:  http://192.168.178.23:8080/
   ```

   Write down this address. Your numbers will be different.
4. **Keep this window open** the whole time you use the demo. Closing it stops the app.

> If the window shows a yellow warning ("Nur am PC erreichbar"), Step 2 did not work. Close the window, repeat Step 2, and start the server again.
>
> If several "Am iPhone" lines appear, use the one that starts with `192.168.` first. Try the others if it does not work.

### Step 4: Check on the PC (optional)

Open <http://localhost:8080/> in your PC browser. If you see the KickNow map, the server works.

### Step 5: Open the app on the iPhone

1. Make sure the iPhone is on the **same Wi-Fi** as the PC (Settings > Wi-Fi).
2. Open **Safari**.
3. Type the address from Step 3 into the address bar, for example `http://192.168.178.23:8080/`. Type `http://` and the `:8080` at the end exactly as shown.
4. The KickNow map should load.

### Step 6: Add it to the home screen (optional)

1. In Safari, tap the **Share** button (square with an arrow pointing up).
2. Scroll down and tap **Add to Home Screen**, then **Add**.
3. KickNow now opens from its own icon like a normal app, without the Safari bar. The PC server must still be running.

### Stop the demo

Close the black server window, or click into it and press **Ctrl + C**. To start again later, repeat Step 3. Step 2 is not needed again.

### Troubleshooting

| Problem | What to try |
| --- | --- |
| Safari says "Safari can't open the page" or loads forever | Check that both devices use the same Wi-Fi. Check that the server window is still open. Try the iPhone hotspot from the note above. |
| The page loads, but the map stays empty | The PC or iPhone has no internet. The map tiles come from the internet. |
| The app does not find your exact GPS position | iPhones only share GPS with secure (`https://`) sites. The demo runs on `http://`, so it uses an approximate position instead. |
| Your PC's address changed | This happens after a restart or on a new network. Start the server again and use the new address it shows. |
| You want to undo Step 2 | Open PowerShell as admin in the `kicknow\server` folder and run `powershell -ExecutionPolicy Bypass -File setup-network.ps1 -Remove`. |
| You want to reset the demo data | In the app, open the profile tab and tap **Demo zurücksetzen**. |
