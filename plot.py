#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import subprocess
import os
import sys

data = """
set xdata time
set timefmt "%Y-%m-%d"
set xrange ["2017-11-01":"2018-01-30"]
set xzeroaxis
set title "BURNDOWN"
set format x "%m-%d"
set grid ytics

set style fill solid 1.0 noborder
set boxwidth 0.7 relative

unset key

set terminal png font "/usr/share/fonts/truetype/freefont/FreeSans.ttf" 12 size 1024,768
set output "burndown.png"
plot '-' using 1:2:2:3:3 with candlesticks lt 1 lc rgb 'red'
2017-11-16      1900    400
2017-11-23      1650    300
2017-11-30      1390    200
2017-12-07      1240    300
2017-12-14      1000    400
2017-12-21      700     200
2017-12-28      640     100
2018-01-05      550     50
2018-01-12      200     100
2018-01-19      100     50
"""

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

gnuplot(data)

plotted, error = gnuplot(data)
if not plotted:
    print(error)
