function Is-Admin() {
    $currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function main() {
    if (-not (Is-Admin)) {
        Write-Host "error: administrator privileges required"
        return 1
    }

    $urls = @{
        "presentmon_1.6.0"  = "https://github.com/GameTechDev/PresentMon/releases/download/v1.6.0/PresentMon-1.6.0-x64.exe"
        "presentmon_latest" = "https://github.com/GameTechDev/PresentMon/releases/download/v1.10.0/PresentMon-1.10.0-x64.exe"
    }

    if (Test-Path ".\csgo_autobenchmark\bin\") {
        Remove-Item -Path ".\csgo_autobenchmark\bin\" -Recurse -Force
    }

    # create bin folder
    mkdir ".\csgo_autobenchmark\bin\"

    # ================
    # Setup PresentMon
    # ================

    mkdir ".\csgo_autobenchmark\bin\PresentMon"

    Invoke-WebRequest $urls["presentmon_1.6.0"] -OutFile ".\csgo_autobenchmark\bin\PresentMon\PresentMon-1.6.0-x64.exe"
    Invoke-WebRequest $urls["presentmon_latest"] -OutFile ".\csgo_autobenchmark\bin\PresentMon\PresentMon-1.10.0-x64.exe"

    return 0
}

$_exitCode = main
Write-Host # new line
exit $_exitCode
