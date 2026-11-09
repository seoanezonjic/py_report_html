#! /usr/bin/env bash

## Run this to update CvX version in py_report_html.

rm ./src/py_report_html/js/canvasXpress.css
rm ./src/py_report_html/js/canvasXpress.min.js

wget https://www.canvasxpress.org/dist/canvasXpress.css -O ./src/py_report_html/js/canvasXpress.css
wget https://www.canvasxpress.org/dist/canvasXpress.min.js -O ./src/py_report_html/js/canvasXpress.min.js

version=`grep -oP 'CanvasXpress \K[0-9]+\.[0-9]+' src/py_report_html/js/canvasXpress.min.js | head -n 1`
echo $version

git add ./src/py_report_html/js/canvasXpress.min.js
git add ./src/py_report_html/js/canvasXpress.css
git commit -m "Updated CanvasXpress to Version $version"
#git push origin master
