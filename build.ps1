function main() {
    # pack executable
    pyinstaller src\csgo-autobenchmark.py --onefile

    # create folder structure
    mkdir csgo-autobenchmark
    Move-Item dist\csgo-autobenchmark.exe csgo-autobenchmark
    Move-Item src\bin csgo-autobenchmark
    Move-Item src\prerequisites csgo-autobenchmark
    Move-Item src\config.txt csgo-autobenchmark

    return 0
}

$_exitCode = main
Write-Host # new line
exit $_exitCode
