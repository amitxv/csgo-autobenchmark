## csgo-autobenchmark

CLI tool to automate the benchmark process in csgo using scripts from [csgo-benchmark](https://github.com/samisalreadytaken/csgo-benchmark).

Contact: https://twitter.com/amitxv

🐭 enable developer console in the game settings

🐱 bind the console hotkey to F12 by running ``bind F12 "toggleconsole"`` in the console

🐰 remove all launch options for csgo to avoid it interfering with the benchmark

🐶 do not have csgo installed on a HDD

The csgo scripts are property of @samisalreadytaken in which i do not claim ownership of.

## Usage

- Download and extract the latest release from the [releases tab](https://github.com/amitxv/csgo-autobenchmark/releases).

- From the ``prerequisites`` folder
    - move the ``csgo`` folder to ``\steamapps\common\Counter-Strike Global Offensive\``
    - move ``video.txt`` to ``\Steam\Userdata\???\730\local\cfg\``

- Launch csgo to the loading screen with the console closed.

- Run ``csgo-autobenchmark.exe`` through the command-line and press enter when ready. There is a 7 second timeout to allow you to tab back into the game to give csgo foreground priority.

- Do not touch your PC at all after after this stage until the estimated time is up.

---

Alternatively you can use this command to start the benchmark if you do not want to manually launch csgo. You must set ``skip_confirmation`` to 1 in the config so that you do not need to press enter to continue.
```
start steam://rungameid/730 && timeout -t 60 && csgo-autobenchmark.exe
```
