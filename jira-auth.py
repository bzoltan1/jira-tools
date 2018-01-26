#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from jira.client import JIRA
import sys
import yaml
import logging

config = yaml.safe_load(open("./jira-config.yaml"))

# function to connect JIRA
def connect_jira(log, jira_server, jira_user, jira_password):
    try:
        log.info("Connecting to JIRA: %s" % jira_server)
        jira_options = {'server': jira_server}
        jira = JIRA(options=jira_options, basic_auth=(jira_user, jira_password))
        return jira
    except Exception,e:
        log.error("Failed to connect to JIRA: %s" % e)
        return None

# create logger
log = logging.getLogger(__name__)

jira = connect_jira(log, config['server']['address'], config['server']['username'], config['server']['password'])

projects = jira.projects()
for v in projects:
    if hasattr(v, 'projectCategory'):
        category = v.projectCategory
        category_name = category._session['name']
        if category_name == config['category_name']:
            jql = "project = %s AND issuetype = Defect" % (v.key)
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
                    print('%s: %s' % (issue.key, issue.fields.summary))

