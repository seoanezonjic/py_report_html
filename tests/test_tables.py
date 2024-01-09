#! /usr/bin/env python

#########################################################
# Load necessary packages
#########################################################

#import json
from collections import defaultdict
from io import BytesIO
import math
import random
import json
import unittest
import os
import re
import copy
import networkx as nx
import matplotlib
import matplotlib.pyplot as plt
from py_report_html import Py_report_html

from importlib.resources import files

ROOT_PATH= os.path.dirname(__file__)
DATA_TEST_PATH = os.path.join(ROOT_PATH, 'data')
JS_AND_CSS_LIBRARIES_PATH =  Py_report_html.JS_FOLDER
TEMPLATES_PATH = Py_report_html.TEMPLATES

### Defining auxiliary methods for testing purposes ###
def get_plot_data(reportObject, ObjectMethod, **cust_options):
    ObjectMethod(**cust_options) #This add the plot data and config as a string to self.html.plots_data and self.html.plots_data
    results = re.findall(r"=.+?;", reportObject.plots_data[0])[:-1]
    data, conf, events, info, afterRender = [json.loads(result[1:-1]) for result in results]
    canvas_call = re.search(r"Cobj_0.+", reportObject.plots_data[0], re.DOTALL).group(0)
    return data, conf, events, info, afterRender, canvas_call

#########################################################
# Define TESTS
#########################################################
class ReportHtml(unittest.TestCase):
    def setUp(self):
        ### TABLE AND PLOT RELATED DATA FOR TESTING ###

        ## Creating py_report_html object and adding data to it ##
        self.simple_table_id = "simple_table"
        self.complex_table_id = "complex_table"
        self.links_id = "links"
        self.links = [
        ["red",     "gen1", "gen2"],
        ["red",     "gen3", "gen4"],
        ["black",   "gen1", "gen3"],
        ["black",   "gen2", "gen4"]]
        self.empty_table_id = []
        self.simple_table = list(map(lambda x: re.split(r"\s+", x),[
            "1	3",
            "2	4",
            "1	2",
            "4	9",
            "5	12",
            "5	10",
            "4	8",
        ]))
        self.complex_table = list(map(lambda x: re.split(r"\s+", x),[
            "tissue  type    type2   liver   brain    cerebellum",
            "nerv    -       -       no      yes      yes",
            "pcr     -       -       true    true     false",
            "gen1    miRNA   tRNA    20      13       15",
            "gen2    miRNA   tRNA    40      60       30",
            "gen3    mRNA    ncRNA   100     85       12",
            "gen4    mRNA    ncRNA   85      10       41"
        ]))
        self.table_no_rownames = list(map(lambda x: re.split(r"\s+", x),[
            "liver   brain  type     cerebellum",
            "20      13     miRNA    15",
            "40      60     miRNA    30",
            "100     85     mRNA     12",
            "85      10     mRNA     41"
        ]))
        self.container = {"simple_table": self.simple_table, "complex_table": self.complex_table,
                           "table_no_rownames": self.table_no_rownames, "links": self.links,
                           "empty_table_id": self.empty_table_id}
        self.html_title = "Sample"

        ## Defining expected results ##
        self.expected_smp_attrs = [    #These are variable attributes, not the variables themselves        
            ["nerv", "no", "yes", "yes"],
            ["pcr", "true", "true", "false"]]
        self.expected_var_attrs = [    #These are sample attributes, not the samples themselves
            ["type" , "miRNA", "miRNA", "mRNA", "mRNA"],
            ["type2", "tRNA" , "tRNA" , "ncRNA", "ncRNA"]]
        self.x_reshaped_smp_attrs = {"nerv":  ["no", "yes", "yes"], "pcr": ["true", "true", "false"]}
        self.z_reshaped_var_attrs = {"type": ["miRNA", "miRNA", "mRNA", "mRNA"], "type2": ["tRNA" , "tRNA" , "ncRNA", "ncRNA"]}
        
        self.expected_data = [
            ["tissue", "liver", "brain", "cerebellum"],
            ["gen1",    20,      13,        15],
            ["gen2",    40,      60,        30],
            ["gen3",    100,     85,        12],
            ["gen4",    85,      10,        41]]
        self.expected_samples = ["liver", "brain", "cerebellum"] #These are the actual samples
        self.expected_variables = ["gen1", "gen2", "gen3", "gen4"] #These are the actual variables
        self.expected_values = [
            [20,      13,     15],
            [40,      60,     30],
            [100,     85,     12],
            [85,      10,     41]]
        self.expected_data_json = {
            "y": {
                "vars": self.expected_variables, 
                "smps": self.expected_samples,
                "data": self.expected_values},
            "x": self.x_reshaped_smp_attrs,
            "z": self.z_reshaped_var_attrs,
        }
        self.expected_data_json_transposed = {
            "y": {
                "vars": self.expected_samples,
                "smps": self.expected_variables,
                "data": list(map(list, zip(*self.expected_values)))},
            "x": self.z_reshaped_var_attrs,
            "z": self.x_reshaped_smp_attrs,
        }
    
        self.options = {"id": self.complex_table_id,
            "fields": [], #Default fields value if user does not specify
            "var_attr": [1,2], #Variable attributes
            "smp_attr": [1,2], #Sample attributes
            "styled": "bs", #Testing table boostrap style
            "cell_align": ["left"]*len(self.complex_table[0]), #Testing table cells style options
            "attrib": {"span": 2, "bgcolor": "red"}, #Table atributes
            "add_header_row_names": False, 
            "header": True, 
            "row_names": True, 
            #"transpose": False, We are not testing this option as most of the functions (table, and the different plot functions) already set the expected behaviour according to the needs 
            "layout": "forcedir", #Testing graph layout
            "x_label": "x_axis", #Testing plots layout
            'title': 'Title',
            'alpha': 1,
            'theme': 'cx',
            'color_scheme': 'CanvasXpress'
            }
        self.config = {
            'toolbarType' : 'under',
            'xAxisTitle' : self.options['x_label'],
            'title' : self.options['title'],
            "objectColorTransparency": self.options["alpha"],
            "theme": self.options["theme"],
            "colorScheme": self.options["color_scheme"]
        }
        
        ### GRAPH/NETWORK RELATED DATA FOR TESTING ###
        self.graph = nx.Graph()
        self.graph.add_edges_from([("A", "B"), ("B", "C"), ("C", "D"), ("D", "B"),
                                    ("A", "X"), ("X", "Y"), ("Y", "Z"), ("Z", "X"),
                                    ("A", "W")])
        for node in self.graph.nodes(): self.graph.nodes[node]["layer"] = "Phenotypes" if node in ["W","B","Y"] else "Patients"

        self.reference_nodes = ["A"] #Reference nodes will have color index 1
        self.group_nodes = {"com1": ["B", "C", "D"], "com2": ["X", "Y", "Z"]} #Nodes in group_nodes will have color index 2,3,4,etc like shown in the comment below
        self.layers = ["Phenotypes", "Patients"] # The following colors index will be given: Phenotypes == 2, Patients == 3 

        self.graph_list = []
        self.graph_dict = {
            "graph": self.graph, 
            "reference_nodes": self.reference_nodes, 
            "group_nodes": self.group_nodes, 
            "layers": self.layers}

        for line in nx.generate_edgelist(self.graph):
            self.graph_list.append(line.split())

        self.container.update({"graph_list": self.graph_list, "graph_dict": self.graph_dict})

        ### CREATING PY_REPORT_HTML OBJECT ###
        self.html = Py_report_html(self.container, title=self.html_title, data_from_files = True, compress= False)

        ### REGEX PATTERNS FOR TESTING ###
        self.pattern_html = re.compile(r"<html>.*</html>", re.DOTALL | re.IGNORECASE)
        self.pattern_head = re.compile(r"<title>"+self.html_title+r"</title>.*<head>.*<link.*bootstrap.min.css\"/>*.</head>", re.DOTALL)
        self.pattern_body_and_table = re.compile(r"<body.*<table .*"+('table_' + str(self.html.count_objects)) + r".*</table>.*</body>", re.DOTALL)
        self.pattern_ths = re.compile(r"<th.*?>.*?</th>.*"*4, re.DOTALL)
        self.pattern_trs = re.compile(r"<tr.*?>.*?</tr>.*"*5, re.DOTALL)
        self.pattern_script_tag = re.compile(r'<script type="text/javascript".*?>.*?</script>', re.DOTALL)
        self.loaded_pattern_script_tag = re.compile(r'<script src=\"data:application/javascript;base64,', re.DOTALL)
        self.pattern_css_stylesheet_tag = re.compile(r'<link rel="stylesheet" type="text/css".*?>', re.DOTALL)
        self.loaded_pattern_css_stylesheet_tag = re.compile(r'<style type="text/css">.*?</style>', re.DOTALL)
                

    # -------------------------------------------------------------------------------------
    # RENDER TEMPLATE METHODS
    # -------------------------------------------------------------------------------------    

    def test_make_head(self):
        self.html.table(**self.options)
        self.html.make_head()
        
        self.assertRegex(self.html.all_report, self.pattern_head)

    def test_build_body(self):
        table = self.html.table(**self.options)
        self.html.build_body(table)
        self.assertRegex(self.html.all_report, self.pattern_body_and_table)
        self.assertRegex(self.html.all_report, self.pattern_ths)
        self.assertRegex(self.html.all_report, self.pattern_trs)

    def test_build(self):
        table = self.html.table(**self.options)
        self.html.build(table)
      
        self.assertTrue(len(self.html.bs_tables) > 0)
        self.assertRegex(self.html.all_report, self.pattern_html)
        self.assertRegex(self.html.all_report, self.pattern_head)
        self.assertRegex(self.html.all_report, self.pattern_body_and_table)
        self.assertRegex(self.html.all_report, self.pattern_ths)
        self.assertRegex(self.html.all_report, self.pattern_trs)

    def test_check_loaded_libraries_inside_html(self):
        self.html.networks = ["cytoscape", "elgrapho", "sigma"]
        self.html.dt_tables = ["mock_dt"]
        self.html.bs_tables = ["mock_bs"]
        self.html.plots_data = ["mock_plot"]
        self.html.compress = True #In order to activate and load pako.js library too
        
        table = self.html.table(**self.options)
        self.html.build(table)

        sigma_cdn_filepath = str(files(TEMPLATES_PATH).joinpath('sigma_cdn.txt'))
        self.assertTrue(sigma_cdn_filepath != "")
        self.assertTrue(sigma_cdn_filepath != None)
        self.assertTrue(sigma_cdn_filepath.endswith("sigma_cdn.txt"))        

        #Asserting that all libraries are found inside the html
        self.assertEqual(9, len(re.findall(self.pattern_script_tag, self.html.all_report)))
        self.assertEqual(4, len(re.findall(self.loaded_pattern_script_tag, self.html.all_report)))

        self.assertEqual(4, len(re.findall(self.pattern_css_stylesheet_tag, self.html.all_report)))
        self.assertEqual(1, len(re.findall(self.loaded_pattern_css_stylesheet_tag, self.html.all_report)))
    
    def test_get_report(self):
        table = self.html.table(**self.options)
        self.html.build(table)
        report = self.html.get_report()
        self.assertEqual(self.html.all_report, report)

    def test_write(self):
        table = self.html.table(**self.options)
        self.html.build(table)
        self.html.write(os.path.join(DATA_TEST_PATH, "test.html"))
        file = open(os.path.join(DATA_TEST_PATH, "test.html"), "r")
        reread_html = "".join(file.readlines())
        file.close()
        
        self.assertTrue(os.path.isfile(os.path.join(DATA_TEST_PATH, "test.html")))
        self.assertEqual(self.html.all_report, reread_html)
        
        os.remove(os.path.join(DATA_TEST_PATH, "test.html"))

    def test_load_js_libraries(self):
        files = ["canvasXpress.min.js", "cytoscape.min.js", "ElGrapho.min.js", "pako.min.js"]
        loaded_js = self.html.load_js_libraries(files)
        self.assertEqual(len(files), len(loaded_js))

    def test_load_css(self):
        css_library = ["canvasXpress.css"]
        loaded_css = self.html.load_css(css_library)
        self.assertEqual(len(loaded_css), 1)

    def test_compress_decompress_data(self):
        data = 'This is a test string'
        expected_data = '"This is a test string"'

        #Testing compression
        self.html.compress = True
        compressed_data = self.html.compress_data(data)
        future_decompressed_data = self.html.decompress_code(compressed_data)
        expected_future_decompressed_data = 'JSON.parse(pako.inflate(atob("eJxTCsnILFYAokSFktTiEoXikqLMvHQlAFwnB/E="), { to: \'string\' }))'
        self.assertEqual(expected_future_decompressed_data, future_decompressed_data)

        #Testing compress false case
        self.html.compress = False
        compressed_data = self.html.compress_data(data)
        decompressed_data = self.html.decompress_code(compressed_data)
        self.assertEqual(expected_data, decompressed_data)
    #-------------------------------------------------------------------------------------
    # DATA MANIPULATION METHODS
    #-------------------------------------------------------------------------------------  
        
    def test_select_complementary_items(self):
        nodes = ["nodeA", "nodeB", "nodeC", "nodeD", "nodeF", "nodeG"]
        nodes_copy = copy.deepcopy(nodes)
        expected = ["nodeB", "nodeD", "nodeF"]
        returned = self.html.select_complementary_items(nodes, [0, 2, 5])
        self.assertEqual(expected, returned)
        self.assertEqual(nodes_copy, nodes) #Testing that the original list is not modified

    def test_extract_rows(self):
        expected = [["1", "3"], ["5", "10"]]
        returned = self.html.extract_rows(self.simple_table_id, [0, 5])
        self.assertEqual(expected, returned)

    def test_extract_fields(self):
        expected = [["true", "true", "false"], #Columns 3, 4, 5, row 2, complex table
                   ["100", "85", "12"]] #Columns 3, 4, 5, row 5, complex table
        expected2 = [["tissue"], ["nerv"], ["pcr"], ["gen1"], ["gen2"], ["gen3"], ["gen4"]] #Column 0, all rows, complex table
        
        #Examples of positive fields selection
        returned = self.html.extract_fields(self.complex_table_id, fields=[3,4,5], del_rows=[0,1,3,4,6])
        returned2 = self.html.extract_fields(self.complex_table_id, fields=[0])
        self.assertEqual(expected, returned)
        self.assertEqual(expected2, returned2)

        #Examples of negative fields selection
        returned = self.html.extract_fields(self.complex_table_id, fields=[], del_fields=[0,1,2], del_rows=[0,1,3,4,6])
        returned2 = self.html.extract_fields(self.complex_table_id, fields=[], del_fields=[1,2,3,4,5])
        self.assertEqual(expected, returned)
        self.assertEqual(expected2, returned2)

    def test_process_attributes(self):
        options = copy.deepcopy(self.options)
        expected_hashvar = copy.deepcopy(self.html.hash_vars["complex_table"])

        #The aggregated attribute apply a transpose operation on the lists so dims[a,b] of sample fields becomes dims[b,a]
        returned_var_attrs = self.html.process_attributes(self.html.extract_fields(options["id"], options['smp_attr']), options['var_attr'], aggregated = True)
        returned_smp_attrs = self.html.process_attributes(self.html.extract_rows(options["id"], options['var_attr']), options['smp_attr'], aggregated = False)
                
        self.assertEqual(self.expected_smp_attrs, returned_smp_attrs)
        self.assertEqual(self.expected_var_attrs, returned_var_attrs)
        #Asserting equality of samples length with sample attributes length (checking the first of the two factors)
        self.assertEqual(len(self.expected_samples), len(returned_smp_attrs[0][1:]))
        #Asserting equality of variables length with variable attributes length (checking the first of the two factors)
        self.assertEqual(len(self.expected_variables), len(returned_var_attrs[0][1:]))

        #Checking that original table has not been modified as more plot calls will be done to the same table
        self.assertEqual(expected_hashvar, self.html.hash_vars["complex_table"]) 


    def test_extract_data(self):
        expected_hashvar = copy.deepcopy(self.html.hash_vars["complex_table"])
        expected_data_str = [
            ["tissue", "liver", "brain", "cerebellum"],
            ["gen1",    "20",   "13",       "15"],
            ["gen2",    "40" ,  "60",       "30"],
            ["gen3",    "100",  "85",       "12"],
            ["gen4",    "85" ,  "10",       "41"]]

        returned_data_str, returned_smp_attr, returned_var_attr = self.html.extract_data(self.options)
        self.assertEqual(expected_data_str, returned_data_str)
        self.assertEqual(self.expected_var_attrs, returned_var_attr)
        self.assertEqual(self.expected_smp_attrs, returned_smp_attr)
        self.assertEqual(expected_hashvar, self.html.hash_vars["complex_table"]) #Checking that original table has not been modified as more plot calls will be done to the same table

        #Testing the table with colnames and no rownames with only one variable attribute (and no sample attribute) as this edge case is giving error 
        custom_options = copy.deepcopy(self.options)
        custom_options["rownames"] = False
        custom_options["header"] = True
        custom_options["add_header_row_names"] = True
        custom_options["transpose"] = False
        custom_options["id"] = "table_no_rownames"
        custom_options["var_attr"] = [2]
        custom_options["smp_attr"] = []
        
        returned_data_str, returned_smp_attr, returned_var_attr = self.html.extract_data(custom_options)
        self.assertEqual([row[1:] for row in expected_data_str], returned_data_str)
        self.assertEqual([["type", "miRNA", "miRNA", "mRNA", "mRNA"]], returned_var_attr)
        self.assertEqual([], returned_smp_attr)

    def test_add_header_row_names(self):
        table_alone = [["1","3"],
                       ["2","4"]]
        table_custom_rownames = [["r1","1","3"],
                                 ["r2","2","4"]]
        table_custom_headers = [["h1", "h2"], 
                                ["1","3"], 
                                ["2","4"]]
        
        expected_default = [[0, 0, 1],
                          [1, "1","3"],
                          [2, "2","4"]]
        expected_custom_rowname_table = [[0, 1,  2], 
                                       ["r1", "1","3"], 
                                       ["r2", "2","4"]]
        expected_custom_header_table = [[0, "h1", "h2"], 
                                      [1, "1", "3"], 
                                      [2, "2", "4"]]

        user_options = {"add_header_row_names": True, "header": False, "row_names": False, "id":"mock"}
        user_options_with_header_names = {"add_header_row_names": True, "header": True, "row_names": False, "id":"mock"}
        user_options_with_row_names = {"add_header_row_names": True, "header": False, "row_names": True, "id":"mock"}

        #Testing function default filling options for headers and rows
        self.html.add_header_row_names(table_alone, options=user_options)
        self.assertEqual(expected_default, table_alone)

        #Testing user custom filling options for rows
        self.html.add_header_row_names(table_custom_rownames, options=user_options_with_row_names)
        self.assertEqual(expected_custom_rowname_table, table_custom_rownames)

        #Testing user custom filling options for headers
        self.html.add_header_row_names(table_custom_headers, options=user_options_with_header_names)
        self.assertEqual(expected_custom_header_table, table_custom_headers)

    def test_get_data(self): #TODO: The emtpy case is returning an error in extract_data, so why is there a len(data) > 0 condition
        expected_hashvar = copy.deepcopy(self.html.hash_vars["complex_table"])
        custom_options = copy.deepcopy(self.options)
        custom_options["transpose"] = False
        returned_data, returned_smp_attrs, returned_var_attrs = self.html.get_data(custom_options)
        self.assertEqual(self.expected_data, returned_data)
        self.assertEqual(self.expected_var_attrs, returned_var_attrs)
        self.assertEqual(self.expected_smp_attrs, returned_smp_attrs)
        self.assertEqual(expected_hashvar, self.html.hash_vars["complex_table"]) #Checking that original table has not been modified as more plot calls will be done to the same table

        #emtpy case
        custom_options = copy.deepcopy(self.options)
        custom_options.update({"id": "empty_table_id", "fields": [], "var_attr": [], "smp_attr": [], "add_header_row_names": False})
        returned_data, returned_smp_attrs, returned_var_attrs = self.html.get_data(custom_options)
        self.assertEqual([], returned_data)
        self.assertEqual([], returned_var_attrs)
        self.assertEqual([], returned_smp_attrs)


    def test_get_data_transpose(self):
        expected_hashvar = copy.deepcopy(self.html.hash_vars["complex_table"])
        custom_options = copy.deepcopy(self.options)
        custom_options["transpose"] = True
         
        transposed_data = list(map(list, zip(*self.expected_data)))
        returned_data, returned_smp_attrs, returned_var_attrs = self.html.get_data(custom_options)
        
        self.assertEqual(transposed_data, returned_data)
        self.assertEqual(self.expected_smp_attrs, returned_var_attrs)
        self.assertEqual(self.expected_var_attrs, returned_smp_attrs)
        self.assertEqual(expected_hashvar, self.html.hash_vars["complex_table"]) #Checking that original table has not been modified as more plot calls will be done to the same table



    #---------------------------------------------------------------------------------------------
    # TABLE METHODS
    #-------------------------------------------------------------------------------------    
 
    def test_prepare_table_attribs(self):
        atributes = {"align": "center", "bgcolor": "red"}
        expected = "bgcolor= \"red\" align= \"center\" "

        returned = self.html.prepare_table_attribs(atributes)
        self.assertEqual(expected, returned)

    def test_get_col_n_row_span(self):
        #Testing table with no span
        table_no_span = [[3, 9, 3], 
                        [4, 5, 6]]
        expected_no_span = [[1, 1, 1], #It is the same result for row and col span
                            [1, 1, 1]]
        
        rowspan, colspan = self.html.get_col_n_row_span(table_no_span)
        self.assertEqual(expected_no_span, rowspan)
        self.assertEqual(expected_no_span, colspan)

        #Testing table with row and col span
        table_with_row_and_col_span = [
            ["title", "colspan", "colspan"], #A tittle spannin the three columns
            ["sample", "colspan", "expresion"], #sample spanning 2 columns and expresion
            ["nerv",    "brain",        3], # nerv spanning 2 rows, brain and value
            ["rowspan", "cerebellum",   4], # space spanned, cerebellum and value
        ]

        expected_row_span = [
            [1, 1, 1],
            [1, 1, 1], 
            [2, 1, 1], 
            [1, 1, 1]]
        
        expected_col_span = [
            [3, 1, 1],
            [2, 1, 1], 
            [1, 1, 1], 
            [1, 1, 1]]

        rowspan, colspan = self.html.get_col_n_row_span(table_with_row_and_col_span)
        self.assertEqual(expected_row_span, rowspan)
        self.assertEqual(expected_col_span, colspan)

    def test_get_span(self):
        colspan = [[3, 1, 1], #A column of width 3 (spanning the whole width of the table)
                   [2, 1, 1], #A column of width 2 and a column of width 1
                   [1, 1, 1]] #Three columns of width 1
                     
        
        rowspan = [[1, 1, 1], #All the columns have height 1
                    [1, 1, 2], #The first two columns have height 1 and the last has height 2 
                   [1, 1, 1]] #The first two columns have height 1 and the last has height 2
        
        no_span = self.html.get_span(colspan, rowspan, 0, 1) #0,1 means row and column for each of the lists (rowspan and colspan)
        field_with_2_colspan = self.html.get_span(colspan, rowspan, 1, 0)
        field_with_3_colspan = self.html.get_span(colspan, rowspan, 0, 0)
        field_with_2_rowspan = self.html.get_span(colspan, rowspan, 1, 2)

        self.assertEqual("", no_span)
        self.assertEqual("colspan=\"2\"", field_with_2_colspan)
        self.assertEqual("colspan=\"3\"", field_with_3_colspan)
        self.assertEqual("rowspan=\"2\"", field_with_2_rowspan)

    
    def test_get_cell_align(self):
        #In the options dictionary that we are testing 
        # we assigned options['cell_align'] key to ["left"] * length of columns
        expected = "align=\"left\""
        returned = self.html.get_cell_align(self.options['cell_align'], 1) #Testing a random element
        self.assertEqual(expected, returned)
    
    def test_table(self):
        #defining a custom function to be used in the options dictionary and check if it works
        #It has to be a function that modifies the array_data in place        
        def change_to_zero(table):
            for idx, row in enumerate(table): table[idx] = [0 if type(item) in [int, float] else item for item in row]
        
        options = copy.deepcopy(self.options)
        options["func"] = change_to_zero
        tabla_html = self.html.table(**options)
        
        n_excepted_headers, n_excepted_rows = 4, 5
        n_expected_td_tags, n_excepted_zeros = 16, 12

        returned_headers = re.findall(r"<th.*?>.*?</th>", tabla_html)
        returned_rows = re.findall(r"<tr.*?>.*?</tr>", tabla_html, flags=re.DOTALL)
        returned_td_tags = re.findall(r"<td.*?>.*?</td>", tabla_html)

        #Checking if object attributes (count_objects, bs_tables) changed
        self.assertEqual(1, len(self.html.bs_tables))
        self.assertEqual(1, self.html.count_objects)

        #Checking if the number of headers, rows and items in the table is correct
        self.assertEqual(n_excepted_headers, len(returned_headers))
        self.assertEqual(n_excepted_rows, len(returned_rows))
        self.assertEqual(n_expected_td_tags, len(returned_td_tags))

        #Checkinf if custom function is being applied if defined in user_options dictionary
        returned_zeros = re.findall(r"<td.*?>\s*0\s*</td>", tabla_html, flags=re.DOTALL)
        self.assertEqual(n_excepted_zeros, len(returned_zeros))


    #-------------------------------------------------------------------------------------
    # CANVASXPRESS METHODS
    #-------------------------------------------------------------------------------------

    def test_get_data_for_plot(self):
        expected_hashvar = copy.deepcopy(self.html.hash_vars["complex_table"])
        custom_options = copy.deepcopy(self.options)
        custom_options["transpose"] = False
        values, smp_attr, var_attr, samples, variables = self.html.get_data_for_plot(custom_options)

        self.assertEqual(self.expected_values, values)
        self.assertEqual(self.expected_var_attrs, var_attr)
        self.assertEqual(self.expected_smp_attrs, smp_attr)
        self.assertEqual(self.expected_samples, samples)
        self.assertEqual(self.expected_variables, variables)
        self.assertEqual(expected_hashvar, self.html.hash_vars["complex_table"]) #Checking that original table has not been modified as more plot calls will be done to the same table

        #Transposing the table
        custom_options["transpose"] = True
        values, smp_attr, var_attr, samples, variables = self.html.get_data_for_plot(custom_options)

        self.assertEqual(self.expected_data_json_transposed["y"]["data"], values)
        self.assertEqual(self.expected_smp_attrs, sorted(var_attr))
        self.assertEqual(self.expected_var_attrs, sorted(smp_attr))
        self.assertEqual(self.expected_variables, samples)
        self.assertEqual(self.expected_samples, variables)

        #Giving the table default rownames
        custom_options["row_names"] = False
        custom_options["header"] = True
        custom_options["add_header_row_names"] = True
        custom_options["transpose"] = False
        custom_options["id"] = "table_no_rownames"
        custom_options["var_attr"] = [2]
        custom_options["smp_attr"] = []
        
        values, smp_attr, var_attr, samples, variables = self.html.get_data_for_plot(custom_options)
        self.assertEqual([["type", "miRNA", "miRNA", "mRNA", "mRNA"]], var_attr)
        self.assertEqual([], smp_attr)
        self.assertEqual(self.expected_data_json["y"]["data"], values)
        self.assertEqual(["liver", "brain", "cerebellum"], samples)
        self.assertEqual([1,2,3,4], variables)

    def test_initialize_extracode(self):
        #without options defined
        self.assertEqual("\n", self.html.initialize_extracode(self.options))
        #with user-defined option
        user_options = copy.deepcopy(self.options)
        user_options["extracode"] = "adding extra code"
        self.assertEqual("adding extra code\n", self.html.initialize_extracode(user_options))

    def test_add_canvas_attr(self):
        return_var_reshaped = {}
        return_smp_reshaped = {}
        self.html.add_canvas_attr(return_smp_reshaped, self.expected_smp_attrs) #Modifies return_var_reshaped in place
        self.html.add_canvas_attr(return_var_reshaped, self.expected_var_attrs) #Modifies return_smp_reshaped in place
        self.assertEqual(self.x_reshaped_smp_attrs, return_smp_reshaped)
        self.assertEqual(self.z_reshaped_var_attrs, return_var_reshaped)

    def test_segregate_data(self):
        variables_to_segregate = {"var": ["nerv", "pcr"], "smp": ["type", "type2"]} 
        expected = "table1.segregateVariables(['nerv','pcr']);\n" + "table1.segregateSamples(['type','type2']);\n"
        returned = self.html.segregate_data("table1", variables_to_segregate)
        self.assertEqual(expected, returned)

    def test_assign_rgb(self):
        test_data = [["red", "A", "B"], ["yellow", "C", "D"], ["blue", "E", "F"]]
        expected = [["rgb(255,0,0)", "A", "B"], ["rgb(255,255,0)", "C", "D"], ["rgb(0,0,255)", "E", "F"]]
        self.html.assign_rgb(test_data) #Modifies test_data in place
        self.assertEqual(expected, test_data)

        #Testing if it raises an error when the color is not defined
        self.assertRaises(Exception, self.html.assign_rgb, link_data=[["pink", "A", "B"],["yellow", "C", "D"]] )

    def test_reshape(self):
        returned_x = copy.deepcopy(self.x_reshaped_smp_attrs)
        expected_x = {key: value*len(self.expected_variables) for key, value in self.x_reshaped_smp_attrs.items()}
        expected_x["Factor"] =  [item for pack in [[var] * len(self.expected_samples) for var in self.expected_variables] for item in pack]
        expected_samples = self.expected_samples + [item for pack in #Unpacking results of nested list compreh...
                                                    [[f"{sample}_{times}" for sample in self.expected_samples] for times in range(0,len(self.expected_variables)-1)] 
                                                    for item in pack] #Unpacking
        expected_variables = ['vals']
        expected_values = [[20, 13, 15, 40 , 60, 30, 100, 85, 12, 85, 10, 41]]

        returned_samples, returned_variables, returned_values = copy.deepcopy(self.expected_samples), copy.deepcopy(self.expected_variables), copy.deepcopy(self.expected_values)
        self.html.reshape(returned_samples, returned_variables, returned_x, returned_values) #Modifies samples, variables, x and values in place

        #print("-----------------------TESTING RESHAPE-----------------------")
        #print("\n\n samples:\n", returned_samples, "\n\n variables:\n", returned_variables, "\n\n values: \n", returned_values, "\n\n")
        #for key, value in returned_x.items(): print(f"attr {key}: \n", value, "\n\n")

        self.assertEqual(expected_variables, returned_variables)
        self.assertEqual(expected_x, returned_x)
        self.assertEqual(expected_values, returned_values)
        self.assertEqual(expected_samples, returned_samples)

    def test_inject_attributes(self):
        x_factors = {"factor1": ["A", "B", "B", "A"], 
                    "factor2": ["Y", "Y", "N", "N"]}
        
        z_factors = {"factor3": [True, True, True, False, False],
                    "factor4": [True, False, True, False, True]}

        #Testing with no additional added factors (it should return the same json)
        expected_json = copy.deepcopy(self.expected_data_json)
        returned_json = copy.deepcopy(self.expected_data_json)
        self.html.inject_attributes(returned_json, self.options, "x")
        self.html.inject_attributes(returned_json, self.options, "z")

        self.assertEqual(expected_json, returned_json)

        #Testing with additional added factors
        expected_json["x"].update(x_factors)
        expected_json["z"].update(z_factors)

        custom_options = copy.deepcopy(self.options)
        custom_options["inject_smp_attr"] = x_factors
        custom_options["inject_var_attr"] = z_factors
        self.html.inject_attributes(returned_json, custom_options, "x")
        self.html.inject_attributes(returned_json, custom_options, "z")
        
        self.assertEqual(expected_json, returned_json)

    def test_set_tree(self):
        user_options = copy.deepcopy(self.options)
        user_options.update({"tree": os.path.join(DATA_TEST_PATH, "tree.txt"),
                             "treeBy": "v"})
        expected_config = copy.deepcopy(self.config)

        self.html.set_tree(user_options, expected_config)

        self.assertTrue(expected_config["variablesClustered"])
        self.assertIsNotNone(expected_config.get("varDendrogramNewick"))
        self.assertTrue(len(expected_config["varDendrogramNewick"]) > 0)

    ### TESTS FOR CANVASXPRESS PLOTS ###

    def test_barplot(self):
        custom_options = copy.deepcopy(self.options)
        custom_options["title"] = "My_barplot"
        custom_options["extracode"] = "adding extra code"
        
        expected_config = copy.deepcopy(self.config)
        expected_config.update({"title": "My_barplot", "graphType": "Bar"})
        obj_id = "obj_0"
        
        data, conf, events, info, afterRender, obj_0 = get_plot_data(self.html, self.html.barplot, **custom_options)
        self.assertEqual(len(self.html.plots_data), 1) #Checking if there is only one plot data and config saved
        self.assertEqual(self.expected_data_json_transposed, data)
        self.assertEqual(expected_config, conf)
        self.assertFalse(events)    #Checking if events is False
        self.assertFalse(info)  #Checking if info is False
        self.assertEqual(len(afterRender), 0)   #Checking if afterRender is empty
        self.assertTrue(obj_id in obj_0 and "adding extra code" in obj_0) #Checking if the object id is in the string and if the extra code is there
        
    def test_line(self):
        expected_config = copy.deepcopy(self.config)
        expected_config["graphType"]= "Line"
        data, conf, events, info, afterRender, obj_0 = get_plot_data(self.html, self.html.line, **self.options)
        self.assertEqual([self.expected_data_json_transposed, expected_config, False, False, []],
                         [data, conf, events, info, afterRender])

    def test_barline(self):
        custom_options = copy.deepcopy(self.options)
        custom_options.update({"xAxisTitle": "Expression of genes 1 and 2 (bars)",
                                "xAxis2Title": "Expression of genes 3 and 4 (lines)",
                                "xAxis": ["lung"], "xAxis2": ["liver"] })
        
        expected_config = copy.deepcopy(self.config)
        expected_config.update({ "graphType": "BarLine",
                                "lineType": "spline",
                                "xAxis": ["lung"],
                                "xAxis2": ["liver"],})
        
        data, conf, events, info, afterRender, canvas_function_call = get_plot_data(self.html, self.html.barline, **custom_options)
        self.assertEqual([self.expected_data_json_transposed, expected_config, False, False, []],
                        [data, conf, events, info, afterRender])

    def test_dotline(self):
        custom_options = copy.deepcopy(self.options)
        custom_options.update({"xAxisTitle": "Expression of genes 1 and 2 (bars)",
                                "xAxis2Title": "Expression of genes 3 and 4 (lines)",
                                "xAxis": ["lung"], "xAxis2": ["liver"] })
        
        expected_config = copy.deepcopy(self.config)
        expected_config.update({ "graphType": "DotLine",
                                "lineType": "spline",
                                "xAxis": ["lung"],
                                "xAxis2": ["liver"],})
        
        data, conf, events, info, afterRender, canvas_function_call = get_plot_data(self.html, self.html.dotline, **custom_options)
        self.assertEqual([self.expected_data_json_transposed, expected_config, False, False, []],
                        [data, conf, events, info, afterRender])

    def test_arealine(self):
        custom_options = copy.deepcopy(self.options)
        custom_options.update({"xAxisTitle": "Expression of genes 1 and 2 (bars)",
                                "xAxis2Title": "Expression of genes 3 and 4 (lines)",
                                "xAxis": ["lung"], "xAxis2": ["liver"] })
        
        expected_config = copy.deepcopy(self.config)
        expected_config.update({ "graphType": "AreaLine",
                                "lineType": "rect",
                                "xAxis": ["lung"],
                                "xAxis2": ["liver"],
                                "objectBorderColor":"false",
                            "objectColorTransparency":0.7})
        
        data, conf, events, info, afterRender, canvas_function_call = get_plot_data(self.html, self.html.arealine, **custom_options)
        self.assertEqual([self.expected_data_json_transposed, expected_config, False, False, []],
                        [data, conf, events, info, afterRender])

    def test_area(self):
        custom_options = copy.deepcopy(self.options)
        custom_options.update({"xAxisTitle": "Expression of genes 1 and 2 (bars)",
                                "xAxis2Title": "Expression of genes 3 and 4 (lines)",
                                "xAxis": ["lung"], "xAxis2": ["liver"] })
        
        expected_config = copy.deepcopy(self.config)
        expected_config.update({ "graphType": "Area",
                                "lineType": "rect",
                                "objectBorderColor":"false",
                                "objectColorTransparency":0.7,})
        
        data, conf, events, info, afterRender, canvas_function_call = get_plot_data(self.html, self.html.area, **custom_options)
        self.assertEqual([self.expected_data_json_transposed, expected_config, False, False, []],
                        [data, conf, events, info, afterRender])        

    def test_stacked(self):
        expected_config = copy.deepcopy(self.config)
        expected_config["graphType"]= "Stacked"
        data, conf, events, info, afterRender, obj_0 = get_plot_data(self.html, self.html.stacked, **self.options)
        self.assertEqual([self.expected_data_json_transposed, expected_config, False, False, []],
                         [data, conf, events, info, afterRender])

    def test_stackedline(self):
        custom_options = copy.deepcopy(self.options)
        custom_options.update({"xAxisTitle": "Expression of genes 1 and 2 (bars)",
                                "xAxis2Title": "Expression of genes 3 and 4 (lines)",
                                "xAxis": ["lung"], "xAxis2": ["liver"] })
        
        expected_config = copy.deepcopy(self.config)
        expected_config.update({ "graphType": "StackedLine",
                                "lineType": "spline",
                                "xAxis": ["lung"],
                                "xAxis2": ["liver"],})
        
        data, conf, events, info, afterRender, canvas_function_call = get_plot_data(self.html, self.html.stackedline, **custom_options)
        self.assertEqual([self.expected_data_json_transposed, expected_config, False, False, []],
                        [data, conf, events, info, afterRender])

    def test_corplot(self):
        expected_config = copy.deepcopy(self.config)
        expected_config.update({"graphType": "Correlation", "correlationAxis": "samples"})
        data, conf, events, info, afterRender, obj_0 = get_plot_data(self.html, self.html.corplot, **self.options)
        self.assertEqual([self.expected_data_json, expected_config, False, False, []],
                         [data, conf, events, info, afterRender])
        
    def test_pie(self):
        expected_config = copy.deepcopy(self.config)
        expected_config.update({"graphType": "Pie", "showPieGrid": True, "xAxis": self.expected_samples})
        data, conf, events, info, afterRender, obj_0 = get_plot_data(self.html, self.html.pie, **self.options)
        expected_config.update({"layout": f"{math.ceil(len(self.expected_samples)/2)}X2",
                              "showPieSampleLabel": True})
        self.assertEqual([self.expected_data_json, expected_config, False, False, []],
                            [data, conf, events, info, afterRender])

    def test_dotplot(self):
        custom_options = copy.deepcopy(self.options)
        custom_options["connect"] = True
        expected_config = copy.deepcopy(self.config)
        expected_config.update({"graphType": "Dotplot", "dotplotType": "stacked", "connectBy": "Connect"})
        custom_data_json = self.expected_data_json_transposed
        custom_data_json["z"]["Connect"] = [1] * len(self.expected_data_json_transposed["y"]["vars"])

        data, conf, events, info, afterRender, obj_0 = get_plot_data(self.html, self.html.dotplot, **custom_options)
        self.assertEqual([custom_data_json, expected_config, False, False, []],
                        [data, conf, events, info, afterRender])

    def test_heatmap(self):
        expected_config = copy.deepcopy(self.config)
        expected_config.update({"graphType": "Heatmap"})
        data, conf, events, info, afterRender, obj_0 = get_plot_data(self.html, self.html.heatmap, **self.options)
        self.assertEqual([self.expected_data_json_transposed, expected_config, False, False, []],
                        [data, conf, events, info, afterRender])

    def test_boxplot_without_factor(self):
        expected_config = copy.deepcopy(self.config)
        expected_config.update({"graphType": "Boxplot",
                                 "showBoxplotIfViolin":True,
                                "showBoxplotOriginalData":True,
                                "showViolinBoxplot":True,
                                "jitter":True})

        ##### First test With default options, no groups defined
        user_options = copy.deepcopy(self.options)
        user_options["add_violin"] = True

        #Although no change is done in boxplot method, the data is being modified in 
        #canvasXpress_main method, at line 424, with 'if options.get('mod_data_structure') == 'boxplot':'
        custom_data_json = copy.deepcopy(self.expected_data_json_transposed)
        custom_data_json["y"]["smps"] = None
        custom_data_json.update({ 'x' : {'Factor' : self.expected_data_json_transposed["y"]["smps"]}})

        data, conf, events, info, afterRender, obj_0 = get_plot_data(self.html, self.html.boxplot, **user_options)
        self.assertEqual([custom_data_json, expected_config, False, False, []],
                        [data, conf, events, info, afterRender])        
        ###### TODO: Pending to do the test with groups defined. Ask Pedro about the possible options for groups, groupingFactors and extracode 
        self.assertIn("groupSamples([\"Factor\"]);", obj_0)

    def test_boxplot_with_one_factor(self):
        user_options = copy.deepcopy(self.options)
        user_options["group"] = "type"

        expected_samples = copy.deepcopy(self.expected_data_json_transposed["y"]["smps"])
        expected_variables = copy.deepcopy(self.expected_data_json_transposed["y"]["vars"])
        expected_values = copy.deepcopy(self.expected_data_json_transposed["y"]["data"])
        expected_x = copy.deepcopy(self.expected_data_json_transposed["x"])

        #We have to reshape the data, variables and samples to be able to use the boxplot method if only one factor is defined
        self.html.reshape(expected_samples, expected_variables, expected_x, expected_values)

        expected_data_json = {          
            'y' : {
                'vars' : expected_variables,
                'smps' : expected_samples,
                'data' : expected_values
            },
            'x' : expected_x,
            'z' : self.expected_data_json_transposed["z"]
        } 

        expected_config = copy.deepcopy(self.config)
        expected_config.update({"graphType": "Boxplot"})
        expected_config["groupingFactors"] = ["Factor", "type"]
        expected_config["colorBy"] = "Factor"
        expected_config["segregateSamplesBy"] = ["type"]

        data, conf, events, info, afterRender, obj_0 = get_plot_data(self.html, self.html.boxplot, **user_options)
        self.assertEqual([expected_data_json, expected_config, False, False, []],
                        [data, conf, events, info, afterRender])

    def test_boxplot_with_two_factors(self):
        user_options = copy.deepcopy(self.options)
        user_options["group"] = ["type", "type2"]

        expected_config = copy.deepcopy(self.config)
        expected_config.update({"graphType": "Boxplot"})
        expected_config["groupingFactors"] = ["type", "type2"]
        expected_config["colorBy"] = "type"
        expected_config["segregateSamplesBy"] = ["type2"]

        data, conf, events, info, afterRender, obj_0 = get_plot_data(self.html, self.html.boxplot, **user_options)
        self.assertEqual([self.expected_data_json_transposed, expected_config, False, False, []],
                        [data, conf, events, info, afterRender])
    
    def test_circular_default(self):
        custom_options = copy.deepcopy(self.options)
        custom_options.update({'ringsType': [], 'ringsWeight': [], 'ring_assignation': [], "links": None})

        expected_config = copy.deepcopy(self.config)
        n_variables = len(self.expected_data_json_transposed["y"]["vars"])
        expected_config.update({"graphType": "Circular", "segregateVariablesBy": ["Ring"],
                              "ringGraphType": ['heatmap'] * n_variables,
                              "ringGraphWeight": [math.trunc(100/n_variables)] * n_variables})

        data, conf, events, info, afterRender, obj_0 = get_plot_data(self.html, self.html.circular, **custom_options)

        #We need to modify these variables after applying the function to get the expected default value we want to check
        custom_options.update({"ring_assignation": [ str(i+1) for i in range(n_variables) ]})
        custom_data_json = copy.deepcopy(self.expected_data_json_transposed)
        custom_data_json.update({ 'z' : {'Ring' : custom_options['ring_assignation']}})
        
        self.assertEqual([custom_data_json, expected_config, False, False, []],
                        [data, conf, events, info, afterRender])
        
    def test_circular_with_links_and_custom_options(self):
        expected_links = copy.deepcopy(self.links)
        self.html.assign_rgb(expected_links)

        custom_options = copy.deepcopy(self.options)
        custom_options.update(
            {"ringsType": ['dot', "heatmap", 'bar'], #The plot in each ring
             "links": self.links_id, #Links between variables
             'ringsWeight': [30, 60, 10], #Width of each ring (it needs to sum up 100)
             'ring_assignation': ["1", "2", "2", "3"], #Ring to which each variable belongs. In this example 1 means dotplot, 2 means heatmap and 3 means bar. So gene1 will be in dotplot, gene2 and gene3 in heatmap and gene4 in bar
             'segregate': {"smp": ["nerv"]} #Portions of the ring are cut according to the number of factors in that sample attribute
             }
        )

        expected_config = copy.deepcopy(self.config)
        expected_config.update(
            {"graphType": "Circular", 
            "segregateVariablesBy": ["Ring"],
            "ringGraphType": ['dot', "heatmap", 'bar'],
            "ringGraphWeight": [30, 60, 10],
            "connections": expected_links})
        
        data, conf, events, info, afterRender, obj_0 = get_plot_data(self.html, self.html.circular, **custom_options)

        custom_data_json = copy.deepcopy(self.expected_data_json_transposed)
        custom_data_json.update({ 'z' : {'Ring' : custom_options['ring_assignation']}})
        
        self.assertEqual([custom_data_json, expected_config, False, False, []],
                        [data, conf, events, info, afterRender])  
        #Testing that the function segregateSamplesBy is used
        self.assertIn(f"segregateSamples(['nerv'])", obj_0)


    def test_scatter2D(self):
        custom_options = copy.deepcopy(self.options)
        custom_options.update({"regressionLine": True, "y_label": "custom_y_axis", "add_densities": True,
                               "pointSize": self.expected_samples[0],
                               "colorScaleBy": self.expected_samples[1]})

        expected_config = copy.deepcopy(self.config)
        expected_config.update({ "graphType": "Scatter2D", 
                              'xAxis': [self.expected_samples[0]], 
                              'yAxis': self.expected_samples[1:], "yAxisTitle": "custom_y_axis",
                              "sizeBy": self.expected_samples[0],
                                "colorBy": self.expected_samples[1],
                              "hideHistogram":"false",
                            "histogramBins":20,
                            "histogramStat":"count",
                            "showFilledHistogramDensity":True,
                            "showHistogramDensity":True,
                            "showHistogramMedian":True,
                            "xAxisHistogramHeight":"150",
                            "xAxisHistogramShow":True,
                            "yAxisHistogramHeight":"150",
                            "yAxisHistogramShow":True})
        
        expected_data_json = copy.deepcopy(self.expected_data_json)
        expected_data_json["z"].update({'liver': [20.0, 40.0, 100.0, 85.0], 'brain': [13.0, 60.0, 85.0, 10.0]})
        #Testing with default options (if no xAxis or yAxis are defined, it gets the first column as xAxis and the rest of the samples as yAxis)
        data, conf, events, info, afterRender, canvas_function_call = get_plot_data(self.html, self.html.scatter2D, **custom_options)

        self.assertEqual([expected_data_json, expected_config, False, False, []],
                        [data, conf, events, info, afterRender])
        self.assertTrue("addRegressionLine()" in canvas_function_call)

    def test_scatter2D_with_user_options(self):
        #Testing with user-defined xAxis and yAxis
        custom_options = copy.deepcopy(self.options)
        custom_options.update({"regressionLine": True, "y_label": "custom_y_axis"})
        custom_options.update({"xAxis": [self.expected_samples[1]], "yAxis": [self.expected_samples[2]]})

        expected_config = copy.deepcopy(self.config)
        expected_config.update({ "graphType": "Scatter2D", "yAxisTitle": "custom_y_axis"})
        expected_config.update({'xAxis': [self.expected_samples[1]], 'yAxis': [self.expected_samples[2]]})
        data, conf, events, info, afterRender, canvas_function_call = get_plot_data(self.html, self.html.scatter2D, **custom_options)
        self.assertEqual([self.expected_data_json, expected_config, False, False, []],
                        [data, conf, events, info, afterRender])

    def test_scatterbubble2D(self):
        custom_options = copy.deepcopy(self.options)
        custom_options.update({"y_label": "custom_y_axis", "z_label": "custom_z_axis",
                               "upper_limit": 10, "lower_limit": 0, "ranges": 2})
        diff = (custom_options['upper_limit'] - custom_options['lower_limit']) / custom_options['ranges']

        expected_config = copy.deepcopy(self.config)
        expected_config.update({"graphType": "ScatterBubble2D",
                              'xAxis': [self.expected_samples[0]], 
                              'yAxis': [self.expected_samples[1]], "yAxisTitle": "custom_y_axis",
                              'zAxis': [self.expected_samples[2]], "zAxisTitle": "custom_z_axis",
                              'sizes': [ custom_options['lower_limit'] + n * diff for n in range(custom_options["ranges"])] })
        
        #Testing with default options
        data, conf, events, info, afterRender, canvas_function_call = get_plot_data(self.html, self.html.scatterbubble2D, **custom_options)
        self.assertEqual([self.expected_data_json, expected_config, False, False, []],
                        [data, conf, events, info, afterRender])
        
    def test_scatterbubble2D_with_user_options(self):
        custom_options = copy.deepcopy(self.options)
        custom_options.update({"y_label": "custom_y_axis", "z_label": "custom_z_axis",
                               "upper_limit": 10, "lower_limit": 0, "ranges": 2})
        custom_options.update({"xAxis": [self.expected_samples[2]], 
                               "yAxis": [self.expected_samples[1]],
                               "zAxis": [self.expected_samples[0]]})
        diff = (custom_options['upper_limit'] - custom_options['lower_limit']) / custom_options['ranges']

        expected_config = copy.deepcopy(self.config)
        expected_config.update({"graphType": "ScatterBubble2D",
                              'xAxis': [self.expected_samples[2]], 
                              'yAxis': [self.expected_samples[1]], "yAxisTitle": "custom_y_axis",
                              'zAxis': [self.expected_samples[0]], "zAxisTitle": "custom_z_axis",
                              'sizes': [ custom_options['lower_limit'] + n * diff for n in range(custom_options["ranges"])] })
        
        #Testing with default options
        data, conf, events, info, afterRender, canvas_function_call = get_plot_data(self.html, self.html.scatterbubble2D, **custom_options)
        self.assertEqual([self.expected_data_json, expected_config, False, False, []],
                        [data, conf, events, info, afterRender])
        
    def test_scatter3D(self):
        custom_options = copy.deepcopy(self.options)
        custom_options.update({"y_label": "custom_y_axis", "z_label": "custom_z_axis",
                               "xAxis": [self.expected_samples[2]], 
                               "yAxis": [self.expected_samples[1]],
                               "zAxis": [self.expected_samples[0]],
                               "pointSize": self.expected_samples[0],
                               "colorScaleBy": self.expected_samples[1],
                               "shapeBy": "nerv"})
        
        expected_config = copy.deepcopy(self.config)
        expected_config.update({"graphType": "Scatter3D",
                                "sizeBy": self.expected_samples[0],
                                "colorBy": self.expected_samples[1],
                                "shapeBy": "nerv",
                              'xAxis': [self.expected_samples[2]], 
                              'yAxis': [self.expected_samples[1]], "yAxisTitle": "custom_y_axis",
                              'zAxis': [self.expected_samples[0]], "zAxisTitle": "custom_z_axis"})
        
        expected_data_json = copy.deepcopy(self.expected_data_json)
        expected_data_json["z"].update({'liver': [20.0, 40.0, 100.0, 85.0], 'brain': [13.0, 60.0, 85.0, 10.0]})
        data, conf, events, info, afterRender, canvas_function_call = get_plot_data(self.html, self.html.scatter3D, **custom_options)
        self.assertEqual([expected_data_json, expected_config, False, False, []],
                        [data, conf, events, info, afterRender])

    def test_hexplot(self):
        custom_options = copy.deepcopy(self.options)
        custom_options.update({"y_label": "custom_y_axis", "x_label": "custom_x_axis", "bins": 50})
        expected_config = copy.deepcopy(self.config)
        expected_config.update({"graphType": "Scatter2D", "binplotShape": "hexagon", "binplotBins":"50",
                          "scatterType":"bin2d", "showScatterDensity": True,
                          'xAxis': [self.expected_samples[0]], "xAxisTitle": "custom_x_axis",
                          'yAxis': [self.expected_samples[1]], "yAxisTitle": "custom_y_axis"})

        data, conf, events, info, afterRender, canvas_function_call = get_plot_data(self.html, self.html.hexplot, **custom_options)
        self.assertEqual([self.expected_data_json, expected_config, False, False, []],
                        [data, conf, events, info, afterRender])


    def test_radar(self):
        custom_options = copy.deepcopy(self.options)
        custom_options.update({"subtype": ["area"], #It could also be "bar", "stacked", "dot" or "line"
                            "show_factors": ["type", "-", "type2"]}) # "-" acts tells CanvasXpress to put a narrow blank space between the two factors 

        expected_config = copy.deepcopy(self.config)
        expected_config.update({"graphType": "Circular", "circularType": "radar",
                                "ringGraphType": ["area"], 
                                "smpOverlays": ["type", "-", "type2"]})
        
        data, conf, events, info, afterRender, canvas_function_call = get_plot_data(self.html, self.html.radar, **custom_options)
        self.assertEqual([self.expected_data_json_transposed, expected_config, False, False, []],
                        [data, conf, events, info, afterRender])

    def test_ridgeline(self):
        custom_options = copy.deepcopy(self.options)

        expected_config = copy.deepcopy(self.config)
        expected_config.update({ "graphType": "Scatter2D", 
                                 "colorBy":"Factor", "ridgeBy":"Factor", "graphType":"Scatter2D",
                                "hideHistogram":True, "histogramBins": "30", "ridgelineScale": 2,
                                "showFilledHistogramDensity":True, "showHistogramDensity":True})
        
        expected_data_json = copy.deepcopy(self.expected_data_json_transposed)
        expected_data_json["y"]["smps"] = ["Sample"]
        expected_data_json["y"]["vars"] = [f"s{num}" for num in range(len(self.expected_values)*len(self.expected_values[0]))]
        expected_data_json["y"]["data"] = list(map(list, zip(*self.expected_values)))
        expected_data_json["y"]["data"] = [[float(item)] for row in expected_data_json["y"]["data"] for item in row]
        expected_data_json["z"] = {"Factor":[ [sample]*len(self.expected_values) for sample in self.expected_samples]}
        expected_data_json["z"]["Factor"] = [item for pack in expected_data_json["z"]["Factor"] for item in pack]
        expected_data_json["x"] = self.x_reshaped_smp_attrs
        
        data, conf, events, info, afterRender, canvas_function_call = get_plot_data(self.html, self.html.ridgeline, **custom_options)
        self.assertEqual([expected_data_json, expected_config, False, False, []],
                        [data, conf, events, info, afterRender])


    def test_density(self):
        custom_options = copy.deepcopy(self.options)

        expected_config = copy.deepcopy(self.config)
        expected_config.update({ "graphType": "Scatter2D", 
                                 "hideHistogram":True,
                                 "histogramData":"Factor",
                                 "showFilledHistogramDensity":False,
                                 "showHistogramDensity":True,
                                 "showHistogramMedian":False})
        
        expected_data_json = copy.deepcopy(self.expected_data_json_transposed)
        expected_data_json["y"]["smps"] = ["Sample"]
        expected_data_json["y"]["vars"] = [f"s{num}" for num in range(len(self.expected_values)*len(self.expected_values[0]))]
        expected_data_json["y"]["data"] = list(map(list, zip(*self.expected_values)))
        expected_data_json["y"]["data"] = [[float(item)] for row in expected_data_json["y"]["data"] for item in row]
        expected_data_json["z"] = {"Factor":[ [sample]*len(self.expected_values) for sample in self.expected_samples]}
        expected_data_json["z"]["Factor"] = [item for pack in expected_data_json["z"]["Factor"] for item in pack]
        expected_data_json["x"] = self.x_reshaped_smp_attrs
        
        data, conf, events, info, afterRender, canvas_function_call = get_plot_data(self.html, self.html.density, **custom_options)
        self.assertEqual([expected_data_json, expected_config, False, False, []],
                        [data, conf, events, info, afterRender])

    def test_circular_genome(self):
        self.assertTrue(False, "Test not implemented yet")

    #-------------------------------------------------------------------------------------
    # CANVASXPRESS NETWORK PLOTTING METHODS
    #-------------------------------------------------------------------------------------
    def test_network(self):
        user_options = copy.deepcopy(self.options)
        user_options.update({
            "var_attr": [],
            "smp_attr": [],
            "add_header_row_names": False,
            "method": "cytoscape",
            "id": "graph_list",
            "reference_nodes": [],
            "group_nodes": {}
        })

        #Test the network input as a list of edges
        returned = self.html.network(**user_options)
        self.assertIn('<div id="container_0"', returned)
        self.assertIn("model_0", returned)
        self.assertIn("cytoscape", returned)

        #Test the network input as a dict object and use the elgrapho method
        user_options.update({"id": "graph_dict", "method": "elgrapho"})
        returned2 = self.html.network(**user_options)

        self.assertIn('<div id="container_1"', returned2)
        self.assertIn("model_1", returned2)
        self.assertIn("ElGrapho", returned2)

        #Test sigma method
        user_options.update({"id": "graph_dict", "method": "sigma"})
        returned3 = self.html.network(**user_options)

        self.assertIn('<div id="container_2"', returned3)
        self.assertIn("model_2", returned3)
        self.assertIn("sigma", returned3)

    def test_cytoscape_network(self):
        user_options = copy.deepcopy(self.options)
        user_options["reference_nodes"] = []
        user_options["group_nodes"] = {} 
        expected = {'nodes': [{'data': {'id': 'A'}}, {'data': {'id': 'B'}}, {'data': {'id': 'C'}}, {'data': {'id': 'D'}}, {'data': {'id': 'X'}}, {'data': {'id': 'Y'}}, {'data': {'id': 'Z'}}, {'data': {'id': 'W'}}], 
                    'edges': [{'data': {'source': 'A', 'target': 'B'}}, {'data': {'source': 'A', 'target': 'X'}}, {'data': {'source': 'A', 'target': 'W'}}, {'data': {'source': 'B', 'target': 'C'}}, {'data': {'source': 'B', 'target': 'D'}}, {'data': {'source': 'C', 'target': 'D'}}, {'data': {'source': 'X', 'target': 'Y'}}, {'data': {'source': 'X', 'target': 'Z'}}, {'data': {'source': 'Y', 'target': 'Z'}}]}
        for node_attrs in expected["nodes"]:
            node_attrs["style"] = {'background-color': '#1f77b4'}
        returned = self.html.cytoscape_network(user_options, self.graph, [], [], [])
        self.assertEqual(expected, returned)

    def test_elgrapho_network(self): 
        expected = {"nodes": [], "edges": [], "steps": 30} #This model will use the group_nodes funcion
        group_index = defaultdict(lambda: 0) 
        group_index.update({"A": 1, "B": 2, "C": 2, "D": 2, "X": 3, "Y":3, "Z":3})
        nodes_index = {'A':0, 'B':1, 'C':2, 'D':3, 'X':4, 'Y':5, 'Z':6, 'W':7} #It is basically converting nodes labels to an index format
        
        for node in self.graph.nodes(): expected["nodes"].append({"group": group_index[node]})
        for e in self.graph.edges: expected["edges"].append({"from": nodes_index[e[0]], "to": nodes_index[e[1]]})

        ##### Testing graph plotting preparation with group_nodes option (skipping layers options as it was already tested in the previous test)
        returned = self.html.elgrapho_network(self.options, self.graph, [], self.reference_nodes, self.group_nodes)
        self.assertEqual(expected, returned)
    
    def test_sigma_network(self):
        color_func = plt.get_cmap("tab10")
        custom_options = self.options.copy()
        custom_options["group"] = "layer" #The layer of each node is defined in the setup graph.
        # Just to remind groups. Phen_layer = [W,B,Y], Pat_layer = [A,C,D,X,Z], but A is the reference node, so color_idx=1
        expected_model = {"nodes": [], "edges": []} #This model will use the group_nodes funcion
        expected_model2 = {"nodes": [], "edges": []} #This model will use the layers funcion

        colors_pos, colors_pos2 = defaultdict(lambda: 0), defaultdict(lambda: 0) #Nodes not in group_nodes/layers or reference nodes will have color index 0
        colors_pos.update({"A": 1, "B": 2, "C": 2, "D": 2, "X": 3, "Y":3, "Z":3})
        colors_pos2.update({"A": 1, "W": 2, "B": 2, "Y":2, "C": 3, "D": 3, "X": 3, "Z":3}) 

        random.seed(1)
        for node in self.graph.nodes():
            x, y = random.randrange(1000), random.randrange(1000)
            data, data2 = {"id": node, "color": None, 'x': x, 'y': y, 'size': 1}, {"id": node, "color": None, 'x': x, 'y': y, 'size': 1}
            data["color"] = matplotlib.colors.rgb2hex(color_func(colors_pos[node]))
            data2["color"] = matplotlib.colors.rgb2hex(color_func(colors_pos2[node]))
            expected_model["nodes"].append(data)
            expected_model2["nodes"].append(data2)

        for i, e in enumerate(self.graph.edges): 
            data = {"id": i, "source": e[0], "target": e[1], 'color': '#202020', 'size': 0.1}
            expected_model["edges"].append(data)
            expected_model2["edges"].append(data)
           
        ##### Testing graph plotting preparation with group_nodes option
        random.seed(1) #Reseting seed to get the same random numbers inside function call
        returned_model = self.html.sigma_network(self.options, self.graph, [], self.reference_nodes, self.group_nodes)
        self.assertEqual(expected_model, returned_model)
        
        ##### Testing graph plotting preparation with layers option
        random.seed(1)
        returned_model2 = self.html.sigma_network(custom_options, self.graph, self.layers, self.reference_nodes, {})
        self.assertEqual(expected_model2, returned_model2)


    ##################################################################################
    # EMBED FILES
    ###################################################################################

    def test_embed_pdf(self):
        pdf_from_file = os.path.join(DATA_TEST_PATH, "mock_pdf.pdf")
        returned = self.html.embed_pdf(pdf_from_file)

        self.assertIn("data:application/pdf;base64,", returned)
        self.assertIn("<embed", returned)
        self.assertIn("type=\"application/pdf\"", returned)

    def test_embed_img(self):
        tmp_image = BytesIO(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x02\x80\x00\x00\x01\xe0\x08\x06\x00\x00\x005\xd1\xdc\xe4\x00\x00\x009tEXtSoftware\x00Matplotlib version3.5.3, https://matplotlib.org/\xcd+\xb9\xd2\x00\x00\x00\tpHYs\x00\x00\x0fa\x00\x00\x0fa\x01\xa8?\xa7i\x00\x00:\xd0IDATx\x9c\xed\xddyx\x94\xf5\xa1\xb7\xf1\xefd\x0f\xd9 \x04\xc2\x92\x04\xc2\xbe$d\x01E(ZpAq\x03\x15\x04b\xad\xb6\xb6\xef\xb1\'\x01\x14\xb5\x8aV\x05\xb7X\xc5\x05\x08z\xf4\xb4G\xed9\x84MDp\x17\x17@\xa4\x88\x90\x85}_\x12\x08\x10\xc2\x92\xc9B&\xc9\xcc\xf3\xfe\xe1)\xa7VE\x96$\xbf\xc9<\xf7\xe7\xba\xe6\xba\x9a\x98\xc0\xd7)dn\x9f\xdfCpX\x96e\t\x00\x00\x00\xb6\xe1gz\x00\x00\x00\x00\x9a\x16\x01\x08\x00\x00`3\x04 \x00\x00\x80\xcd\x10\x80\x00\x00\x006C\x00\x02\x00\x00')
        image_from_file = os.path.join(DATA_TEST_PATH, "mock_img.png")

        #Testing with a file
        returned = self.html.embed_img(image_from_file)
        self.assertIn("data:image/png;base64,", returned)
        self.assertIn("<img", returned)

        #Testing with a bytes object
        returned = self.html.embed_img(tmp_image, bytesIO=True)
        self.assertIn("data:image/png;base64,", returned)
        self.assertIn("<img", returned)

    ################################################################################
    # TEST FOR STATIC PLOTTING METHOD(S)
    ################################################################################

    def test_static_plot_main(self):
        plotting_function=  lambda data, plotter_list: plotter_list["sns"].scatterplot(data=data, x='liver', y='brain', hue='type', size='cerebellum')

        user_options = copy.deepcopy(self.options)
        user_options.update({"plotting_function": plotting_function, "theme": "ggplot"})

        returned = self.html.static_plot_main(**user_options)
        self.assertIn("data:image/png;base64,", returned)
        self.assertIn("<img", returned)


    ################################################################################
    # TESTS FOR UTILS METHODS
    ################################################################################

    def test_get_color_palette(self):
        obj_result = self.html.get_color_palette(5)
        cls_result = Py_report_html.get_color_palette(5)
        expected = [(1.0, 0.0, 0.16, 1.0), (1.0, 0.918918918918919, 0.0, 1.0), (0.0, 1.0, 0.0, 1.0), (0.0, 0.9239130434782604, 1.0, 1.0), (0.16304347826086973, 0.0, 1.0, 1.0)]
        
        self.assertEqual(obj_result, expected)
        self.assertEqual(cls_result, expected)