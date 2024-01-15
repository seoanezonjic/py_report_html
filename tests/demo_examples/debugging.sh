#! /usr/bin/env bash
. ~soft_bio_267/initializes/init_python

#mkdir -p ~/tests/py_report_venv
#python -m venv ~/tests/py_report_venv --system-site-packages
source ~/tests/py_report_venv/bin/activate
#pip install -e ~/dev_py/py_report_html
export PATH=~/tests/py_report_venv/bin:$PATH

paths=`echo -e "
file_data/barplot1.txt,
file_data/network.txt
" | tr -d [:space:]` 

report_html -t debugging.txt -d $paths -o debugging
#report_html -t table_template -d $paths
#report_html -t template_mixed -d $paths -o mixed
#report_html -t template_mixed_string_syntax -d $paths -o mixed_string