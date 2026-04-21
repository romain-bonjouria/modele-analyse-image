$ErrorActionPreference = "Stop"

function Add-ToUserPathIfMissing([string]$directory) {
    if (!(Test-Path $directory)) { return }
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ([string]::IsNullOrWhiteSpace($userPath)) {
        [Environment]::SetEnvironmentVariable("Path", $directory, "User")
        $env:Path = "$env:Path;$directory"
        return
    }

    $segments = $userPath.Split(';') | ForEach-Object { $_.Trim() }
    if ($segments -notcontains $directory) {
        [Environment]::SetEnvironmentVariable("Path", "$userPath;$directory", "User")
        $env:Path = "$env:Path;$directory"
    }
}

function Resolve-OllamaExe {
    $candidates = @(
        "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe",
        "C:\Program Files\Ollama\ollama.exe"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    return $null
}

function Ensure-OllamaInstalled {
    $ollamaExe = Resolve-OllamaExe
    if ($ollamaExe) { return $ollamaExe }

    Write-Host "Ollama absent. Installation via winget..."
    winget install --id Ollama.Ollama -e --silent --accept-package-agreements --accept-source-agreements

    $ollamaExe = Resolve-OllamaExe
    if (-not $ollamaExe) {
        throw "Installation Ollama échouée."
    }

    return $ollamaExe
}

Write-Host "[1/4] Vérification d'Ollama"
$ollamaExe = Ensure-OllamaInstalled
Add-ToUserPathIfMissing (Split-Path $ollamaExe)

Write-Host "[2/4] Vérification version Ollama"
& $ollamaExe --version

Write-Host "[3/4] Téléchargement des modèles requis"
& $ollamaExe pull llama3.1
& $ollamaExe pull nomic-embed-text

Write-Host "[4/4] Lancement de l'application"
$legacyOneFileExe = Join-Path $PSScriptRoot "..\dist\RagClientApp.exe"
if (Test-Path $legacyOneFileExe) {
    Write-Warning "Ancien binaire onefile détecté ($legacyOneFileExe). Utilisez le build onedir: dist\\RagClientApp\\RagClientApp.exe"
}
$appExeCandidates = @(
    (Join-Path $PSScriptRoot "..\dist\RagClientApp\RagClientApp.exe")
)
$appExe = $null
foreach ($candidate in $appExeCandidates) {
    if (Test-Path $candidate) {
        $appExe = $candidate
        break
    }
}
if ([string]::IsNullOrWhiteSpace($appExe)) {
    throw "Application introuvable dans dist. Construisez l'exécutable via packaging/build_windows_exe.ps1"
}

try {
    Unblock-File -Path $appExe -ErrorAction SilentlyContinue
    $proc = Start-Process -FilePath $appExe -PassThru -ErrorAction Stop
    Start-Sleep -Seconds 2
    if ($proc.HasExited) {
        Write-Warning "L'application s'est fermée juste après lancement (exit code: $($proc.ExitCode))."
        Write-Warning "Pour voir l'erreur complète, lancez manuellement:"
        Write-Warning "powershell -NoExit -Command `"& '$appExe'`""
    } else {
        Write-Host "Installation client terminée."
    }
} catch {
    Write-Warning "Impossible de lancer automatiquement l'application: $($_.Exception.Message)"
    Write-Warning "Ouvrez manuellement: $appExe"
    Write-Warning "Si Windows SmartScreen bloque, cliquez 'Informations complémentaires' puis 'Exécuter quand même'."
}
