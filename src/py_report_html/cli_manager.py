import argparse, sys, os, glob, re

from py_cmdtabs import CmdTabs
from py_report_html import Py_report_html

def parse_paths(string): 
	expanded_paths = []
	for path in re.sub(r"\s+", '', string).split(','):
		if '*' in path: expanded_paths.extend(glob.glob(path))
		else: expanded_paths.append(path)
	return expanded_paths

def py_report_html(args=None):
	if args == None: args = sys.argv[1:]
	parser = argparse.ArgumentParser(description='Perform Network analysis from NetAnalyzer package')
	parser.add_argument("-t", "--template", dest="template", default= None, 
						help="Input template file")
	parser.add_argument("-s", "--subtemplates_paths", dest="subtemplates_paths", default= [], type=parse_paths,
						help="Comma-separated paths to check for subtemplates that will be use in the main template")
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
	parser.add_argument("-m", "--menu", dest="menu", default= 'contents_list', 
						help="Indicate if indexed content must be a contents list (contents_list) or a menu (menu)")	

	opts =  parser.parse_args(args)
	main_py_report_html(opts)    

def main_py_report_html(options):
	if not os.path.exists(options.template): sys.exit('Template file not exists')
	template = open(options.template).read()

	if len(options.data_files) == 0: sys.exit('Data files has not been specified')
	container = CmdTabs.load_several_files(options.data_files, dict_keys_mapper=os.path.basename, autodetect_compression=True)

	Py_report_html.additional_templates.extend(options.subtemplates_paths)
	report = Py_report_html(container, os.path.basename(options.output), True, options.uncompressed_data, options.menu)
	report.add_js_files(options.javascript_files)
	report.add_css_files(options.css_files)
	report.add_js_cdn(options.javascript_cdn)
	report.add_css_cdn(options.css_cdn)
	report.build(template)
	report.write(options.output + '.html')
