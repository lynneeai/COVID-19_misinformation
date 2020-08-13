"""Solve import issue"""
import os
import sys
from tqdm import tqdm
from pathlib import Path

current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root_dir = f"{current_file_dir}/../../"
sys.path.append(current_file_dir)
sys.path.append(project_root_dir)

DATA_ROOT = "./USC_dataset/"
data_dirs = [
    "2020-01",
    "2020-02",
    "2020-03",
    "2020-04",
    "2020-05",
    "2020-06",
    "2020-07",
]
data_dirs.reverse()

for data_dir in tqdm(data_dirs):
    month_output_file = f"{DATA_ROOT}/{data_dir}.txt"
    outfile = open(month_output_file, "w")
    data_dir = DATA_ROOT + data_dir
    for path in Path(data_dir).iterdir():
        if path.name.endswith(".txt"):
            with open(path, "r") as infile:
                for line in infile:
                    outfile.writelines(line)
    outfile.close()
