#!/bin/bash
echo "Run rsync of current directory to $1"
echo "Ignoring __pycache__/ logs/ *.db *.log *.DS_Store twitter_datasets/usc_covid19/USC_dataset/ .git/"

if [ "$1" = "moto" ];
then
    rsync -avP --exclude "__pycache__/" --exclude "logs/" --exclude "*.db" --exclude "*.log" --exclude "*.DS_Store" --exclude "twitter_datasets/covid19/dataset/" --exclude ".git/" ./ la2734@quake.rcs.columbia.edu:/moto/katt2/users/la2734/covid19_misinformation
fi

if [ "$1" = "hecate" ];
then
    rsync -avP --exclude "__pycache__/" --exclude "logs/" --exclude "*.db" --exclude "*.log" --exclude "*.DS_Store" --exclude "twitter_datasets/covid19/dataset/" --exclude ".git/" ./ lin.ai@hecate.cs.columbia.edu:/proj/afosr/covid19_misinformation
fi

if [ "$1" = "paka" ];
then
    rsync -avP --exclude "__pycache__/" --exclude "logs/" --exclude "*.db" --exclude "*.log" --exclude "*.DS_Store" --exclude "twitter_datasets/covid19/dataset/" --exclude ".git/" ./ lin.ai@paka.cs.columbia.edu:/proj/afosr/covid19_misinformation
fi