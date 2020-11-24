"""Solve import issue"""
import os
import sys
import argparse
from tqdm import tqdm
from pathlib import Path

current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root_dir = f"{current_file_dir}/../../"
sys.path.append(current_file_dir)
sys.path.append(project_root_dir)

DATA_ROOT = "./USC_dataset"

def combine_monthly_files(month):
    month_output_file = f"{DATA_ROOT}/{month}.txt"
    outfile = open(month_output_file, "w")
    data_dir = f"{DATA_ROOT}/{month}"
    for path in Path(data_dir).iterdir():
        if path.name.endswith(".txt"):
            with open(path, "r") as infile:
                for line in infile:
                    outfile.writelines(line)
    outfile.close()


def ignore_lines_and_overwrite_file(month, ignore_lines):
    month_id_file = f"{DATA_ROOT}/{month}.txt"
    with open(month_id_file, "r") as infile:
        lines = infile.readlines()
    with open(month_id_file, "w") as outfile:
        line_ptr = 1
        for line in lines:
            if line_ptr > ignore_lines:
                outfile.writelines(line)
            line_ptr += 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--task", required=True, choices=["combine", "ignore"])
    parser.add_argument("-m", "--month", required=True, choices=[f"2020-{str(i).zfill(2)}" for i in range(1, 9)])
    parser.add_argument("-i", "--ignore", required=False)
    args = parser.parse_args()
    
    if args.task == "combine":
        combine_monthly_files(args.month)
    if args.task == "ignore":
        ignore_lines_and_overwrite_file(args.month, int(args.ignore))