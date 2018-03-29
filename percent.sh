#!/bin/bash

# Quick and dirty tool to process a bunch of yaml and plot files where the 
# plot file has two columns, the done and the not done. This tool processes
# all the yaml files given as file mask and calculates the percentages of
# the two columns.

# For example with this plot data:
#  0	0	0
#   2018-03-21	262.0	11.0
#   2018-03-28	241.0	32.0
# 
# the script will look up the title in the yaml file and print 13.27%

for f in $*
do 
    ISSUE=$(grep filter_title $f|sed -e "s/    filter_title: //"|xargs)
    jira-full.py -c $f 
    STATUS=$(egrep "^[0-9]{4,}" ${ISSUE// /_}*plot|tail -1)
    DATE=$(echo $STATUS | cut -f1 -d" ")
    OPEN_ISSUES=$(echo $STATUS | cut -f2 -d" ")
    DONE_ISSUES=$(echo $STATUS | cut -f3 -d" ")
    if [ "$OPEN_ISSUES" != "0" ]; then
        PERCENT=$(echo "($DONE_ISSUES/$OPEN_ISSUES)*100"|bc -l|sed -e "s/\(\.[0-9][0-9]\).*/\1%/g")
    else
        PERCENT="100%"
    fi
    echo -e $ISSUE '\t' $PERCENT
done
