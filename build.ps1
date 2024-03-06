function main() {
    if (Test-Path ".\build\") {
        Remove-Item -Path ".\build\" -Recurse
    }

    $entryPoint = "..\..\csgo_autobenchmark\main.py"

    # create folder structure
    New-Item -ItemType Directory -Path ".\build\csgo-autobenchmark\"

    # pack executable
    New-Item -ItemType Directory -Path ".\build\pyinstaller\"
    Push-Location ".\build\pyinstaller\"
    pyinstaller $entryPoint --onefile --name csgo-autobenchmark
    Pop-Location

    # create final package
    Copy-Item ".\build\pyinstaller\dist\csgo-autobenchmark.exe" ".\build\csgo-autobenchmark\"
    Copy-Item ".\csgo_autobenchmark\bin\" ".\build\csgo-autobenchmark\" -Recurse
    Copy-Item ".\csgo_autobenchmark\prerequisites\" ".\build\csgo-autobenchmark\" -Recurse
    Copy-Item ".\csgo_autobenchmark\config.txt" ".\build\csgo-autobenchmark\"

    return 0
}

$_exitCode = main
Write-Host # new line
exit $_exitCode
