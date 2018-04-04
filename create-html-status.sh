#!/bin/bash
#
# HTML format status report generator script
#

rm -rf *.png *.plot Status.html
HTML_FILE="Status.html"

cat >> $HTML_FILE <<HEAD
<!DOCTYPE HTML>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Status report</title>
<style>
table {
    border-collapse: collapse;
    width: 1024px;
}
th, td {
    text-align: left;
    padding: 8px;
}
tr:nth-child(even){background-color: #f2f2f2}
th {
    background-color: #33C7FF;
    color: white;
}
</style>
</head>
<body class="wrap wider">
HEAD

cat >> $HTML_FILE << TABLE_HEAD
<p>
<table>
<tr><th>Epic</th><th>Status (%)</th><th>Ready by</th></tr>
TABLE_HEAD

./status-and-projection.sh $*| egrep -v Epic|sed 's/^/<tr><td>/g'|sed 's/$/<\/td><\/tr>/g'|sed 's/,/<\/td><td>/g' >> $HTML_FILE

cat >> $HTML_FILE << TABLE_FOOT
</table>
</p>
TABLE_FOOT

for IMAGE_FILE in `ls *.png | sort -V`;
do 
cat >> $HTML_FILE <<HTML
    <div class="unit w-1-3">
      <div class="lb" id="img_$i">
        <img src="$IMAGE_FILE"/>
      </div>
    </div>
HTML
done

cat >> $HTML_FILE << FOOT
</body>
</html>
FOOT

echo "HTML created and written to $HTML_FILE"
