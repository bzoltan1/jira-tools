#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Copyright 2018 Zoltán Balogh.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; version 2.1.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Author: Zoltán Balogh <zoltan@bakter.hu>

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
set terminal png font "/usr/share/fonts/truetype/freefont/FreeSans.ttf" \
12 size 1024,768
set output "PNG"
$dataset << EOD
HEADER
DATA
EOD
PLOTLINE
"""


def gnuplot(data):
    try:
        gnuplot_process = subprocess.Popen(["gnuplot"],
                                           stdin=subprocess.PIPE,
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE)
    except OSError as e:
        return False, "Could not execute gnuplot ({0}): {1}".format(e.errno,
                                                                    e.strerror)
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
        jira_conf = yaml.safe_load(open(value))
    except yaml.YAMLError:
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
        jira = JIRA(options=jira_options, basic_auth=(server['username'],
                                                      server['password']))
        return jira
    except Exception, e:
        log.error("Failed to connect to JIRA: %s" % e)
        return None


epilog_text = "CREDENTIAL_FILE:\n" + \
              "  In case the tool is used in a scripted mode the JIRA " + \
              "address and credentals can be used form the " + \
              "jira_conf.yaml file\n"
log = logging.getLogger(__name__)
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
                    type=check_valid_yaml_file,
                    default=None,
                    required=False)
parser.add_argument('-v',
                    '--verbose',
                    dest='verbose',
                    default=False,
                    action='store_true')
options = parser.parse_args()
if options.verbose:
    logging.basicConfig(level=logging.INFO)
else:
    logging.basicConfig(level=logging.WARNING)
jira = connect_jira(log, jira_conf['server'])
sum = 0
jql_commands = jira_conf['jql_commands']
filter_name = jira_conf['filter']['filter_name']
filter_value = jira_conf['filter']['filter_value']
filter_names = filter_name.split(".")
filter_title = jira_conf['filter']['filter_title']
summing = jira_conf['summing']['field']
if 'date' in jira_conf:
    start = jira_conf['date']['start']
    if 'stop' in jira_conf['date']:
        stop = jira_conf['date']['stop']
    else:
        stop = datetime.datetime.now().strftime("%Y/%m/%d")
    delta = jira_conf['date']['delta']
else:
    start = stop = datetime.datetime.now().strftime("%Y/%m/%d")
    delta = 1
start_date = datetime.datetime.strptime('%s' % start, '%Y/%m/%d')
end_date = datetime.datetime.strptime('%s' % stop, '%Y/%m/%d')
plot = re.sub(r"BURNDOWN", "%s" % filter_title, plot)
plot = re.sub(r"PNG", "%s_%s-%s.png" % (re.sub(" ", "_", filter_title),
              re.sub("/", "-", start),
              re.sub("/", "-", stop)),
              plot)
plotfile = "%s_%s-%s.plot" % (re.sub(" ", "_", filter_title),
                              re.sub("/", "-", start),
                              re.sub("/", "-", stop))
dataline = [0 for x in range(len(jql_commands))]
plot = re.sub(r"HEADER", "0\t%s" % '\t'.join(str(e) for e in dataline), plot)
projects = jira.projects()
date = start_date
data_table = ""
plotline = "plot "
p = [["+0"],
     ["+0", "+0.24"],
     ["-0.1", "+0.1", "+0.3"],
     ["-0.16", "+0.00i", "+0.16", "+0.32"],
     ["-0.23", "-0.08", "+0.07", "+0.23", "+0.38"],
     ["-0.26", "-0.13", "+0.00", "+0.13", "+0.26", "+0.39"],
     ["-0.27", "-0.16", "-0.05", "+0.06", "+0.17", "+0.28", "+0.39"],
     ["-0.30", "-0.19", "-0.10", "+0.00", "+0.11", "+0.21", "+0.30", "+0.40"]]

if len(jql_commands) > 8:
    print("Do not use more than 8 jql or add the label positioning data " +
          "to the pos array")
    sys.exit(1)

for idx, commands in enumerate(jql_commands):
    plotline += ("\\\n\t$dataset  using " +
                 "%d:xtic(1) with histogram, " % (idx+2) +
                 "\\\n\t$dataset using  " +
                 "($0%s)" % p[len(jql_commands)-1][idx] +
                 ":($%d):(stringcolumn(%d)) " % (idx+2, idx+2) +
                 "w labels offset 0,1")
    if (idx != len(jql_commands)-1):
        plotline += (",")

while (date <= end_date):
    dataline = [0 for x in range(len(jql_commands))]
    sum = 0
    for project in projects:
        if hasattr(project, filter_names[0]):
            project_category = getattr(project, filter_names[0])
            if len(filter_names) > 1:
                project_category_value = project_category._session[filter_names[1]]
            else:
                project_category_value = getattr(project, filter_names[0])

            if re.search(project_category_value, filter_value):
                for idx, jql_command in enumerate(jql_commands):
                    jql = "project = %s AND %s" % (project.key, jql_command)
                    jql = re.sub(r"%DATE%",
                                 "\"%s\"" % (date.strftime("%Y/%m/%d")),
                                 jql)
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
                            if summing:
                                log.info("%s: %s - %s" % (issue.key,
                                                          issue.fields.summary,
                                                          getattr(issue.fields,
                                                                  summing)))
                                if hasattr(issue.fields, summing) and (getattr(issue.fields, summing)):
                                    sum += float("%s" % getattr(issue.fields, summing))
                                    dataline[idx] += float("%s" % getattr(issue.fields, summing))
                            else:
                                log.info("%s: %s" % (issue.key, issue.fields.summary))
                                sum += 1
                                dataline[idx] += 1
    data_table += ("%s\t%s\n" % (date.strftime("%Y-%m-%d"), '\t'.join(str(e) for e in dataline)))
    log.info("%s\t%d" % (date.strftime("%Y-%m-%d"), sum))
    if date < end_date:
        if ((date + datetime.timedelta(delta)) > end_date):
            date = end_date
        else:
            date += datetime.timedelta(delta)
    else:
        break
plot = re.sub(r"DATA", "%s" % data_table, plot)
plot = re.sub(r"PLOTLINE", "%s" % plotline, plot)
gnuplot(plot)
file = open(plotfile, "w")
file.write(plot)
file.close()
