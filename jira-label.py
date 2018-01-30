#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from jira.client import JIRA
import logging
import sys

def connect_jira(log, jira_server, jira_user, jira_password):
    try:
        log.info("Connecting to JIRA: %s" % jira_server)
        jira_options = {'server': jira_server}
        jira = JIRA(options=jira_options, basic_auth=(jira_user, jira_password))
                                        # ^--- Note the tuple
        return jira
    except Exception,e:
        log.error("Failed to connect to JIRA: %s" % e)
        return None

# create logger
log = logging.getLogger(__name__)

# NOTE: You put your login details in the function call connect_jira(..) below!

# create a connection object, jc
jira = connect_jira(log, "", "", "")

jql = "project =  AND labels = "

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
       if hasattr(issue.fields, 'customfield_12085') and issue.fields.customfield_12085 is not None:
           if hasattr(issue.fields,'customfield_10094'):
               if issue.fields.customfield_10094 is None:
                   print('%s: %s - %s - %s' % (issue.key, issue.fields.summary, issue.fields.customfield_12085, issue.fields.customfield_10094))
#                   issue.update(fields={'customfield_10094': int('%d' % int(issue.fields.customfield_12085))})


