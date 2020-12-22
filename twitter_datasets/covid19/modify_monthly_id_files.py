"""Solve import issue"""
import csv
import os
import sys
import argparse
from tqdm import tqdm
from pathlib import Path

current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root_dir = f"{current_file_dir}/../../"
sys.path.append(current_file_dir)
sys.path.append(project_root_dir)

DATA_ROOT = "./dataset"

def get_usc_monthly_files(month):
    month_output_file = f"{DATA_ROOT}/{month}.txt"
    outfile = open(month_output_file, "w")
    data_dir = f"{DATA_ROOT}/{month}"
    for path in Path(data_dir).iterdir():
        if path.name.endswith(".txt"):
            with open(path, "r") as infile:
                for line in infile:
                    outfile.writelines(line)
    outfile.close()


def ignore_lines_and_overwrite_file(file, ignore_lines):
    with open(file, "r") as infile:
        lines = infile.readlines()
    with open(file, "w") as outfile:
        line_ptr = 1
        for line in lines:
            if line_ptr > ignore_lines:
                outfile.writelines(line)
            line_ptr += 1


def get_panacealab_monthly_files(month):
    month_source_id_file = f"{DATA_ROOT}/{month}_source.txt"
    month_retweet_id_file = f"{DATA_ROOT}/{month}_retweets.txt"
    
    clean_files, full_files = [], []
    for path in Path(f"{DATA_ROOT}/{month}_panacealab").iterdir():
        path_name = path.name
        if path_name.endswith(".tsv"):
            if "_clean" in path_name:
                clean_files.append(path)
            else:
                full_files.append(path)
    
    # get source tweets
    print("get source tweets...")
    source_tids = set()
    source_outfile = open(month_source_id_file, "w")
    for clean_file in tqdm(clean_files):
        with open(clean_file, "r") as infile:
            tsv_reader = csv.DictReader(infile, delimiter="\t")
            for row in tsv_reader:
                if row["lang"] == "en":
                    tid = row["tweet_id"]
                    source_tids.add(tid)
                    source_outfile.writelines(f"{tid}\n")
    source_outfile.close()

    # get retweets
    print("get retweets...")
    retweet_outfile = open(month_retweet_id_file, "w")
    for full_file in tqdm(full_files):
        with open(full_file, "r") as infile:
            tsv_reader = csv.DictReader(infile, delimiter="\t")
            for row in tsv_reader:
                tid = row["tweet_id"]
                if tid not in source_tids and row["lang"] == "en":
                    retweet_outfile.writelines(f"{tid}\n")
    retweet_outfile.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--task", required=True, choices=["usc", "panacealab", "ignore"])
    parser.add_argument("-m", "--month", required=False, choices=[f"2020-{str(i).zfill(2)}" for i in range(1, 13)])
    parser.add_argument("-f", "--file", required=False)
    parser.add_argument("-i", "--ignore", required=False)
    args = parser.parse_args()
    
    if args.task == "usc":
        get_usc_monthly_files(args.month)
    if args.task == "panacealab":
        get_panacealab_monthly_files(args.month)
    if args.task == "ignore":
        ignore_lines_and_overwrite_file(args.file, int(args.ignore))
