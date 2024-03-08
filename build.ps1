function Is-Admin() {
    $currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function main() {
    if (-not (Is-Admin)) {
        Write-Host "error: administrator privileges required"
        return 1
    }

    if (Test-Path ".\build\") {
        Remove-Item -Path ".\build\" -Recurse -Force
    }

    mkdir ".\build\"

    # entrypoint relative to .\build\pyinstaller\
    $entryPoint = "..\..\csgo_autobenchmark\main.py"

    # create folder structure
    mkdir ".\build\csgo-autobenchmark\"

    # pack executable
    mkdir ".\build\pyinstaller\"
    Push-Location ".\build\pyinstaller\"
    pyinstaller $entryPoint --onefile --name csgo-autobenchmark
    Pop-Location

    # create final package
    Copy-Item ".\build\pyinstaller\dist\csgo-autobenchmark.exe" ".\build\csgo-autobenchmark\"
    Copy-Item ".\csgo_autobenchmark\bin\" ".\build\csgo-autobenchmark\" -Recurse
    Copy-Item ".\csgo_autobenchmark\config.txt" ".\build\csgo-autobenchmark\"
    Copy-Item ".\csgo_autobenchmark\video.txt" ".\build\csgo-autobenchmark\"

    return 0
}

$_exitCode = main
Write-Host # new line
exit $_exitCode
