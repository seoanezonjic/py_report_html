#! /usr/bin/env python

#########################################################
# Load necessary packages
#########################################################

#import json
from collections import defaultdict
import random
import unittest
import os
import re
import copy
import networkx as nx
import matplotlib
import matplotlib.pyplot as plt
from py_report_html import Py_report_html

ROOT_PATH= os.path.dirname(__file__)
DATA_TEST_PATH = os.path.join(ROOT_PATH, 'data')

#########################################################
# Define TESTS
#########################################################
class ReportHtmlTables(unittest.TestCase):
    def setUp(self):
        ### TABLE RELATED DATA FOR TESTING ###
        self.simple_table_id = "simple_table"
        self.complex_table_id = "complex_table"
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
            "tissue  type    type2   liver   brain   lung    cerebellum",
            "nerv    -       -       no      yes     no      yes",
            "pcr     -       -       true    true    false   false",
            "gen1    miRNA   tRNA    20      13      60      15",
            "gen2    miRNA   tRNA    40      60      90      30",
            "gen3    mRNA    ncRNA   100     85      10      12",
            "gen4    mRNA    ncRNA   85      10      20      41"
        ]))
        self.expected_var = [            
            ["nerv", "no", "yes", "no", "yes"],
            ["pcr", "true", "true", "false", "false"]]
        self.expected_smp = [
            ["type" , "miRNA", "miRNA", "mRNA", "mRNA"],
            ["type2", "tRNA" , "tRNA" , "ncRNA", "ncRNA"]]
        self.expected_data = [
            ["tissue", "liver", "brain", "lung", "cerebellum"],
            ["gen1",    20,      13,        60,     15],
            ["gen2",    40 ,     60,        90,     30],
            ["gen3",    100,     85,        10,     12],
            ["gen4",    85,     10,         20,     41]]

        self.container = {"simple_table": self.simple_table, "complex_table": self.complex_table}
        self.html = Py_report_html(self.container, title="Sample", 
                                           data_from_files = True, compress= False)
        
        self.options = {"id": self.complex_table_id,
            "fields": [], #Default fields value if user does not specify
            "var_attr": [1,2],
            "smp_attr": [1,2],
            "styled": "bs", #Testing table boostrap style
            "cell_align": ["left"]*len(self.complex_table[0]), #Testing table cells style options
            "attrib": {"span": 2, "bgcolor": "red"}, #Table atributes
            "add_header_row_names": False, "header": True, "row_names": True, "transpose": False,
            "layout": "forcedir" #Testing graph layout
            }
        
        ### GRAPH RELATED DATA FOR TESTING ###
        self.graph = nx.Graph()
        self.graph.add_edges_from([("A", "B"), ("B", "C"), ("C", "D"), ("D", "B"),
                                    ("A", "X"), ("X", "Y"), ("Y", "Z"), ("Z", "X"),
                                    ("A", "W")])
        for node in self.graph.nodes(): self.graph.nodes[node]["layer"] = "Phenotypes" if node in "WBY" else "Patients"

        self.reference_nodes = ["A"] #Reference nodes will have color index 1
        self.group_nodes = {"com1": ["B", "C", "D"], "com2": ["X", "Y", "Z"]} #Nodes in group_nodes will have color index 2,3,4,etc
        self.layers = ["Phenotypes", "Patients"] # The following colors index will be given: Phenotypes == 2, Patients == 3 
                
    #-------------------------------------------------------------------------------------
    # DATA MANIPULATION METHODS
    #-------------------------------------------------------------------------------------  
        
    def test_delete_items(self):
        nodes = ["nodeA", "nodeB", "nodeC", "nodeD", "nodeF", "nodeG"]
        expected = ["nodeB", "nodeD", "nodeF"]
        self.html.delete_items(nodes, [0, 2, 5])
        self.assertEqual(nodes, expected)

    def test_extract_rows(self):
        expected = [["1", "3"], ["5", "10"]]
        returned = self.html.extract_rows(self.simple_table_id, [0, 5])
        self.assertEqual(expected, returned)

    def test_extract_fields(self):
        expected = [["true", "false", "false"], #Columns 3, 5, 6, row 2, complex table
                   ["100", "10", "12"]] #Columns 3, 5, 6, row 5, complex table
        expected2 = [["tissue"], ["nerv"], ["pcr"], ["gen1"], ["gen2"], ["gen3"], ["gen4"]] #Column 0, all rows, complex table
        
        #Examples of positive fields selection
        returned = self.html.extract_fields(self.complex_table_id, fields=[3,5,6], del_rows=[0,1,3,4,6])
        returned2 = self.html.extract_fields(self.complex_table_id, fields=[0])
        self.assertEqual(expected, returned)
        self.assertEqual(expected2, returned2)

        #Examples of negative fields selection
        returned = self.html.extract_fields(self.complex_table_id, fields=[], del_fields=[0,1,2,4], del_rows=[0,1,3,4,6])
        returned2 = self.html.extract_fields(self.complex_table_id, fields=[], del_fields=[1,2,3,4,5,6])
        self.assertEqual(expected, returned)
        self.assertEqual(expected2, returned2)

    def test_process_attributes(self):
        options = self.options

        returned_row_var = self.html.process_attributes(self.html.extract_rows(options["id"], options['var_attr']), options['smp_attr'], aggregated = False)
        #The aggregated attribute apply a transpose operation on the lists so dims[a,b] of sample fields becomes dims[b,a]
        returned_fields_smp = self.html.process_attributes(self.html.extract_fields(options["id"], options['smp_attr']), options['var_attr'], aggregated = True)
        
        self.assertEqual(self.expected_var, returned_row_var)
        self.assertEqual(self.expected_smp, returned_fields_smp)

    def test_extract_data(self):
        expected_data = [
            ["tissue", "liver", "brain", "lung", "cerebellum"],
            ["gen1",    "20",   "13",   "60",       "15"],
            ["gen2",    "40" ,  "60",   "90",       "30"],
            ["gen3",    "100",  "85",   "10",       "12"],
            ["gen4",    "85" ,  "10",   "20",       "41"]]

        return_data, return_smp, return_var = self.html.extract_data(self.options)
        self.assertEqual(expected_data, return_data)
        self.assertEqual(self.expected_smp, return_smp)
        self.assertEqual(self.expected_var, return_var)

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

        user_options = {"add_header_row_names": True, "header": [], "row_names": []}
        user_options_with_header_names = {"add_header_row_names": True, "header": True, "row_names": False}
        user_options_with_row_names = {"add_header_row_names": True, "header": False, "row_names": True}

        #Testing function default filling options for headers and rows
        self.html.add_header_row_names(table_alone, options=user_options)
        self.assertEqual(expected_default, table_alone)

        #Testing user custom filling options for rows
        self.html.add_header_row_names(table_custom_rownames, options=user_options_with_row_names)
        self.assertEqual(expected_custom_rowname_table, table_custom_rownames)

        #Testing user custom filling options for headers
        self.html.add_header_row_names(table_custom_headers, options=user_options_with_header_names)
        self.assertEqual(expected_custom_header_table, table_custom_headers)

    def test_get_data(self):
        return_data, return_smp, return_var = self.html.get_data(self.options)
        self.assertEqual(self.expected_data, return_data)
        self.assertEqual(self.expected_smp, return_smp)
        self.assertEqual(self.expected_var, return_var)

    def test_get_data_transpose(self):
        options = copy.deepcopy(self.options)
        options["transpose"] = True
         
        transposed_data = list(map(list, zip(*self.expected_data)))
        return_data, return_smp, return_var = self.html.get_data(options)
        
        self.assertEqual(transposed_data, return_data)
        self.assertEqual(self.expected_var, return_smp)
        self.assertEqual(self.expected_smp, return_var)

    #---------------------------------------------------------------------------------------------
    # TABLE METHODS
    #-------------------------------------------------------------------------------------    
 
    def test_prepare_table_attribs(self):
        atributes = {"span": 2, "align": "center", "bgcolor": "red"}
        expected = "bgcolor= \"red\" align= \"center\" span= \"2\" "

        returned = self.html.prepare_table_attribs(atributes)
        self.assertEqual(expected, returned)

    def test_get_col_n_row_span(self):
        tabla = [[3, 9, 3], [4, 5, 6]]
        expected = [[1, 1, 1], [1, 1, 1]]

        rowspan, colspan = self.html.get_col_n_row_span(tabla)
        self.assertEqual(expected, rowspan)
        self.assertEqual(expected, colspan)

    def test_get_span(self):
        colspan = [[1, 2, 1], 
                   [1, 1, 3]]
        
        rowspan = [[1, 1, 1], 
                   [1, 2, 4]]

        no_span = self.html.get_span(colspan, rowspan, 0, 0) #0,0 means row and column for each of the lists 
        only_colspan = self.html.get_span(colspan, rowspan, 0, 1)
        only_rowspan = self.html.get_span(colspan, rowspan, 1, 1)
        both = self.html.get_span(colspan, rowspan, 1, 2)

        self.assertEqual("", no_span)
        self.assertEqual("colspan=\"2\"", only_colspan)
        self.assertEqual("rowspan=\"2\"", only_rowspan)
        self.assertEqual("colspan=\"3\" rowspan=\"4\"", both)
    
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
        
        number_excepted_headers = 5
        number_excepted_rows = 5
        number_expected_td_tags = 20
        number_excepted_zeros = 16

        returned_headers = re.findall(r"<th.*?>.*?</th>", tabla_html)
        returned_rows = re.findall(r"<tr.*?>.*?</tr>", tabla_html, flags=re.DOTALL)
        returned_td_tags = re.findall(r"<td.*?>.*?</td>", tabla_html)

        #Checking if object attributes (count_objects, bs_tables) changed
        self.assertEqual(1, len(self.html.bs_tables))
        self.assertEqual(1, self.html.count_objects)

        #Checking if the number of headers, rows and items in the table is correct
        self.assertEqual(number_excepted_headers, len(returned_headers))
        self.assertEqual(number_excepted_rows, len(returned_rows))
        self.assertEqual(number_expected_td_tags, len(returned_td_tags))

        #Checkinf if custom function is being applied if defined in user_options dictionary
        returned_zeros = re.findall(r"<td.*?>\s*0\s*</td>", tabla_html, flags=re.DOTALL)
        self.assertEqual(number_excepted_zeros, len(returned_zeros))


    #-------------------------------------------------------------------------------------
    # CANVASXPRESS METHODS
    #-------------------------------------------------------------------------------------

    def test_get_data_for_plot(self):
        expected_samples = ["liver", "brain", "lung", "cerebellum"]
        expected_variables = ["gen1", "gen2", "gen3", "gen4"]
        expected_values = [[20,      13,        60,     15],
                            [40 ,     60,        90,     30],
                            [100,     85,        10,     12],
                            [85,     10,         20,     41]]
        values, smp_attr, var_attr, samples, variables = self.html.get_data_for_plot(self.options)

        self.assertEqual(expected_values, values)
        self.assertEqual(self.expected_smp, smp_attr)
        self.assertEqual(self.expected_var, var_attr)
        self.assertEqual(expected_samples, samples)
        self.assertEqual(expected_variables, variables)

    def test_initialize_extracode(self):
        #without options defined
        self.assertEqual("\n", self.html.initialize_extracode(self.options))
        #with user-defined option
        user_options = copy.deepcopy(self.options)
        user_options["extracode"] = "adding extra code"
        self.assertEqual("adding extra code\n", self.html.initialize_extracode(user_options))

    def test_add_canvas_attr(self):
        expected = {"nerv":  ["no", "yes", "no", "yes"], "pcr": ["true", "true", "false", "false"]}
        returned = {}
        self.html.add_canvas_attr(returned, self.expected_var) #Modifies returned in place
        self.assertEqual(expected, returned)

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
        pass

    #-------------------------------------------------------------------------------------
    # CANVASXPRESS GRAPHS METHODS
    #-------------------------------------------------------------------------------------

    def test_cytoscape_network(self): 
        expected = {'nodes': [{'data': {'id': 'A'}}, {'data': {'id': 'B'}}, {'data': {'id': 'C'}}, {'data': {'id': 'D'}}, {'data': {'id': 'X'}}, {'data': {'id': 'Y'}}, {'data': {'id': 'Z'}}, {'data': {'id': 'W'}}], 
                    'edges': [{'data': {'source': 'A', 'target': 'B'}}, {'data': {'source': 'A', 'target': 'X'}}, {'data': {'source': 'A', 'target': 'W'}}, {'data': {'source': 'B', 'target': 'C'}}, {'data': {'source': 'B', 'target': 'D'}}, {'data': {'source': 'C', 'target': 'D'}}, {'data': {'source': 'X', 'target': 'Y'}}, {'data': {'source': 'X', 'target': 'Z'}}, {'data': {'source': 'Y', 'target': 'Z'}}]}
        returned = self.html.cytoscape_network(self.options, self.graph, [], [], [])
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
        