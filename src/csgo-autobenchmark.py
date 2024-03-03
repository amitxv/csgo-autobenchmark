import argparse
import csv
import ctypes
import logging
import os
import subprocess
import sys
import time
import traceback

from pynput.keyboard import Controller, Key

logger = logging.getLogger("CLI")


def aggregate(input_files: list[str], output_file: str) -> None:
    aggregated: list[str] = []

    for file in input_files:
        with open(file, encoding="utf-8") as input_file:
            lines = input_file.readlines()
            aggregated.extend(lines)

    with open(output_file, "a", encoding="utf-8") as file:
        column_names = aggregated[0]
        file.write(column_names)

        for line in aggregated:
            if line != column_names:
                file.write(line)


def app_latency(input_file: str, output_file: str) -> None:
    with open(input_file, encoding="utf-8") as file:
        contents: list[dict[str, str]] = list(csv.DictReader(file))

    # convert key names to lowercase because column names changed in a newer version of PresentMon
    for index, row in enumerate(contents):
        contents[index] = {key.lower(): value for key, value in row.items()}

    with open(output_file, "a", encoding="utf-8") as file:
        file.write("MsPCLatency\n")

        for i in range(1, len(contents)):
            ms_input_latency = (
                float(contents[i]["msbetweenpresents"])
                + float(contents[i]["msuntildisplayed"])
                - float(contents[i - 1]["msinpresentapi"])
            )

            file.write(f"{ms_input_latency:.3f}\n")


def parse_config(config_path: str) -> dict[str, str]:
    config: dict[str, str] = {}

    try:
        with open(config_path, encoding="utf-8") as file:
            for line in file:
                if line.startswith("//"):
                    continue

                stripped_line = line.strip("\n")
                setting, _, value = stripped_line.rpartition("=")

                if setting and value:
                    config[setting] = value
    finally:
        return config


def timer_resolution(enabled: bool) -> int:
    ntdll = ctypes.WinDLL("ntdll.dll")
    min_res, max_res, curr_res = ctypes.c_ulong(), ctypes.c_ulong(), ctypes.c_ulong()

    ntdll.NtQueryTimerResolution(
        ctypes.byref(min_res),
        ctypes.byref(max_res),
        ctypes.byref(curr_res),
    )

    return ntdll.NtSetTimerResolution(10000, int(enabled), ctypes.byref(curr_res))


def main() -> int:
    logging.basicConfig(format="[%(name)s] %(levelname)s: %(message)s", level=logging.INFO)

    version = "0.4.2"

    cfg = {
        "map": "1",
        "cache_trials": "1",
        "trials": "3",
        "skip_confirmation": "0",
        "output_path": f"captures\\csgo-autobenchmark-{time.strftime('%d%m%y%H%M%S')}",
    }  # default values

    windows_version_info = sys.getwindowsversion()
    # use 1.6.0 on Windows Server
    presentmon = f"PresentMon-{'1.9.0' if windows_version_info.major >= 10 and windows_version_info.product_type != 3 else '1.6.0'}-x64.exe"
    map_options = {
        1: {"map": "de_dust2", "record_duration": "40"},
        2: {"map": "de_cache", "record_duration": "45"},
    }

    print(
        f"csgo-autobenchmark Version {version} - GPLv3\nGitHub - https://github.com/amitxv\n",
    )

    if not ctypes.windll.shell32.IsUserAnAdmin():
        logger.error("administrator privileges required")
        return 1

    if getattr(sys, "frozen", False):
        os.chdir(os.path.dirname(sys.executable))
    elif __file__:
        os.chdir(os.path.dirname(__file__))

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--version",
        action="version",
        version=f"csgo-autobenchmark v{version}",
    )
    parser.add_argument(
        "--map",
        metavar="<map choice>",
        help="1 for de_dust2, 2 for de_cache",
        type=int,
    )
    parser.add_argument(
        "--cache-trials",
        metavar="<amount>",
        help="number of trials to execute to build cache",
        type=int,
    )
    parser.add_argument(
        "--trials",
        metavar="<amount>",
        help="number of trials to benchmark",
        type=int,
    )
    parser.add_argument(
        "--skip-confirmation",
        help="use this argument to skip start confirmation",
        action="store_const",
        const=1,
    )
    parser.add_argument(
        "--output-path",
        metavar="<path>",
        help="specify the full path to a folder to log CSVs to",
    )
    args = parser.parse_args()

    args_dict = vars(args)  # convert arguments to dict[str, Any]
    config_file = parse_config("config.txt")

    # load settings from config and arguments
    # note: arguments have a higher precedence
    for key in cfg:
        for _dict in (config_file, args_dict):
            if _dict.get(key) is not None:
                cfg[key] = str(_dict[key])

    if not os.path.exists(f"bin\\PresentMon\\{presentmon}"):
        logger.error("presentmon not found")
        return 1

    try:
        map_config = map_options[int(cfg["map"])]
        cs_map = map_config["map"]
        record_duration = int(map_config["record_duration"])
    except KeyError:
        logger.error("invalid map specified")
        return 1

    if int(cfg["trials"]) <= 0 or int(cfg["cache_trials"]) < 0:
        logger.error("invalid trials or cache trials specified")
        return 1

    estimated_time_sec: int = 43 + (int(cfg["cache_trials"]) + int(cfg["trials"])) * (record_duration + 15)
    estimated_time_min = estimated_time_sec / 60

    logger.info("estimated time: %d minutes approx", round(estimated_time_min))

    for key, value in cfg.items():
        logger.info("%s: %s", key, value)

    if not int(cfg["skip_confirmation"]):
        input("press enter to start benchmarking...")

    logger.info("starting in 5 Seconds (tab back into game)")
    time.sleep(5)

    try:
        os.makedirs(cfg["output_path"])
    except FileExistsError:
        logger.error("%s already exists", cfg["output_path"])
        return 1

    timer_resolution(enabled=True)
    keyboard = Controller()

    # everything beyond this point assumes the user is loaded to the menu screen as stated in the readme

    # open console (console must be bound to f5)
    keyboard.tap(Key.f5)
    time.sleep(1)

    # load map
    keyboard.type(f"map {cs_map}\n")

    logger.info("waiting for %s to load", cs_map)
    time.sleep(40)

    keyboard.tap(Key.f5)
    time.sleep(1)

    # load benchmark config
    keyboard.type("exec benchmark\n")
    time.sleep(1)

    if int(cfg["cache_trials"]) > 0:
        for trial in range(1, int(cfg["cache_trials"]) + 1):
            logger.info("cache trial: %d/%d", trial, int(cfg["cache_trials"]))

            keyboard.type("benchmark\n")
            time.sleep(record_duration + 15)

    for trial in range(1, int(cfg["trials"]) + 1):
        logger.info("recording trial: %d/%d", trial, int(cfg["trials"]))

        keyboard.type("benchmark\n")

        with subprocess.Popen(
            [
                f"bin\\PresentMon\\{presentmon}",
                "-stop_existing_session",
                "-no_top",
                "-delay",
                "5",
                "-timed",
                str(record_duration),
                "-process_name",
                "csgo.exe",
                "-output_file",
                f"{cfg['output_path']}\\Trial-{trial}.csv",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ) as process:
            time.sleep(record_duration + 15)
            process.kill()

        if not os.path.exists(f"{cfg['output_path']}\\Trial-{trial}.csv"):
            logger.error(
                "csv log unsuccessful, this may be due to a missing dependency or windows component",
            )
            return 1

    raw_csvs = [f"{cfg['output_path']}\\Trial-{trial}.csv" for trial in range(1, int(cfg["trials"]) + 1)]
    aggregate(raw_csvs, f"{cfg['output_path']}\\Aggregated.csv")
    app_latency(
        f"{cfg['output_path']}\\Aggregated.csv",
        f"{cfg['output_path']}\\MsPCLatency.csv",
    )

    logger.info("raw and aggregated CSVs located in: %s\n", cfg["output_path"])

    return 0


if __name__ == "__main__":
    __exit_code__ = 0
    try:
        __exit_code__ = main()
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception:
        print(traceback.format_exc())
        __exit_code__ = 1
    finally:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        process_array = (ctypes.c_uint * 1)()
        num_processes = kernel32.GetConsoleProcessList(process_array, 1)
        # only pause if script was ran by double-clicking
        if num_processes < 3:
            input("press enter to exit")

        sys.exit(__exit_code__)
