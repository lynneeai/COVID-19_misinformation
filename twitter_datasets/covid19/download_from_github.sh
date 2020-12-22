#!/bin/bash

month=$1
folder=$2

cd $folder

for ((i=1;i<=9;i++))
do  
    if (($month < 10))
    then
        date="2020-0$month-0$i"
    else
        date="2020-$month-0$i"
    fi
    echo "downloading for $date"
    curl -O -L "https://github.com/thepanacealab/covid19_twitter/raw/master/dailies/$date/$date-dataset.tsv.gz"
    curl -O -L "https://github.com/thepanacealab/covid19_twitter/raw/master/dailies/$date/{$date}_clean-dataset.tsv.gz"
done

for ((i=10;i<=28;i++))
do 
    if (($month < 10))
    then
        date="2020-0$month-$i"
    else
        date="2020-$month-$i"
    fi
    echo "downloading for $date"
    curl -O -L "https://github.com/thepanacealab/covid19_twitter/raw/master/dailies/$date/$date-dataset.tsv.gz"
    curl -O -L "https://github.com/thepanacealab/covid19_twitter/raw/master/dailies/$date/{$date}_clean-dataset.tsv.gz"
done

if (($month!=2))
then 
    for ((i=29;i<=30;i++))
    do 
        if (($month < 10))
        then
            date="2020-0$month-$i"
        else
            date="2020-$month-$i"
        fi
        echo "downloading for $date"
        curl -O -L "https://github.com/thepanacealab/covid19_twitter/raw/master/dailies/$date/$date-dataset.tsv.gz"
        curl -O -L "https://github.com/thepanacealab/covid19_twitter/raw/master/dailies/$date/{$date}_clean-dataset.tsv.gz"
    done
fi

if (($month==1 || $month==3 || $month==5 || $month==7 || $month==8 || $month==10 || $month==12))
then
    if (($month < 10))
    then
        date="2020-0$month-31"
    else
        date="2020-$month-31"
    fi
    echo "downloading for $date"
    curl -O -L "https://github.com/thepanacealab/covid19_twitter/raw/master/dailies/$date/$date-dataset.tsv.gz"
    curl -O -L "https://github.com/thepanacealab/covid19_twitter/raw/master/dailies/$date/{$date}_clean-dataset.tsv.gz"
fi