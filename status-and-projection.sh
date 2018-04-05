#!/bin/bash
#
# Status reporting wrapper script.
#
# Quick and dirty tool to process a bunch of yaml and plot files where the 
# plot file has two columns, the done and the not done. This tool processes
# all the yaml files given as file mask and calculates the percentages of
# the two columns.
# 
# For example with this plot data:
#  0	0	0
#   2018-03-21	262.0	11.0
#   2018-03-28	241.0	32.0
# 
# the script will look up the title in the yaml file and print 13.27%

RESULT="\e[34mEpic,Status (%),Ready by\e[0m"
NEWLINE='\n'
DELIMITER=','
for f in $*
do 
    # Get the feature from the yaml file
    ISSUE=$(grep filter_title $f|sed -e "s/    filter_title: //"|xargs)
    # Run the JIRA tool with the yaml file
    ./jira-tool.py -c $f || exit 1 
    # Get the last value of the table. This is the latest status.
    STATUS=$(egrep "^[0-9]{4,}" ${ISSUE// /_}*plot|tail -1)
    # Get the date where the project was started
    START_DATE=$(egrep "^[0-9]{4,}" ${ISSUE// /_}*plot|head -1|xargs echo|cut -f1 -d" ")
    # get the date of the last status
    DATE=$(echo $STATUS | cut -f1 -d" ")
    OPEN_ISSUES=$(echo $STATUS | cut -f2 -d" ")
    DONE_ISSUES=$(echo $STATUS | cut -f3 -d" ")
    # Calucalate the percentage of the done points
    PERCENT=$(echo "($DONE_ISSUES/($OPEN_ISSUES+$DONE_ISSUES))*100"|bc -l|sed -e "s/\(\.[0-9][0-9]\).*/\1/g")
    NOW=$(date +%Y-%m-%d)
    if [ "$PERCENT" != "0" ]; then
        # Calculate the projected date of when the feature will be ready
        PAST_SECONDS=$(echo $(date --date="$NOW" +%s) - $(date --date="$START_DATE" +%s)|bc -l)
        START_DATE_SECOND=$(date --date="$START_DATE" +%s)
        PROJECTION_SECOND=$(echo "$START_DATE_SECOND+(($PAST_SECONDS/$PERCENT)*100)"|bc -l)
        PROJECTION_DATE=$(date -d @$PROJECTION_SECOND +%Y-%m-%d)
    else
        PROJECTION_DATE="Unknown"
    fi
    RESULT=$RESULT$NEWLINE$ISSUE$DELIMITER$PERCENT$DELIMITER$PROJECTION_DATE
done
echo -e $RESULT
