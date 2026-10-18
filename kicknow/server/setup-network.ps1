# KickNow – einmalige Netzwerk-Einrichtung (benoetigt Administratorrechte)
#  1. URL-Reservierung, damit der Server ohne Adminrechte im Netzwerk lauschen darf
#  2. Firewall-Regel, die den Port NUR fuer Geraete im eigenen lokalen Subnetz oeffnet
# Rueckgaengig machen: ... -File setup-network.ps1 -Remove
param([int]$Port = 8080, [switch]$Remove)

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
  [Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
  $argList = "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`" -Port $Port"
  if ($Remove) { $argList += ' -Remove' }
  Start-Process powershell.exe -Verb RunAs -ArgumentList $argList
  exit
}

$ruleName = "KickNow Demo (TCP $Port)"
& netsh http delete urlacl "url=http://+:$Port/" | Out-Null
Remove-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue

if ($Remove) {
  Write-Host "Einrichtung fuer Port $Port wurde entfernt." -ForegroundColor Green
} else {
  # WD = "Jeder" (sprachunabhaengige SID)
  & netsh http add urlacl "url=http://+:$Port/" "sddl=D:(A;;GX;;;WD)" | Out-Null
  New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Protocol TCP -LocalPort $Port `
    -Action Allow -Profile Private, Public -RemoteAddress LocalSubnet | Out-Null
  Write-Host ''
  Write-Host "Fertig! Port $Port ist fuer Geraete im lokalen Netzwerk freigegeben." -ForegroundColor Green
  Write-Host 'Starte jetzt "KickNow starten.bat".'
}
Write-Host ''
Read-Host 'Enter druecken zum Schliessen'
