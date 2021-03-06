import json
import sys
import time

from tqdm import tqdm


class DOT_DICT(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as k:
            raise AttributeError(k)

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError as k:
            raise AttributeError(k)

    def __repr__(self):
        return "DOT_DICT(" + dict.__repr__(self) + ")"


def program_sleep(sec):
    trange = tqdm(range(sec), bar_format="sleeping for {n_fmt}/{total_fmt} seconds...", leave=False)
    for _ in trange:
        time.sleep(1)
    trange.close()
    print(f"Done sleeping! Slept {sec} seconds!")


def print_dict(d):
    print(json.dumps(d, indent=4, sort_keys=False))


def write_to_log(log_file, msg):
    with open(log_file, "a+") as outfile:
        outfile.writelines(f"{msg}\n")
