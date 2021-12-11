#!/bin/bash

cd $3

lines=$(wc -l ${1} | sed 's/ .*//g')

lines_per_file=`expr ${lines} / 20`

if [ ${lines_per_file} -eq 0 ]
then
    lines_per_file=${lines}
fi

split -d -l ${lines_per_file} $1 $1__part__

sed -i '1d' $1__part__"00"

for file in *__part__*

do

{

sort $file > sort_$file

} &

done

wait

sort -smu sort_* > $2

rm -f *__part__*

rm -f sort_*
