#! /usr/bin/env python

import argparse
import sys
import os
import re  


ROOT_PATH=os.path.dirname(__file__)
sys.path.append(os.path.join(ROOT_PATH, '..'))
from py_report_html import Py_report_html

#################################################################################################
## METHODS
#################################################################################################

def load_files(data_files):
	container = {}
	for file_path in options.data_files:
		if not os.path.exists(file_path): sys.exit(f"File path {file_path} not exists") 
		data_id = os.path.basename(file_path)
		data = parse_tabular_file(file_path)
		container[data_id] = data
	return container

def parse_tabular_file(file_path):
	with open(file_path) as f:
		data = [line.rstrip().split("\t") for line in f]
	return data

#################################################################################################
## INPUT PARSING
#################################################################################################
def parse_paths(string):
	return re.sub(r"\s+", '', string).split(',')

parser = argparse.ArgumentParser(description='Perform Network analysis from NetAnalyzer package')

parser.add_argument("-t", "--template", dest="template", default= None, 
					help="Input template file")
parser.add_argument("-o", "--report", dest="output", default= 'Report', 
					help="Path to generated html file (without extension)")
parser.add_argument("-d", "--data_files", dest="data_files", default= [], type=parse_paths,
					help="Text files with data to use on graphs or tables within report")

options = parser.parse_args()

####################################################################################################
## MAIN
######################################################################################################

if not os.path.exists(options.template): sys.exit('Template file not exists')
template = open(options.template).read()

if len(options.data_files) == 0: sys.exit('Data files has not been specified')
container = load_files(options.data_files)

report = Py_report_html(container, os.path.basename(options.output), True)
report.build(template)
report.write(options.output + '.html')
