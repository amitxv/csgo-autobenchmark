from __future__ import annotations
import time
import os
import subprocess
import sys
import ctypes
from pynput.keyboard import Controller, Key

keyboard = Controller()
ntdll = ctypes.WinDLL("ntdll.dll")


def keyboard_press(key: str | Key) -> None:
    """keyboard keypress action"""
    time.sleep(0.1)
    keyboard.press(key)
    keyboard.release(key)


def send_command(command: str) -> None:
    """sends commands to the foreground window and presses enter"""
    time.sleep(0.1)
    for char in command:
        keyboard_press(char)
    keyboard_press(Key.enter)


def aggregate(files: list, output_file: str) -> None:
    """aggregates presentmon csv files"""
    aggregated = []
    for file in files:
        with open(file, "r", encoding="UTF-8") as csv_f:
            lines = csv_f.readlines()
            aggregated.extend(lines)

    with open(output_file, "a", encoding="UTF-8") as csv_f:
        column_names = aggregated[0]
        csv_f.write(column_names)

        for line in aggregated:
            if line != column_names:
                csv_f.write(line)


def parse_config(config_path: str) -> dict:
    """parse a simple configuration file and return a dict of the settings/values"""
    config = {}
    with open(config_path, "r", encoding="UTF-8") as config_file:
        for line in config_file:
            if "//" not in line:
                line = line.strip("\n")
                setting, _equ, value = line.rpartition("=")
                if setting != "" and value != "":
                    config[setting] = value
    return config


def timer_resolution(enabled: bool) -> int:
    """
    sets the kernel timer-resolution to 1000hz
    this function does not affect other processes on Windows 10 2004+
    """
    min_res = ctypes.c_ulong()
    max_res = ctypes.c_ulong()
    curr_res = ctypes.c_ulong()

    ntdll.NtQueryTimerResolution(ctypes.byref(min_res), ctypes.byref(max_res), ctypes.byref(curr_res))

    if max_res.value <= 10000 and ntdll.NtSetTimerResolution(10000, int(enabled), ctypes.byref(curr_res)) == 0:
        return 0
    return 1


def is_admin() -> bool:
    """check if script is ran with admin privileges"""
    return ctypes.windll.shell32.IsUserAnAdmin() != 0


def main() -> int:
    """cli entrypoint"""

    if not is_admin():
        print("error: administrator privileges required")
        return 1

    subprocess_null = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}

    # change directory to location of program
    program_path = ""
    if getattr(sys, "frozen", False):
        program_path = os.path.dirname(sys.executable)
    elif __file__:
        program_path = os.path.dirname(__file__)
    os.chdir(program_path)

    config = parse_config("config.txt")

    if not os.path.exists("bin\\PresentMon\\PresentMon.exe"):
        print("error: presentmon not found")
        return 1

    if int(config["map"]) == 1:
        cs_map = "de_dust2"
        duration = 40
    elif int(config["map"]) == 2:
        cs_map = "de_cache"
        duration = 45
    else:
        print("error: invalid map in config")
        return 1

    trials = int(config["trials"])
    cache_trials = int(config["cache_trials"])

    if trials <= 0 or cache_trials < 0:
        print("error: invalid trials or cache_trials in config")
        return 1

    skip_confirmation = bool(int(config["skip_confirmation"]))

    estimated_time = (40 + ((duration + 15) * cache_trials) + ((duration + 15) * trials)) / 60
    print(f"info: estimated time: {estimated_time:.2f} min")

    if not skip_confirmation:
        input("press enter to start benchmarking...")
    print("info: starting in 7 Seconds (tab back into game)")
    time.sleep(7)

    if timer_resolution(True) != 0:
        print("info: unable to set timer-resolution")

    keyboard_press(Key.f5)
    send_command(f"map {cs_map}")
    print(f"info: waiting for {cs_map} to load")
    time.sleep(40)
    keyboard_press(Key.f5)
    send_command("exec benchmark")

    if cache_trials > 0:
        for trial in range(1, cache_trials + 1):
            print(f"info: cache trial: {trial}/{cache_trials}")
            send_command("benchmark")
            time.sleep(duration + 15)

    output_path = f"captures\\csgo-autobenchmark-{time.strftime('%d%m%y%H%M%S')}"
    os.makedirs(output_path)

    for trial in range(1, trials + 1):
        print(f"info: recording trial: {trial}/{trials}")
        send_command("benchmark")

        try:
            subprocess.run([
                "bin\\PresentMon\\PresentMon.exe",
                "-stop_existing_session",
                "-no_top",
                "-delay", "5",
                "-timed", str(duration),
                "-process_name", "csgo.exe",
                "-output_file", f"{output_path}\\Trial-{trial}.csv"
                ], timeout=duration + 15, **subprocess_null, check=False)
        except subprocess.TimeoutExpired:
            pass

        if not os.path.exists(f"{output_path}\\Trial-{trial}.csv"):
            print("error: csv log unsuccessful, this is due to a missing dependency/ windows component")
            return 1

    if trials > 1:
        raw_csvs = []
        for trial in range(1, trials + 1):
            raw_csvs.append(f"{output_path}\\Trial-{trial}.csv")

        aggregate(raw_csvs, f"{output_path}\\Aggregated.csv")

    timer_resolution(False)
    print("info: finished")
    print(f"info: raw and aggregated CSVs located in: {output_path}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
