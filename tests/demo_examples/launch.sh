#! /usr/bin/env bash
. ~soft_bio_267/initializes/init_python

#### Uncomment the following lines to create a virtual environment and install the package 
#### if you want to check changes in the package done by yourself

mkdir -p ~/tests/py_report_venv
python -m venv ~/tests/py_report_venv --system-site-packages
source ~/tests/py_report_venv/bin/activate
pip install -e ~/dev_py/py_report_html
#export PATH=~/tests/py_report_venv/bin:$PATH

paths=`echo -e "
file_data/barplot1.txt,
file_data/barplot2.txt,
file_data/barplot3.txt,
file_data/barplot4.txt,
file_data/x_y.txt,
file_data/x_y_crowded.txt,
file_data/table1.txt,
file_data/table1_header.txt,
file_data/text_number_tab.txt,
file_data/pie_uniq.txt,
file_data/boxplot.txt,
file_data/boxplot_one_series.txt,
file_data/boxplot_factor.txt,
file_data/rank_distribution.txt,
file_data/ridgeline.txt,
file_data/circular.txt,
file_data/links,
file_data/hap_sample,
file_data/haplotipe_array,
file_data/correlation1.tsv,
file_data/canvas_table,
file_data/network.txt,
file_data/scatter3dsizeAndColor.txt,
file_data/boxplot_grid.txt,
file_data/density_one_serie.txt
" | tr -d [:space:]` 

report_html -t template.txt -d $paths -c file_data/custom_css -j file_data/custom_js
#report_html -t table_template -d $paths
#report_html -t template_mixed -d $paths -o mixed
#report_html -t template_mixed_string_syntax -d $paths -o mixed_string
