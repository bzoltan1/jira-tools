#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import argparse
from argparse import RawTextHelpFormatter
import urllib2
from jira.client import JIRA
from os.path import isfile
import yaml
import logging
import sys
import datetime
from datetime import timedelta, date
import subprocess
import os
import re

plot = """
set title "BURNDOWN"
set xtics nomirror rotate by -45
set style data histogram
set grid ytics
set border 1
set style fill solid 1.00 border lt -1
set style data histograms
set xtics border scale 1,0 nomirror autojustify norangelimit
set key off auto columnheader
set yrange [0:*]
set linetype 1 lc rgb '#183693'
set terminal png font "/usr/share/fonts/truetype/freefont/FreeSans.ttf" 12 size 1024,768
set output "PNG"
$dataset << EOD
DATA
EOD
plot $dataset  using 2:xtic(1) with histogram, $dataset using 0:($2):2 with labels offset 1,1 
"""

logging.basicConfig(level=logging.INFO)

# create logger
log = logging.getLogger(__name__)

def gnuplot(data):
    try:
        gnuplot_process = subprocess.Popen(["gnuplot"],
                                           stdin=subprocess.PIPE,
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE)
    except OSError as e:
       return False, "Could not execute gnuplot ({0}): {1}".format(e.errno, e.strerror)
    gnuplot_process.stdin.write("%s" % data)
    stdout_value, stderr_value = gnuplot_process.communicate()
    if stderr_value:
        return False, stderr_value.decode("utf-8")
    return True, 0



# function to check if yaml file is valid
def check_valid_yaml_file(value):
    global jira_conf    
    if not isfile(value):
        raise argparse.ArgumentTypeError("%s does not exist" % value)
    try:
        jira_conf=yaml.safe_load(open(value))
    except:
        raise argparse.ArgumentTypeError('Can not parse yaml file: %s' % value)
    return value


# function to check if JIRA address is valid
def check_jira_address(value):
    try:
        urllib2.urlopen(value)
    except urllib2.HTTPError, e:
        raise argparse.ArgumentTypeError("HTTP Error: %s" % e.code)
    except urllib2.URLError, e:
        raise argparse.ArgumentTypeError("URL Error: %s" % e.args)
    log.info("Valid JIRA server: %s" % value)
    return value

# function to connect JIRA
def connect_jira(log, server):
    try:
        log.info("Connecting to JIRA: %s" % server['address'])
        jira_options = {'server': server['address']}
        jira = JIRA(options=jira_options, basic_auth=(server['username'], server['password']))
        return jira
    except Exception,e:
        log.error("Failed to connect to JIRA: %s" % e)
        return None


epilog_text = "CREDENTIAL_FILE:\n" + \
              "  In case the tool is used in a scripted mode the JIRA address and credentals can be used form the jira_conf.yaml file\n"


parser = argparse.ArgumentParser(description="JIRA helper tool",
                                 epilog=epilog_text,
                                 formatter_class=RawTextHelpFormatter)

parser.add_argument('-a',
                    '--address',
                    action="store",
                    default="https://jira.atlassian.com",
                    type=check_jira_address)

parser.add_argument('-u',
                    '--user_name',
                    action="store",
                    default="")

parser.add_argument('-p',
                    '--password',
                    action='store',
                    default='')

parser.add_argument('--jql',
                    dest='store',
                    action='store_true')

parser.add_argument('-c',
                    '--jira_conf_file',
                    dest='jira_conf_file',
                    type = check_valid_yaml_file,
                    default=None, 
                    required=False)

options = parser.parse_args()

jira = connect_jira(log, jira_conf['server'])

overall_story_points = 0

filter_name = jira_conf['filter']['filter_name']
filter_value = jira_conf['filter']['filter_value']
filter_names = filter_name.split(".")
summing = jira_conf['summing']['field']


if 'date' in jira_conf:
    start = jira_conf['date']['start']
    stop = jira_conf['date']['stop']
    delta = jira_conf['date']['delta']
else:
    start = stop = datetime.datetime.now().strftime("%Y/%m/%d")
    delta = 1

start_date = datetime.datetime.strptime('%s' % start, '%Y/%m/%d')
end_date = datetime.datetime.strptime('%s' % stop, '%Y/%m/%d')

plot = re.sub(r"BURNDOWN","%s" % filter_value, plot)
plot = re.sub(r"PNG","%s_%s-%s.png" % (re.sub(" ","_",filter_value), re.sub("/","-",start),re.sub("/","-",stop)), plot)

projects = jira.projects()
date = start_date
data_table=""
while date <= end_date:
    overall_story_points=0
    for project in projects:
        if hasattr(project, filter_names[0] ):
            project_category = getattr(project, filter_names[0])
            if len(filter_names) > 1:
                project_category_value = project_category._session[filter_names[1]]
            else:
                project_category_value = getattr(project, filter_names[0])

            if project_category_value == filter_value:
                jql = "project = %s AND %s on (\"%s\")" % (project.key, jira_conf['jql'], date.strftime("%Y/%m/%d"))
                log.info(jql)
                block_size = 50
                block_num = 0
                while True:
                    start_idx = block_num*block_size
                    issues = jira.search_issues(jql, start_idx, block_size)
                    if len(issues) == 0:
                        # Retrieve issues until there are no more to come
                       break
                    block_num += 1
                    for issue in issues:
                        log.info("%s: %s \t %s" % (issue.key, issue.fields.summary, getattr(issue.fields, summing)))
                        if hasattr(issue.fields, summing) and (getattr(issue.fields, summing)):
                            overall_story_points += float("%s" % getattr(issue.fields, summing))
    data_table+=("%s\t%d\n" % (date.strftime("%Y-%m-%d"), overall_story_points))
    log.info("%s\t%d\t0" % (date.strftime("%Y-%m-%d"), overall_story_points))
    date += datetime.timedelta(delta)
plot = re.sub(r"DATA","%s" % data_table, plot)
gnuplot(plot)

