#! /usr/bin/env python

#########################################################
# Load necessary packages
#########################################################

#import json
import unittest
import os
import re
import copy
from py_report_html import Py_report_html

ROOT_PATH= os.path.dirname(__file__)
DATA_TEST_PATH = os.path.join(ROOT_PATH, 'data')

#########################################################
# Define TESTS
#########################################################
class ReportHtmlTables(unittest.TestCase):
    def setUp(self):
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

        self.container = {"simple_table": self.simple_table, "complex_table": self.complex_table}


        self.html = Py_report_html(self.container, title="Sample", 
                                           data_from_files = True, compress= False)
        
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
        options = {"ids": self.complex_table_id,
                   "var_attr": [1,2],
                   "smp_attr": [1,2]}

        parsed_row_var = [            
            ["nerv", "no", "yes", "no", "yes"],
            ["pcr", "true", "true", "false", "false"]]
        parsed_fields_smp = [
            ["type" , "miRNA", "miRNA", "mRNA", "mRNA"],
            ["type2", "tRNA" , "tRNA" , "ncRNA", "ncRNA"]]

        returned_row_var = self.html.process_attributes(self.html.extract_rows(options["ids"], options['var_attr']), options['smp_attr'], aggregated = False) 
        returned_fields_smp = self.html.process_attributes(self.html.extract_fields(options["ids"], options['smp_attr']), options['var_attr'], aggregated = True)
        
        self.assertEqual(parsed_row_var, returned_row_var)
        self.assertEqual(parsed_fields_smp, returned_fields_smp)

    def test_prepare_table_attribs(self):
        atributes = {"span": 2, "align": "center", "bgcolor": "red"}
        expected = "bgcolor= \"red\" align= \"center\" span= \"2\" "

        returned = self.html.prepare_table_attribs(atributes)
        self.assertEqual(expected, returned)

"""
    def test_extract_data(self):
        #Prepare a test for a single table and for multiple tables
        #Check the test_process_attributes before to remember what is expected
        
        var_attrs, smp_attrs = [1,2], [1,2]

        expected_smp = []
        expected_var = []
        expected_data = [
            ["20", "13", "60", "15"],
            ["40" , "60", "90", "30"],
            ["100", "85", "10", "12"],
            ["85" , "10", "20", "41"]]

        user_options = {"id": "complex_table", 
                        "fields": [],
                        "del_fields": smp_attrs,
                        "del_rows": var_attrs }
        

    def test_add_header_row_names(self):
        table_alone = [ 
            ["1","3"], 
            ["2","4"]]
        table_custom_rownames = [
            ["r1"],
            ["r2","1","3"], 
            ["r3","2","4"]]
        table_custom_headers = [
            [, "h1", "h2"] 
            ["1","3"], 
            ["2","4"]]
        
        expected_default = [
            [0, 0, 1],
            [1, "1","3"],
            [2, "2","4"]]
        expected_custom_rownames = [
            ["r1", 0,  1],
            ["r2", "1","3"],
            ["r3", "2","4"]]
        expected_custom_header = [
            [0, "h1", "h2"],
            [1, "1", "3"],
            [2, "2", "4"]]

        user_options = {"add_header_row_names": True, "header": [], "row_names": []}
        user_options_with_header_names = {"add_header_row_names": True, "header": ["h1", "h2", "h3"], "row_names": []}
        user_options_with_row_names = {"add_header_row_names": True, "header": [], "row_names": ["r1", "r2", "r3"]}

        #Testing function default filling options for headers and rows
        self.html.add_header_row_names(table_alone, options=user_options)
        self.assertEqual(expected_default, table_alone)

        #Testing user custom filling options for rows
        self.html.add_header_row_names(table_custom_rownames, options=user_options_with_row_names)
        self.assertEqual(expected_custom_rownames, table_custom_rownames)

        #Testing user custom filling options for headers
        self.html.add_header_row_names(table_custom_headers, options=user_options_with_header_names)
        self.assertEqual(expected_custom_header, table_custom_headers)
"""