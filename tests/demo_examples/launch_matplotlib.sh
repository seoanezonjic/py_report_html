#! /usr/bin/env bash
. ~soft_bio_267/initializes/init_python

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
