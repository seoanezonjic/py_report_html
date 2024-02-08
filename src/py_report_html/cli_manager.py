import argparse
import sys
import os
import glob
import re

from py_report_html import Py_report_html

def parse_paths(string): return re.sub(r"\s+", '', string).split(',')

def py_report_html(args=None):
	if args == None: args = sys.argv[1:]
	parser = argparse.ArgumentParser(description='Perform Network analysis from NetAnalyzer package')
	parser.add_argument("-t", "--template", dest="template", default= None, 
						help="Input template file")
	parser.add_argument("-o", "--report", dest="output", default= 'Report', 
						help="Path to generated html file (without extension)")
	parser.add_argument("-d", "--data_files", dest="data_files", default= [], type=parse_paths,
						help="Text files with data to use on graphs or tables within report")
	parser.add_argument("-j", "--javascript_files", dest="javascript_files", default= [], type=parse_paths,
						help="Path to javascript files that must be included. Use ',' as path separator for each file")
	parser.add_argument("-c", "--css_files", dest="css_files", default= [], type=parse_paths,
						help="Path to css files that must be included. Use ',' as path separator for each file")
	parser.add_argument("-J", "--javascript_cdn", dest="javascript_cdn", default= [], type=parse_paths,
						help="URL to javascript CDNs that must be included. Use ',' as path separator for each file")
	parser.add_argument("-C", "--css_cdn", dest="css_cdn", default= [], type=parse_paths,
						help="URL to css CDNs that must be included. Use ',' as path separator for each file")
	parser.add_argument("-u", "--uncompressed_data", dest="uncompressed_data", default=True, action='store_false',
						help="Delete redundant items")

	opts =  parser.parse_args(args)
	main_py_report_html(opts)    

def main_py_report_html(options):
	if not os.path.exists(options.template): sys.exit('Template file not exists')
	template = open(options.template).read()

	if len(options.data_files) == 0: sys.exit('Data files has not been specified')
	container = load_files(options.data_files)

	report = Py_report_html(container, os.path.basename(options.output), True, options.uncompressed_data)
	report.add_js_files(options.javascript_files)
	report.add_css_files(options.css_files)
	report.add_js_cdn(options.javascript_cdn)
	report.add_css_cdn(options.css_cdn)
	report.build(template)
	report.write(options.output + '.html')

def load_files(data_files):
	container = {}
	for file_path in data_files:
		if not os.path.exists(file_path): sys.exit(f"File path {file_path} not exists") 
		data_id = os.path.basename(file_path)
		data = parse_tabular_file(file_path)
		container[data_id] = data
	return container

def parse_tabular_file(file_path):
	with open(file_path) as f:
		data = [line.rstrip().split("\t") for line in f]
	return data