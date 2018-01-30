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

logging.basicConfig(level=logging.WARNING)

# create logger
log = logging.getLogger(__name__)

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

projects = jira.projects()
for project in projects:
    if hasattr(project, filter_names[0] ):
        project_category = getattr(project, filter_names[0])
        if len(filter_names) > 1:
            project_category_value = project_category._session[filter_names[1]]
        else:
            project_category_value = getattr(project, filter_names[0])

        if project_category_value == filter_value:
            jql = "project = %s AND %s" % (project.key, jira_conf['jql'])
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
                    print('%s: %s \t %s' % (issue.key, issue.fields.summary, issue.fields.customfield_10094))
                    if issue.fields.customfield_10094:
                        overall_story_points += float("%s" % issue.fields.customfield_10094)

print("Overall story points: %d" % overall_story_points)
