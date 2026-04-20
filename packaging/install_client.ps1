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
$appExe = Join-Path $PSScriptRoot "..\dist\RagClientApp.exe"
if (!(Test-Path $appExe)) {
    throw "Application introuvable: $appExe. Construisez l'exécutable via packaging/build_windows_exe.ps1"
}

Start-Process -FilePath $appExe
Write-Host "Installation client terminée."
