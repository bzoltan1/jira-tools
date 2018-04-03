# JIRA data mining and processing tool

The goal of this project is to provide CLI tools to access JIRA via REST API and do calculations, estimations and projections based on the data retrieved.

## Requirements

* GNU/Linux
* Python 2.7+
* gnuplot
* Python library for interacting with JIRA via REST APIs - https://github.com/pycontribs/jira
* YAML parser and emitter for Python (python-yaml package or PyYAML from pip )

## 1) Main tool
    jira-tool.py -c [configuration file] [-v]

Looks up the JIRA issues by a jql command via jira's REST API and sums up the story points (or any other values in the issue record).
The script is configured with yaml files. 
The tool outputs a gnuplot data file (.plot) and the .png file created from that.

### Example for input yaml file:
    server:
        address: [URL]
        username:[ID]
        password: [PWD]
    filter:
        filter_name: [FILTER_FIELD]
        filter_value: [FILTER_VALUE]
    date:
        start: [START_DATE]
        stop:[STOP_DATE]
        delta: [DAYS]
    summing:
        field: []
    jql_commands:
        -
        -

* The URL of the server should be the JIRA instance the tool has access. For example  http://jira.company.com:8080/

* The ID/PWD are the credentials to the server. It is good to use dedicated credentials instead of personal.

* The filter section is to define what projects the tool should look up in the JIRA. The FILTER\_FIELD is the field identifier in the JIRA project records. For example if the tool should work on projects with projectCategory.name field where the value is "My Umbrella projects" then the filter name and value should be set to these values. If the tool is used on a single project then the FILTER\_FIELD should be 'name' and the FILTER VALUE should be the 'MyProject'

* The date section defines the time window the tool is used. The current date is used when the stop field is not used.

* The summing section is to configure what values to use to do statistics. The simplest case is when the tool is used to count defects or bugs. In that use case the field should be False and the tool will simple count the issues. More interesting case is when story points or other values are searched and summed up. In that case it is possible to use customfield_XXXXX where the field holds the numerical value.

* The jql_command list can be a list of jql commands executed for the pre-filetered projects. Each command will be represented by a column in the result data file and a histogram  in the png outpout. The list can have maximum 8 commands.

The jira-tool.py expects the yaml configuration file as the parameter of the -c option.

The optional -v parameter will make the tool verbose. The logs will contain the exact jql commands executed and the list if issues each command returns.

The tool creates a .plot file with the result data. This plot file can be manually modified and the png file can be manually re-created by gnuplot tool.

## 2) Wrapper tool
    status-and-projection.sh [YAML FILES]

A bash script what wraps around the jira-tool.py and calculates the readiness and projected delivery date of the epics.
This tool is usable when the there are several yaml files each for a different JIRA epic and where the jql commands in the yaml files return are done/open.
For example:

    jql_commands:
       - status was not in (Closed, "Won't Do", Resolved) on %DATE% AND "Epic Link" in (EPIC_KEY)
       - status was in (Closed, "Won't Do", Resolved) on %DATE% AND "Epic Link" in (EPIK_KEY)


## 3) HTML page creator
    create-html-status.sh [YAML FILES]

Very basic bash script to produce a Status.html file to visualize all the data the wrapper tool and the jira-tool.py creates.
