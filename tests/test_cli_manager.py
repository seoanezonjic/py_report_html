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
from py_report_html import py_report_html, parse_paths, main_py_report_html, load_files, parse_tabular_file
import pytest
from argparse import Namespace

ROOT_PATH= os.path.dirname(__file__)
DATA_TEST_PATH = os.path.join(ROOT_PATH, 'data')
OUTPUT_TEST_PATH = os.path.join(ROOT_PATH, 'output')
JS_AND_CSS_LIBRARIES_PATH = os.path.join(ROOT_PATH,"..", "src", "py_report_html","js")

# Make data and output directories if they don't exist
if not os.path.exists(DATA_TEST_PATH): os.makedirs(DATA_TEST_PATH)
if not os.path.exists(OUTPUT_TEST_PATH): os.makedirs(OUTPUT_TEST_PATH)

@pytest.fixture
def simple_table():
    return list(map(lambda x: re.split(r"\s+", x),[
            "1	3",
            "2	4",
            "1	2",
            "4	9",
            "5	12",
            "5	10",
            "4	8",
        ]))

@pytest.fixture
def simple_table_formatted():
    return [[1.0,	3.0],
            [2.0,	4.0],
            [1.0,	2.0],
            [4.0,	9.0],
            [5.0,	1.0],
            [5.0,	10.0],
            [4.0,	8.0]]

@pytest.fixture
def complex_table():
    return list(map(lambda x: re.split(r"\s+", x),[
            "tissue  type    type2   liver   brain    cerebellum",
            "nerv    -       -       no      yes      yes",
            "pcr     -       -       true    true     false",
            "gen1    miRNA   tRNA    20      13       15",
            "gen2    miRNA   tRNA    40      60       30",
            "gen3    mRNA    ncRNA   100     85       12",
            "gen4    mRNA    ncRNA   85      10       41"
        ]))

@pytest.fixture
def complex_table_formatted():
    return [["tissue", "liver", "brain", "cerebellum"],
            ["gen1",    20.0,      13.0,        15.0],
            ["gen2",    40.0,      60.0,        30.0],
            ["gen3",    100.0,     85.0,        12.0],
            ["gen4",    85.0,      10.0,        41.0]]

@pytest.fixture
def user_options():
    return {
        "template": os.path.join(DATA_TEST_PATH, "template.txt"),
        "output": os.path.join(OUTPUT_TEST_PATH, "output"),
        "data_files": [os.path.join(DATA_TEST_PATH, "simple_table.txt"), os.path.join(DATA_TEST_PATH, "complex_table.txt")],
        "uncompressed_data": True
    }


def test_parse_tabular_file(simple_table, complex_table):
    assert parse_tabular_file(os.path.join(DATA_TEST_PATH, "simple_table.txt")) == simple_table
    assert parse_tabular_file(os.path.join(DATA_TEST_PATH, "complex_table.txt")) == complex_table

def test_load_files(simple_table, complex_table):
    files = [os.path.join(DATA_TEST_PATH, "simple_table.txt"), os.path.join(DATA_TEST_PATH, "complex_table.txt")]
    container = load_files(files)
    assert container == {'simple_table.txt': simple_table, 'complex_table.txt': complex_table}

def test_main_py_report_html(user_options, simple_table_formatted, complex_table_formatted):
    user_options_namespace = Namespace(**user_options)
    main_py_report_html(user_options_namespace)
    html = open(os.path.join(OUTPUT_TEST_PATH, "output.html")).read()
    for row in simple_table_formatted:
        #Assert a regex of the form <td.*>row[0]</td> is in the html
        assert re.search(r"<t[hd].*>\s*{}\s*</t[hd]>".format(row[0]), html)
        assert re.search(r"<t[hd].*>\s*{}\s*</t[hd]>".format(row[1]), html)
    for row in complex_table_formatted:
        assert re.search(r"<t[hd].*>\s*{}\s*</t[hd]>".format(row[0]), html)
        assert re.search(r"<t[hd].*>\s*{}\s*</t[hd]>".format(row[1]), html)

    #assert that there are two <canvas.*> tags in the html
    assert len(re.findall(r"<canvas.*>", html)) == 2

    #assert that the script is stopped when the template file does not exist and when the data files is empty
    user_options_namespace.data_files = []
    with pytest.raises(SystemExit):
        main_py_report_html(user_options_namespace)

    user_options_namespace.template = "nonexistentfile.txt"
    with pytest.raises(SystemExit):
        main_py_report_html(user_options_namespace)
    
    #remove the output file
    os.remove(os.path.join(OUTPUT_TEST_PATH, "output.html"))

def test_py_report_html(simple_table_formatted, complex_table_formatted):
    args = ["-t", os.path.join(DATA_TEST_PATH, "template.txt"), 
            "-o", os.path.join(OUTPUT_TEST_PATH, "output"), 
            "-d", f'{os.path.join(DATA_TEST_PATH, "simple_table.txt")},{os.path.join(DATA_TEST_PATH, "complex_table.txt")}']
    
    py_report_html(args)
    html = open(os.path.join(OUTPUT_TEST_PATH, "output.html")).read()
    for row in simple_table_formatted:
        #Assert a regex of the form <td.*>row[0]</td> is in the html
        assert re.search(r"<t[hd].*>\s*{}\s*</t[hd]>".format(row[0]), html)
        assert re.search(r"<t[hd].*>\s*{}\s*</t[hd]>".format(row[1]), html)
    for row in complex_table_formatted:
        assert re.search(r"<t[hd].*>\s*{}\s*</t[hd]>".format(row[0]), html)
        assert re.search(r"<t[hd].*>\s*{}\s*</t[hd]>".format(row[1]), html)

    #assert that there are two <canvas.*> tags in the html
    assert len(re.findall(r"<canvas.*>", html)) == 2
    
    #remove the output file
    os.remove(os.path.join(OUTPUT_TEST_PATH, "output.html"))
