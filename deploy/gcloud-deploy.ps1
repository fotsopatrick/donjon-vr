# Deploiement KOTOAGE / WebMCP sur Google Cloud Storage (bucket statique HTTPS)
# Usage : powershell -ExecutionPolicy Bypass -File deploy\gcloud-deploy.ps1 [-Bucket galere] [-Projet galere] [-SansOui]
# Essai a blanc : powershell -ExecutionPolicy Bypass -File deploy\gcloud-deploy.ps1 -EssaiABlanc

param(
  [string]$Bucket = "",
  [string]$Projet = "",
  [switch]$SansOui,          # env. $env:ARMOR.. sinon demande confirmation
  [switch]$EssaiABlanc       # prepare seulement les commandes, ne rien executer
)

$ErrorActionPreference = "Continue"
$racine = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)   # dossier du jeu
$js_admin = "$env:LOCALAPPDATA\Google\Cloud SDK\google-cloud-sdk\bin"

function Resoudre-Binaire {
  param([string]$Binaire)
  $cmd = (Get-Command $Binaire -ErrorAction SilentlyContinue)
  if ($cmd -and $cmd.Source) { return $cmd.Source }
  foreach ($c in @(
    (Join-Path $js_admin "$Binaire.cmd"),
    "$env:ProgramFiles\Google\Cloud SDK\google-cloud-sdk\bin\$Binaire.cmd",
    "$env:ProgramFiles(x86)\Google\Cloud SDK\google-cloud-sdk\bin\$Binaire.cmd"
  )) { if (Test-Path $c) { return $c } }
  return ""
}
function Gcloud {
  $r = Resoudre-Binaire "gcloud"
  if (-not $r) { throw "gcloud introuvable. Obtenez-le : winget install -e --id Google.CloudSDK" }
  return $r
}
function Gsutil {
  $r = Resoudre-Binaire "gsutil"
  if (-not $r) { throw "gsutil introuvable (fourni avec gcloud)." }
  return $r
}
function GsutilZip {
  $sdk_root = Split-Path $js_admin
  foreach ($c in @(
    (Join-Path $sdk_root "platform\gsutil\gsutil"),
    "$env:ProgramFiles\Google\Cloud SDK\google-cloud-sdk\platform\gsutil\gsutil"
  )) { if (Test-Path $c) { return $c } }
  return ""
}

$GCLOUD = Gcloud
$GSUTIL = Gsutil
$GSUTIL_PY = GsutilZip
$PYTHON = (Get-Command "python" -ErrorAction SilentlyContinue).Source
if (-not $PYTHON) { $PYTHON = "python" }
$env:PATH = "$env:PATH;$js_admin"
$env:CLOUDSDK_CONFIG = (& $GCLOUD "info" "--format=value(config.paths.global_config_dir)" 2>&1 | Out-String).Trim()
Write-Host "gcloud  : $GCLOUD"
Write-Host "gsutil  : $GSUTIL  (via $PYTHON $GSUTIL_PY)"
Write-Host "source  : $racine"

# ---- Connexion ------------------------------------------------------------
$comptes = (& $GCLOUD "config" "get-value" "account" 2>&1 | Out-String).Trim()
if (-not $comptes) {
  Write-Host "PAS DE COMPTE ACTIF."
  Write-Host "    => Ouvrez https://console.cloud.google.com/ ou PowerShell local"
  Write-Host "       puis : gcloud auth login"
  Write-Host "Exemple local :  & ""$GCLOUD"" auth login"
  if (-not $EssaiABlanc) { exit 2 }
}
Write-Host "Compte actif : $comptes"

if (-not $Projet) {
  $Projet = (& $GCLOUD "config" "get-value" "project" 2>$null).Trim()
}
if (-not $Projet) {
  $Projet = Read-Host "ID de projet Google Cloud (facturation active obligatoire)"
}

if (-not $Bucket) {
  $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
  $Bucket = "kotoage-webmcp-$stamp"
}
Write-Host ""
Write-Host "Bucket cible : gs://$Bucket   (projet : $Projet)"
Write-Host "URL publique : https://storage.googleapis.com/$Bucket/index.html"

$tailleMo = [math]::Round(((Get-ChildItem $racine -Recurse -File -ErrorAction SilentlyContinue |
  Where-Object { $_.FullName -notmatch '\\(voix|\.git)\\' -and $_.Extension -ne '.zip' } |
  Measure-Object Length -Sum).Sum) / 1MB)
Write-Host ("Volume envoye (hors voix/, .git/, *.zip) : {0:N0} Mo" -f $tailleMo)

if ((-not $SansOui) -and (-not $EssaiABlanc)) {
  $ok = Read-Host "Confirmer creation + upload (o/n)"
  if ($ok -notin @("o","O","oui","OUI","y","yes")) { Write-Host "Abandon."; exit 1 }
}

function Exec($titre, $cmd) {
  Write-Host ""; Write-Host "==> $titre"
  Write-Host ("    " + ($cmd -join " "))
  if ($EssaiABlanc) { return }
  & $cmd[0] $cmd[1..($cmd.Length-1)] 2>&1
  if ($LASTEXITCODE -ne 0) { throw "Echec : $titre (code $LASTEXITCODE)" }
}

# ---- Bucket ---------------------------------------------------------------
$bs = @("$GCLOUD","storage","buckets","create","gs://$Bucket","--project=$Projet","--location=US",
        "--uniform-bucket-level-access")
Write-Host ""; Write-Host "==> Creation du bucket (uniform access). OK si 'already exists'."
Write-Host ("    " + ($bs -join " "))
if (-not $EssaiABlanc) {
  & $bs[0] $bs[1..($bs.Length-1)] 2>&1
  if ($LASTEXITCODE -ne 0 -and -not $EssaiABlanc) {
    Write-Warning "creation du bucket a renvoye code $LASTEXITCODE (probablement 'already exists') : on continue."
  }
}

Exec "Levee de la protection anti-acces-public" @("$GCLOUD","storage","buckets","update",
     "gs://$Bucket","--no-public-access-prevention")

Exec "Lecture publique (allUsers:objectViewer)" @("$GCLOUD","storage","buckets",
     "add-iam-policy-binding","gs://$Bucket","--member=allUsers",
     "--role=roles/storage.objectViewer")

Exec "Index par defaut index.html" @("$GCLOUD","storage","buckets","update",
     "gs://$Bucket","--web-main-page-suffix=index.html")

# ---- Upload ---------------------------------------------------------------
# gsutil est un .bat : from PowerShell, les metacharacteres (| ; ( ) ) sont
# devores par cmd.exe. On passe donc par un fichier .bat temporaire quotE.
function ExecBat($titre, $ligne) {
  Write-Host ""; Write-Host "==> $titre"
  Write-Host "    $ligne"
  if ($EssaiABlanc) { return }
  $bat = Join-Path $env:TEMP ("kotoage-" + [guid]::NewGuid().ToString("N").Substring(0,6) + ".bat")
  [IO.File]::WriteAllText($bat, $ligne + "`r`n")
  try   { & cmd.exe /d /c $bat 2>&1 }
  catch { }
  $code = $LASTEXITCODE
  Remove-Item $bat -ErrorAction SilentlyContinue
  if ($code -ne 0) { throw "Echec : $titre (code $code)" }
}

$excl = "(^|/)(\.git/|voix/)|\.zip$"
ExecBat "Rsync du jeu vers le bucket (-d : miroir)" `
  ("`"$GSUTIL`" -m rsync -d -r -x `"$excl`" `"$racine`" gs://$Bucket")

# Les Content-Type sont inferes par gsutil a l'upload (text/html, text/javascript,
# model/gltf+json...) : rien a corriger. On force juste no-cache sur index.html
# (le fichier qui bouge le plus entre deux redeploiements).
if (-not $EssaiABlanc) {
  Exec "Cache no-cache sur index.html" @("$GCLOUD","storage","objects","update",
       "gs://$Bucket/index.html","--cache-control=no-cache,max-age=0")
}

# ---- Verdict --------------------------------------------------------------
Write-Host ""
Write-Host "=== DEPLOIEMENT KOTOAGE TERMINE ==="
Write-Host "URL de test :      https://storage.googleapis.com/$Bucket/index.html"
Write-Host "  Chrome : ouvrir chrome://flags/#enable-webmcp-testing puis activer."
Write-Host "  ChatGPT : coller l'URL dans le navigateur integre de l'app."
Write-Host "Bucket a reperer pour le rapport : gs://$Bucket"