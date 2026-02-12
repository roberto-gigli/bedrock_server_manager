param(
    [string]$InstallDir = "$env:USERPROFILE\bedrock_server_manager"
)

$ErrorActionPreference = "Stop"

function Ensure-Repo {
    if (Test-Path -LiteralPath $InstallDir) {
        if (Test-Path -LiteralPath (Join-Path $InstallDir ".git")) {
            Write-Host "Updating existing repo in $InstallDir..."
            Push-Location $InstallDir
            git pull --ff-only
            Pop-Location
            return
        }
        Write-Host "Directory exists but is not a git repo: $InstallDir"
        Write-Host "Remove it or choose a different -InstallDir."
        exit 1
    }

    if (Get-Command git -ErrorAction SilentlyContinue) {
        Write-Host "Cloning repo into $InstallDir..."
        git clone "https://github.com/roberto-gigli/bedrock_server_manager.git" $InstallDir
        return
    }

    Write-Host "Git not found, downloading ZIP..."
    $zipUrl = "https://github.com/roberto-gigli/bedrock_server_manager/archive/refs/heads/main.zip"
    $tmpZip = Join-Path $env:TEMP "bedrock_server_manager.zip"
    Invoke-WebRequest -Uri $zipUrl -OutFile $tmpZip
    Expand-Archive -LiteralPath $tmpZip -DestinationPath $env:TEMP -Force
    $extracted = Join-Path $env:TEMP "bedrock_server_manager-main"
    Move-Item -LiteralPath $extracted -Destination $InstallDir
    Remove-Item -LiteralPath $tmpZip -Force
}

function Add-ToPath {
    $current = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($null -eq $current) { $current = "" }

    $parts = $current.Split(";", [System.StringSplitOptions]::RemoveEmptyEntries)
    if ($parts -contains $InstallDir) {
        Write-Host "Path already contains $InstallDir"
        return
    }

    $newPath = if ($current.Trim()) { "$current;$InstallDir" } else { $InstallDir }
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    $env:Path = "$env:Path;$InstallDir"
    Write-Host "Added $InstallDir to user PATH. Restart your terminal to refresh."
}

Ensure-Repo
Add-ToPath
Write-Host "Done. You can run: python bedrock_server_manager.py"
