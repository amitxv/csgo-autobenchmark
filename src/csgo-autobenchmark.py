import time
import os
import subprocess
from pynput.keyboard import Controller, Key
import pandas

keyboard = Controller()


def log(msg: str) -> None:
    """Logs messages to the console with a timestamp"""
    print(f"[{time.strftime('%H:%M')}] CLI: {msg}")


def send_command(command: str) -> None:
    """Sends commands to the foreground window"""
    time.sleep(0.1)

    def keyboard_press(key):
        time.sleep(0.1)
        keyboard.press(key)
        keyboard.release(key)

    for char in command:
        keyboard_press(char)
    if command != "`":
        keyboard_press(Key.enter)


def main() -> None:
    """Main application logic"""
    subprocess_null = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}

    config = {}
    with open("config.txt", "r", encoding="UTF-8") as f:
        for line in f:
            if "//" not in line:
                line = line.strip("\n")
                setting, _equ, value = line.rpartition("=")
                if setting != "" and value != "":
                    config[setting] = value

    if int(config["map"]) == 1:
        cs_map = "de_dust2"
        duration = 40
    elif int(config["map"]) == 2:
        cs_map = "de_cache"
        duration = 45
    else:
        raise ValueError("invalid map in config")

    trials = int(config["trials"])
    cache_trials = int(config["cache_trials"])

    if trials <= 0 or cache_trials < 0:
        raise ValueError("invalid trials or cache_trials in config")

    skip_confirmation = int(config["skip_confirmation"])

    log(
        f"Estimated time: {(40 + ((duration + 15) * cache_trials)+ ((duration + 15) * trials))/60:.2f} min"
    )

    if not skip_confirmation:
        input("Press enter to start benchmarking...")
        log("Starting in 7 Seconds (tab back into game)")
        time.sleep(7)

    send_command("`")
    send_command(f"map {cs_map}")
    log(f"Waiting for {cs_map} to load")
    time.sleep(40)
    send_command("`")
    send_command("exec benchmark")

    if cache_trials > 0:
        for trial in range(1, cache_trials + 1):
            log(f"Cache Trial: {trial}/{cache_trials}")
            send_command("benchmark")
            time.sleep(duration + 15)

    output_path = f"captures\\csgo-autobenchmark-{time.strftime('%d%m%y%H%M%S')}"
    os.makedirs(output_path)

    for trial in range(1, trials + 1):
        log(f"Recording Trial: {trial}/{trials}")
        send_command("benchmark")

        try:
            # fmt: off
            subprocess.run([
                "bin\\PresentMon\\PresentMon.exe",
                "-stop_existing_session",
                "-no_top",
                "-verbose",
                "-delay", "5"
                "-timed", str(duration),
                "--terminate_after_timed",
                "-process_name", "csgo.exe",
                "-output_file", f"{output_path}\\Trial-{trial}.csv.csv",
                ], timeout=duration + 15, **subprocess_null, check=False)
            # fmt: on
        except subprocess.TimeoutExpired:
            pass

    CSVs = []
    for trial in range(1, trials + 1):
        CSV = f"{output_path}\\Trial-{trial}.csv"
        CSVs.append(pandas.read_csv(CSV))
        aggregated = pandas.concat(CSVs)
        aggregated.to_csv(f"{output_path}\\Aggregated.csv", index=False)

    log("Finished")
    log(f"Raw and aggregated CSVs located in: {output_path}\n")


if __name__ == "__main__":
    main()
