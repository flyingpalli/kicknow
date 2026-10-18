# KickNow – minimaler statischer Webserver für das lokale Netzwerk (keine Installation nötig)
# Start: Doppelklick auf "KickNow starten.bat" oder
#        powershell -ExecutionPolicy Bypass -File server\server.ps1 [-Port 8080]
param([int]$Port = 8080)

$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path.TrimEnd('\') + '\'

$Mime = @{
  '.html' = 'text/html; charset=utf-8'; '.js' = 'application/javascript; charset=utf-8'
  '.css' = 'text/css; charset=utf-8'; '.svg' = 'image/svg+xml'; '.png' = 'image/png'
  '.json' = 'application/json'; '.webmanifest' = 'application/manifest+json'; '.ico' = 'image/x-icon'
}

$localOnly = $false
$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://+:$Port/")
try {
  $listener.Start()
} catch {
  # Ohne einmalige Einrichtung (URL-Reservierung) darf Windows nur localhost bedienen
  $localOnly = $true
  $listener = New-Object System.Net.HttpListener
  $listener.Prefixes.Add("http://localhost:$Port/")
  $listener.Start()
}

$ips = @(Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object {
    $_.IPAddress -notmatch '^(127\.|169\.254\.)' -and
    $_.InterfaceAlias -notmatch 'Loopback|vEthernet|VirtualBox|VMware|WSL|Hyper-V|Bluetooth'
  } | Select-Object -ExpandProperty IPAddress)

Write-Host ''
Write-Host '  KickNow-Server laeuft' -ForegroundColor Green
Write-Host '  ---------------------'
Write-Host "  Am PC:      http://localhost:$Port/"
if ($localOnly) {
  Write-Host ''
  Write-Host '  ACHTUNG: Nur am PC erreichbar. Fuehre einmalig "Netzwerk einrichten (einmalig).bat" aus,' -ForegroundColor Yellow
  Write-Host '  damit das iPhone im WLAN zugreifen darf. Danach diesen Server neu starten.' -ForegroundColor Yellow
} else {
  foreach ($ip in $ips) { Write-Host "  Am iPhone:  http://${ip}:$Port/" -ForegroundColor Cyan }
}
Write-Host ''
Write-Host '  Beenden mit Strg+C oder durch Schliessen des Fensters.'
Write-Host ''

try {
  while ($listener.IsListening) {
    $task = $listener.GetContextAsync()
    while (-not $task.AsyncWaitHandle.WaitOne(500)) { }  # erlaubt Strg+C zwischen Anfragen
    $ctx = $task.GetAwaiter().GetResult()
    $req = $ctx.Request
    $res = $ctx.Response
    $status = 200
    try {
      $rel = [Uri]::UnescapeDataString($req.Url.AbsolutePath).TrimStart('/')
      if ($rel -eq '' -or $rel.EndsWith('/')) { $rel += 'index.html' }
      $full = [IO.Path]::GetFullPath((Join-Path $Root $rel))
      $blocked = -not $full.StartsWith($Root, [StringComparison]::OrdinalIgnoreCase) -or
                 $full.StartsWith((Join-Path $Root 'server'), [StringComparison]::OrdinalIgnoreCase)
      if ($blocked -or -not (Test-Path -LiteralPath $full -PathType Leaf)) {
        $status = 404
        $bytes = [Text.Encoding]::UTF8.GetBytes('404 - Nicht gefunden')
        $res.ContentType = 'text/plain; charset=utf-8'
      } else {
        $bytes = [IO.File]::ReadAllBytes($full)
        $ext = [IO.Path]::GetExtension($full).ToLowerInvariant()
        $res.ContentType = if ($Mime.ContainsKey($ext)) { $Mime[$ext] } else { 'application/octet-stream' }
      }
      $res.StatusCode = $status
      $res.Headers['Cache-Control'] = 'no-cache'
      $res.ContentLength64 = $bytes.Length
      if ($req.HttpMethod -ne 'HEAD') { $res.OutputStream.Write($bytes, 0, $bytes.Length) }
    } catch {
      $status = 500
      try { $res.StatusCode = 500 } catch { }
    } finally {
      try { $res.Close() } catch { }
    }
    Write-Host ('  {0}  {1}  {2,-4} {3}' -f (Get-Date -Format 'HH:mm:ss'), $status, $req.HttpMethod, $req.Url.AbsolutePath) -ForegroundColor DarkGray
  }
} finally {
  $listener.Stop()
  $listener.Close()
}
