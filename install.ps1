param(
    [string]$InstallDir = (Get-Location).Path
)

$ErrorActionPreference = "Stop"

function Test-IsEmptyDir {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        return $true
    }

    $items = Get-ChildItem -LiteralPath $Path -Force
    return $items.Count -eq 0
}

function Test-LooksLikeRepo {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    return (Test-Path -LiteralPath (Join-Path $Path "bedrock_server_manager.py")) -and
    (Test-Path -LiteralPath (Join-Path $Path "README.md"))
}

function Ensure-Repo {
    $useZip = $false
    if (Test-Path -LiteralPath $InstallDir) {
        if (Test-Path -LiteralPath (Join-Path $InstallDir ".git")) {
            Write-Host "Updating existing repo in $InstallDir..."
            Push-Location $InstallDir
            git pull --ff-only
            Pop-Location
            return
        }
        if (-not (Test-IsEmptyDir -Path $InstallDir)) {
            $useZip = $true
        }
    }

    if (-not $useZip -and (Get-Command git -ErrorAction SilentlyContinue)) {
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
    if (Test-Path -LiteralPath $InstallDir) {
        Get-ChildItem -LiteralPath $extracted -Force | Move-Item -Destination $InstallDir
        Remove-Item -LiteralPath $extracted -Force -Recurse
    }
    else {
        Move-Item -LiteralPath $extracted -Destination $InstallDir
    }
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

function Ensure-Executable {
    $targets = @(
        (Join-Path $InstallDir "bedrock_server_manager.sh"),
        (Join-Path $InstallDir "bedrock_server_manager.bat")
    )

    $chmod = Get-Command chmod -ErrorAction SilentlyContinue
    if ($null -ne $chmod) {
        foreach ($target in $targets) {
            if (Test-Path -LiteralPath $target) {
                chmod +x $target
            }
        }
        return
    }

    $icacls = Get-Command icacls -ErrorAction SilentlyContinue
    if ($null -ne $icacls) {
        foreach ($target in $targets) {
            if (Test-Path -LiteralPath $target) {
                icacls $target /grant "$env:USERNAME:(RX)" | Out-Null
            }
        }
    }
}

Ensure-Repo
Ensure-Executable
Add-ToPath
Write-Host "Done. You can run: bedrock_server_manager"
