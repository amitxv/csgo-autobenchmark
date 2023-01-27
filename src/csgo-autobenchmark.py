import time
import os
import subprocess
import sys
import ctypes
from pynput.keyboard import Controller, Key

keyboard = Controller()
ntdll = ctypes.WinDLL("ntdll.dll")


def keyboard_press(key):
    time.sleep(0.1)
    keyboard.press(key)
    keyboard.release(key)


def send_command(command):
    time.sleep(0.1)
    for char in command:
        keyboard_press(char)
    keyboard_press(Key.enter)


def aggregate(files, output_file):
    aggregated = []
    for file in files:
        with open(file, "r", encoding="utf-8") as file:
            lines = file.readlines()
            aggregated.extend(lines)

    with open(output_file, "a", encoding="utf-8") as file:
        column_names = aggregated[0]
        file.write(column_names)

        for line in aggregated:
            if line != column_names:
                file.write(line)


def parse_config(config_path):
    config = {}
    with open(config_path, "r", encoding="utf-8") as file:
        for line in file:
            if line.startswith("//"):
                continue

            line = line.strip("\n")
            setting, _, value = line.rpartition("=")

            if setting and value:
                config[setting] = value

    return config


def timer_resolution(enabled):
    min_res = ctypes.c_ulong()
    max_res = ctypes.c_ulong()
    curr_res = ctypes.c_ulong()

    ntdll.NtQueryTimerResolution(ctypes.byref(min_res), ctypes.byref(max_res), ctypes.byref(curr_res))

    if max_res.value <= 10000 and ntdll.NtSetTimerResolution(10000, int(enabled), ctypes.byref(curr_res)) == 0:
        return 0
    return 1


def main():
    version = "0.3.3"
    stdnull = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    cfg = parse_config("config.txt")
    present_mon = "PresentMon-1.6.0-x64.exe"
    map_options = {1: ("de_dust2", 40), 2: ("de_cache", 45)}

    print(f"csgo-autobenchmark v{version}")
    print("GitHub - https://github.com/amitxv\n")

    if not ctypes.windll.shell32.IsUserAnAdmin():
        print("error: administrator privileges required")
        return

    if getattr(sys, "frozen", False):
        os.chdir(os.path.dirname(sys.executable))
    elif __file__:
        os.chdir(os.path.dirname(__file__))

    if sys.getwindowsversion().major >= 10:
        present_mon = "PresentMon-1.8.0-x64.exe"

    if not os.path.exists(f"bin\\PresentMon\\{present_mon}"):
        print("error: presentmon not found")
        return

    try:
        cs_map, duration = map_options[int(cfg["map"])]
    except KeyError:
        print("error: invalid map in config")
        return

    if int(cfg["trials"]) <= 0 or int(cfg["cache_trials"]) < 0:
        print("error: invalid trials or cache_trials in config")
        return

    estimated_time = (40 + ((duration + 15) * int(cfg["cache_trials"])) + ((duration + 15) * int(cfg["trials"]))) / 60
    print(f"info: estimated time: {round(estimated_time)} minutes approx")

    if not int(cfg["skip_confirmation"]):
        input("press enter to start benchmarking...")
    print("info: starting in 7 Seconds (tab back into game)")
    time.sleep(7)

    output_path = f"captures\\csgo-autobenchmark-{time.strftime('%d%m%y%H%M%S')}"
    os.makedirs(output_path)

    timer_resolution(True)

    keyboard_press(Key.f5)
    send_command(f"map {cs_map}")
    print(f"info: waiting for {cs_map} to load")
    time.sleep(40)
    keyboard_press(Key.f5)
    send_command("exec benchmark")

    if int(cfg["cache_trials"]) > 0:
        for trial in range(1, int(cfg["cache_trials"]) + 1):
            print(f"info: cache trial: {trial}/{int(cfg['cache_trials'])}")
            send_command("benchmark")
            time.sleep(duration + 15)

    for trial in range(1, int(cfg["trials"]) + 1):
        print(f"info: recording trial: {trial}/{int(cfg['trials'])}")
        send_command("benchmark")

        try:
            subprocess.run(
                [
                    f"bin\\PresentMon\\{present_mon}",
                    "-stop_existing_session",
                    "-no_top",
                    "-delay",
                    "5",
                    "-timed",
                    str(duration),
                    "-process_name",
                    "csgo.exe",
                    "-output_file",
                    f"{output_path}\\Trial-{trial}.csv",
                ],
                timeout=duration + 15,
                **stdnull,
                check=False,
            )
        except subprocess.TimeoutExpired:
            pass

        if not os.path.exists(f"{output_path}\\Trial-{trial}.csv"):
            print("error: csv log unsuccessful, this may be due to a missing dependency or windows component")
            return

    if int(cfg["trials"]) > 1:
        raw_csvs = []
        for trial in range(1, int(cfg["trials"]) + 1):
            raw_csvs.append(f"{output_path}\\Trial-{trial}.csv")

        aggregate(raw_csvs, f"{output_path}\\Aggregated.csv")

    print("info: finished")
    print(f"info: raw and aggregated CSVs located in: {output_path}\n")


if __name__ == "__main__":
    main()
