#! /usr/bin/env bash
. ~soft_bio_267/initializes/init_python

#### Uncomment the following lines to create a virtual environment and install the package 
#### if you want to check changes in the package done by yourself

#mkdir -p ~/tests/py_report_venv
#python -m venv ~/tests/py_report_venv --system-site-packages
#source ~/tests/py_report_venv/bin/activate
#pip install -e ~/dev_py/py_report_html

paths=`echo -e "
file_data/barplot1.txt,
file_data/x_y_crowded.txt,
file_data/boxplot.txt,
file_data/boxplot_one_series.txt,
file_data/boxplot_factor.txt,
file_data/boxplot_factor_long.txt,
file_data/coverage_data_modified.txt
" | tr -d [:space:]` 

report_html -t template_matplotlib.txt -d $paths  -o Report_matplotlib
