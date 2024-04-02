import warnings
warnings.filterwarnings(action='ignore', category=FutureWarning, module="seaborn")

import re, os, json, math, zlib, warnings
import pandas as pd
import base64
from io import BytesIO
from collections import defaultdict
from mako.template import Template
import networkx as nx
#from pyvis.network import Network
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import random
import copy
from importlib.resources import files
import pylab

class Py_report_html:
    
    JS_FOLDER = "py_report_html.js"
    TEMPLATES = "py_report_html.templates"
    #JS_FOLDER = os.path.join(os.path.dirname(__file__), 'js')
    #TEMPLATES = os.path.join(os.path.dirname(__file__), 'templates')

    def __init__(self, hash_vars, title = "report", data_from_files = False, compress = True):
        self.all_report = ""
        self.title = title
        self.hash_vars = hash_vars
        self.data_from_files = data_from_files
        self.count_objects = 0
        self.figures = {}
        self.tables = {}
        self.compress = compress
        self.features = { 
            'mermaid': False, 'dt_tables': False, 'pdfHtml5': False, 'canvasXpress': False, 'pako': False,
            'cytoscape': False, 'pyvis': False, 'elgrapho': False, 'sigma': False
        }
        self.js_libraries = []
        self.css_files = []
        self.js_cdn = []
        self.css_cdn = []
        self.custom_css_js = {'js': {'file': [], 'cdn': []}, 'css': {'file': [], 'cdn': []}}
        self.dynamic_js = [] # Chunks of js code that are generated in template rendering
        self.headers = []
        self.header_index = False

    ###################################################################################
    # RENDER TEMPLATE METHODS
    ###################################################################################

    def add_js_files(self, files):
        self.custom_css_js['js']['file'].extend(files)

    def add_css_files(self, files):
        self.custom_css_js['css']['file'].extend(files)

    def add_js_cdn(self, cdns):
        self.custom_css_js['js']['cdn'].extend(cdns)

    def add_css_cdn(self, cdns):
        self.custom_css_js['css']['cdn'].extend(cdns)

    def merge_custom_cdn(self):
        self.js_cdn.extend(self.custom_css_js['js']['cdn'])
        self.css_cdn.extend(self.custom_css_js['css']['cdn'])

    def merge_custom_files(self):
        self.js_libraries.extend(self.custom_css_js['js']['file'])
        self.css_files.extend(self.custom_css_js['css']['file'])

    def get_css_cdn(self):
        string = []
        for cc in self.css_cdn:
            if re.search("^http", cc): # CAnonical form of css CDN loading
                string.append(f"<link rel=\"stylesheet\" type=\"text/css\" href=\"{cc}\"/>")
            else: # Other sintaxis, inject line as is
                string.append(cc)
        return  "\n".join(string)+"\n"

    def get_js_cdn(self):
        string = []
        for jc in self.js_cdn:
            if re.search("^http", jc): # CAnonical form of js CDN loading
                string.append(f"<script type=\"text/javascript\" src=\"{jc}\"></script>")
            else: # Other sintaxis, inject line as is
                string.append(jc)
        return  "\n".join(string)+"\n"

    def build(self, template, build_options = {}):
        templ = Template(template)
        renderered_template = templ.render(plotter=self, build_options=build_options)
        self.all_report += "<HTML>\n"
        self.make_head()
        self.build_body(renderered_template)
        self.all_report += "\n</HTML>"

    def add_dynamic_js(self):
        string_chunks = "\n".join(self.dynamic_js)
        return f"<script>\n{string_chunks}\n</script>\n"

    def load_js_libraries(self, js_libraries):
        loaded_libraries = []
        for js_lib in js_libraries:
            if os.path.exists(js_lib): # External file not provided by py_report_html
                file = js_lib
            else: # File provided by py_report_html
                file = str(files(Py_report_html.JS_FOLDER).joinpath(js_lib))
            with open(file, 'rb') as f:
                loaded_libraries.append(base64.b64encode(f.read()).decode('UTF-8'))
        return loaded_libraries

    def load_css(self, css_files):
        loaded_css = []
        for css_lib in css_files:
            if os.path.exists(css_lib): # External file not provided by py_report_html
                file = css_lib
            else: # File provided by py_report_html
                file = str(files(Py_report_html.JS_FOLDER).joinpath(css_lib))
            with open(file, 'r') as f:
                loaded_css.append(f.read())
        return loaded_css

    def make_head(self):
        self.all_report += (
            f"\t<title>{self.title}</title>\n"
            "<head>\n"
            "<meta charset=\"utf-8\">\n"
            "<meta http-equiv=\"CACHE-CONTROL\" CONTENT=\"NO-CACHE\">\n"
            "<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\" />\n"
            "<meta http-equiv=\"Content-Language\" content=\"en-us\" />\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, shrink-to-fit=no\">\n\n"
        )
        # ADD JS LIBRARIES AND CSS
        # -----------------------------------------------

        # CDN LOAD
        #UPDATED: Now bootstrap is loaded by default
        #self.css_cdn.append('https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css')
        self.css_cdn.append('https://cdn.jsdelivr.net/npm/bootstrap@5.0.0-beta3/dist/css/bootstrap.min.css')
        self.js_cdn.append("https://cdn.jsdelivr.net/npm/bootstrap@5.0.0-beta3/dist/js/bootstrap.bundle.min.js")

        if self.features['dt_tables']: # CDN load, this library is difficult to embed in html file
            self.css_cdn.extend([
                'https://cdn.datatables.net/2.0.0/css/dataTables.dataTables.css',
                'https://cdn.datatables.net/buttons/3.0.0/css/buttons.dataTables.css'
            ])
            self.js_cdn.extend([
                'https://code.jquery.com/jquery-3.7.1.js',
                'https://cdn.datatables.net/2.0.0/js/dataTables.js',
                'https://cdn.datatables.net/buttons/3.0.0/js/dataTables.buttons.js',
                'https://cdn.datatables.net/buttons/3.0.0/js/buttons.dataTables.js',
                'https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js',
                'https://cdn.datatables.net/buttons/3.0.0/js/buttons.html5.min.js',
            ])
            if self.features['pdfHtml5']:
                self.js_cdn.extend([
                    'https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.2.7/pdfmake.min.js',
                    'https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.2.7/vfs_fonts.js'
                ])

        if self.features['mermaid']: self.js_cdn.append("<script type=\"module\"> import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs'; </script>")

        if self.features['sigma']: # sigma CDN load is HUGE so we read it from file
            file = str(files(Py_report_html.TEMPLATES).joinpath('sigma_cdn.txt'))
            with open(os.path.join(file), 'r') as f:
                self.js_cdn.extend(f.readlines())
        
        if self.features['pyvis']: 
            self.js_cdn.append("https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/dist/vis-network.min.js")
            self.css_cdn.append("https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/dist/dist/vis-network.min.css")

        self.merge_custom_cdn()
        self.all_report += self.get_css_cdn()
        self.all_report += self.get_js_cdn()


        # FILE LOAD
        self.js_libraries.append('py_report_html.js') # CUSTOM JAVASCRIPT CREATED BY py_report_html AUTHORS!!!!
        self.css_files.append('py_report_html.css') # CUSTOM CSS CREATED BY py_report_html AUTHORS!!!!

        if self.features['pako']: self.js_libraries.append('pako.min.js')
        if self.features['cytoscape']: self.js_libraries.append('cytoscape.min.js')
        if self.features['elgrapho']: self.js_libraries.append('ElGrapho.min.js')
        if self.features['pyvis']: self.js_libraries.append('PyvisUtils.js')

        if self.features['canvasXpress']:
            self.js_libraries.append('canvasXpress.min.js')
            self.css_files.append('canvasXpress.css')

        self.merge_custom_files()
        for css in self.load_css(self.css_files):
            self.all_report += (f"<style type=\"text/css\">\n{css}\n</style>\n\n")

        for lib in self.load_js_libraries(self.js_libraries):
            self.all_report += f"<script src=\"data:application/javascript;base64,{lib}\" type=\"application/javascript\"></script>\n\n"
        
        self.all_report += self.add_dynamic_js()
        self.all_report +=  "</head>\n"

    def build_body(self, template):
        self.all_report += f"<body>\n{self.create_header_index()}\n{template}\n</body>\n"

    def get_report(self): #return all html string
        templ = Template(self.all_report)
        return templ.render(plotter=self)

    def write(self, file):
        with open(file, 'w') as f: f.write(self.get_report())

    def compress_data(self, data):
        json_data = json.dumps(data)
        if self.compress:
            compressed_data = base64.b64encode(zlib.compress(json_data.encode('UTF-8'))).decode('UTF-8')
        else:
            compressed_data = json_data
        return compressed_data

    def decompress_code(self, data):
        if self.compress:
            self.features['pako'] = True
            string = "JSON.parse(pako.inflate(atob(\"" + data + "\"), { to: 'string' }))"
        else:
            string =  data
        return string

    ###################################################################################
    # REPORT SYNTAX METHODS
    ###################################################################################

    #-------------------------------------------------------------------------------------
    # DATA MANIPULATION METHODS
    #-------------------------------------------------------------------------------------  
    def get_data(self, options):
        data, smp_attr, var_attr = self.extract_data(options)
        if len(data) > 0:
            if self.data_from_files: # If data on container is loaded using html_report as lib, we don't care about data format
                                # if data comes from files and is loaded as strings. We need to format correctly the data.
                rows = len(data)
                cols = len(data[0])
                text = options.get('text')
                if text == None or not text: #TODO: ask Pedro about the text option
                    for r in range(rows):
                        for c in range(cols):
                            if r == 0 and options['header']: continue 
                            if c == 0 and options['row_names']: continue 
                            data[r][c] = float(data[r][c])

            self.add_header_row_names(data, options)

            # Renaming samples and variables if user specified
            if options.get("renamed_samples") and len(options['renamed_samples']) > 0:
                if len(options['renamed_samples']) == len(data[0]):
                    data[0] = options['renamed_samples']
                else:
                    raise Exception("The number of given sample names is not equal to the number of samples in the data")
            if options.get("renamed_variables") and len(options['renamed_variables']) > 0:
                if len(options['renamed_variables']) == len(data):
                    for i, row in enumerate(data): row[0] = options['renamed_variables'][i]
                else:
                    raise Exception("The number of given variable names is not equal to the number of variables in the data")

            if options['transpose']:
                data = list(map(list, zip(*data))) # Transposing data (rows become columns and viceversa)
                smp_attr_bkp = smp_attr
                smp_attr = var_attr
                var_attr = smp_attr_bkp
        return data, smp_attr, var_attr

    def add_header_row_names(self, data, options):
        if options['add_header_row_names']: # This check if html object needs a default header/row_names or not
            if not options['header']:
                data.insert(0, [n for n in range(len(data[0]))])
            if not options['row_names']:
                for i, row in enumerate(data): row.insert(0, i) 

    #TODO: we have to check about this functionallity. Still needed to test
    def merge_tables(self, options):
        data = []
        fields = options['fields']
        ids = options['id']
        ids = ids.split(',')
        if type(fields) is str: fields = [ [int(n) for n in data_fields.split(',') ] for data_fields in fields.split(';') ] # String syntax
        for n,id in enumerate(ids):
            data_file = self.extract_fields(id, fields[n])
            if len(data) == 0:
                data.extend(data_file)
            else:
                for n, row in enumerate(data):
                    data[n] = row + data_file[n]
        return data

    def extract_data(self, options):
        data = []
        smp_attr = None
        var_attr = None
        ids = options['id']
        if type(ids) is str and ',' in ids: ids = ids.split(',')  # String syntax
        fields = options['fields']
        if type(ids) is list:
            data = self.merge_tables(options) #TODO: we have to check about this functionallity
        else:   
            if 'smp_attr' in options and len(options['smp_attr']) > 0:
                if 'var_attr' in options and len(options['var_attr']) > 0:
                    smp_attr = self.process_attributes(self.extract_rows(ids, options['var_attr']), options['smp_attr'], aggregated = False)
                else:
                    smp_attr = []
                    for idx in options['smp_attr']:
                        attr =  self.extract_rows(ids, [idx])
                        smp_attr.append([item for sublist in attr for item in sublist])
            else:
                smp_attr = []
            if 'var_attr' in options and len(options['var_attr']) > 0: 
                if 'smp_attr' in options and len(options['smp_attr']) > 0:                
                    var_attr = self.process_attributes(self.extract_fields(ids, options['smp_attr']), options['var_attr'], aggregated = True)
                else:
                    var_attr = []
                    for idx in options['var_attr']:
                        attr =  self.extract_fields(ids, [idx])
                        var_attr.append([item for sublist in attr for item in sublist])
            else:
                var_attr = []
            data = self.extract_fields(ids, options.get('fields'), del_fields = options.get('var_attr'), del_rows = options.get('smp_attr'))
        return data, smp_attr, var_attr

    def extract_fields(self, id, fields, del_fields = [], del_rows = []):
        data = []
        
        for i, row in enumerate(self.hash_vars[id]):
            if del_rows != None and i in del_rows: continue 
            if len(fields) == 0:
                row = copy.deepcopy(row) # Copy generates a array copy that avoids to modify original objects on data manipulation creating graphs
                if del_fields != None: 
                    row = self.select_complementary_items(row, del_fields)
                data.append(row)
            else:
                data.append([ row[field] for field in fields ]) # new list with extracted fields
        return data

    def select_complementary_items(self, list2del, indexes):
        returned_list = copy.deepcopy(list2del)
        indexes.sort(reverse=True)
        for j in indexes: returned_list.pop(j)
        return returned_list        

    def extract_rows(self, id, rows):
        table = self.hash_vars[id]
        data = [ table[field] for field in rows ]
        return data

    def process_attributes(self, attribs, delete_items, aggregated = False):
        parsed_attr = []
        if aggregated:
            if delete_items != None and len(delete_items) > 0:
                indexes = [1] * len(delete_items)
                attribs = self.select_complementary_items(attribs, indexes)
            for i in range(len(attribs[0])):
                parsed_attr.append([ at[i] for at in attribs ])
        else:
            for attrib in attribs:
                if delete_items != None and len(delete_items) > 0:
                    indexes = range(1, len(delete_items) +1)
                    attrib = self.select_complementary_items(attrib, list(indexes))
                parsed_attr.append(attrib)
        return parsed_attr

    #---------------------------------------------------------------------------------------------
    # TABLE METHODS
    #-------------------------------------------------------------------------------------
    def table(self, **user_options): # https://treyhunner.com/2018/04/keyword-arguments-in-python/#Capturing_arbitrary_keyword_arguments
        options = {
            'id': None,
            'header': False,
            'row_names': False,
            'add_header_row_names': False,
            'transpose': False,
            'fields': [],
            'smp_attr': [],
            'var_attr': [],           
            'border': 1,
            'cell_align': [],
            'attrib': {},
            'func': None,
            'renamed_samples': [],
            'renamed_variables': [],
            'custom_buttons': ['copyHtml5', 'excelHtml5', 'csvHtml5']
        }
        options.update(user_options)
        
        table_attr = self.prepare_table_attribs(options['attrib'])
        array_data, _, _ = self.get_data(options)
        if options.get('func') != None: options['func'](array_data)
        rowspan, colspan = self.get_col_n_row_span(array_data)
        table_id = 'table_' + str(self.count_objects)
        if options.get('styled') == 'dt': 
            if not options["header"]: raise Exception("Tables styled as datatables need to have a header to be properly displayed")    

            embedded_buttons = ','.join([f"'{button}'" for button in options['custom_buttons']])
            if 'pdfHtml5' in options['custom_buttons']: self.features['pdfHtml5'] = True

            self.features['dt_tables'] = True
            self.dynamic_js.append(
                (f"        $(document).ready(function () {{\n"
                f"            $('#{table_id}').DataTable({{ dom:'Bfrtip', buttons: [{embedded_buttons}] }});\n"
                f"        }});\n")
            )

        self.count_objects += 1
        template_file = str(files(Py_report_html.TEMPLATES).joinpath('table.txt'))
        templ = Template(filename=template_file)
        return templ.render(plotter=self, options=options, array_data=array_data, table_id= table_id, table_attr=table_attr, rowspan = rowspan, colspan=colspan)

    def prepare_table_attribs(self, attribs):
        attribs_string = ''
        if len(attribs) > 0:
            for attrib, value in attribs.items():
                attribs_string = f"{attrib}= \"{value}\" " + attribs_string
        return attribs_string

    def get_col_n_row_span(self, table):
        colspan = []
        rowspan = []
        last_row = 0
        for r, row in enumerate(table):
            rowspan.append([1] * len(row))
            colspan.append([1] * len(row))
            last_col = 0
            for c, col in enumerate(row):
                if col == 'colspan':
                    colspan[r][last_col] += 1
                else:
                    last_col = c
                if col == 'rowspan':
                    rowspan[last_row][c] += 1
                else:
                    last_row = r
        return rowspan, colspan

    def get_cell_align(self, align_vector, position):
        cell_align = '' 
        if len(align_vector) > 0: 
            align = align_vector[position]
            cell_align = f"align=\"{align}\""
        return cell_align

    def get_span(self, colspan, rowspan, row, col):
        span = []
        colspan_value = colspan[row][col]
        rowspan_value = rowspan[row][col]
        if colspan_value > 1: span.append(f"colspan=\"{colspan_value}\"")
        if rowspan_value > 1: span.append(f"rowspan=\"{rowspan_value}\"")
        return ' '.join(span)

    #-------------------------------------------------------------------------------------
    # CANVASXPRESS METHODS
    #-------------------------------------------------------------------------------------

    # Support methods
    #-------------------------------------------------------------------------------------
    def get_data_for_plot(self, options):
        values = None
        smp_attr = None
        var_attr = None
        samples = None
        variables = None

        data_array, smp_attr, var_attr = self.get_data(options)
        if len(data_array) > 0:  
            if options.get('func') != None: options['func'](data_array)
            if data_array == None: raise Exception(f"ID {options['id']} has not data") 
            samples = data_array.pop(0)
            samples.pop(0) # We obtain sample names with first pop, the second remove vars title
            if len(data_array) > 0:
                variables = [ row.pop(0) for row in data_array ]
                values = data_array

        return values, smp_attr, var_attr, samples, variables


    def inject_attributes(self, data_structure, options, slot):
        attributes = {}
        attributes_options = {"x": "inject_smp_attr", "z": "inject_var_attr"}
        chosed_option = options.get(attributes_options[slot])
        if chosed_option != None:
            for key, col in chosed_option.items():
                attributes[key] = col 
            data_structure[slot].update(attributes)


    def tree_from_file(self, file):
            string_tree = []
            with open(file) as f:
                string_tree = [line.strip() for line in f.readlines()]
            return string_tree


    def set_tree(self, options, config):
        tree = self.tree_from_file(options["tree"])
        if options["treeBy"] == 's':
            config['smpDendrogramNewick'] = tree
            config['samplesClustered'] = True
        elif options["treeBy"] == 'v':
            config['varDendrogramNewick'] = tree
            config['variablesClustered'] = True

    def canvasXpress_main(self, user_options):
        # Handle arguments
        #------------------------------------------
        options = {
            'id': None,
            'func': None,
            'config_chart': None,
            'fields': [],
            'smp_attr': [],
            'var_attr': [],
            'segregate': [],
            'show_factors': [],
            'data_format': 'one_axis',
            'responsive': True,
            'height': '600px',
            'width': '600px',
            'header': False,
            'row_names': False,
            'add_header_row_names': True,
            'transpose': True,
            'x_label': 'x_axis',
            'title': 'Title',
            'config': {},
            'after_render': [],
            'treeBy': 's',
            'renamed_samples': [],
            'renamed_variables': [],
            'alpha': 1,
            'theme': 'cx',
            'color_scheme': 'CanvasXpress'
        }
        options.update(user_options)
        config = {
            'toolbarType' : 'under',
            'xAxisTitle' : options['x_label'],
            'title' : options['title'],
            "objectColorTransparency": options["alpha"],
            "theme": options["theme"],
            "colorScheme": options["color_scheme"]
        }
        if  options.get('tree') != None : self.set_tree(options, config)

        config.update(options['config'])
        # Data manipulation
        #------------------------------------------

        values, smp_attr, var_attr, samples, variables = self.get_data_for_plot(options)
        if values == None: return f"<div width=\"{options['width']}\" height=\"{options['height']}\" > <p>NO DATA<p></div>"
        object_id = f"obj_{self.count_objects}_"

        x = {}
        z = {}
        if var_attr != None and len(var_attr) > 0: self.add_canvas_attr(z, var_attr) 
        if smp_attr != None and len(smp_attr) > 0: self.add_canvas_attr(x, smp_attr) 
        options['config_chart'](options, config, samples, variables, values, object_id, x, z) # apply custom chart method to configure plot
        # Build JSON objects and Javascript code
        #-----------------------------------------------
        self.count_objects += 1
        data_structure = {
            'y' : {
                'vars' : variables,
                'smps' : samples,
                'data' : values
            },
            'x' : x,
            'z' : z
        }

        events = False  #Possible future use for events for CanvasXpress, currently not used
        info = False   #Possible future use for info for CanvasXpress, currently not used
        afterRender = options['after_render']
        if options.get('mod_data_structure') == 'boxplot':
            data_structure['y']['smps'] = None
            data_structure.update({ 'x' : {'Factor' : samples}})
        elif options.get('mod_data_structure') == 'circular':
            data_structure.update({ 'z' : {'Ring' : options['ring_assignation']}})
        elif options.get('mod_data_structure') == 'ridgeline':
            
            data_structure['y']['smps'] = ["Sample"]
            transposed_values_to_flaten = list(map(lambda *x: list(x), *values))
            data_structure['y']['data'] = [[item] for sublist in transposed_values_to_flaten for item in sublist]
            data_structure['y']['vars'] = [f"s{id}" for id in range(len(data_structure['y']['data']))]
            reshaped_factor = [[sample]*len(values) for sample in samples]
            data_structure.update({ 'z' : {'Factor' : [item for sublist in reshaped_factor for item in sublist]}})
            #print("reshaped_factor:", len(reshaped_factor))
            #print("data:", len(data_structure['y']['data']))
            #print("vars:", len(data_structure['y']['vars']))
            
        
        self.inject_attributes(data_structure, options, slot="x")
        self.inject_attributes(data_structure, options, slot="z") 

        extracode = self.initialize_extracode(options)
        if len(options['segregate']) > 0: extracode += self.segregate_data(f"C{object_id}", options['segregate']) + "\n"
        if options.get('group_samples') != None: extracode += f"C{object_id}.groupSamples({options['group_samples']})\n"
  
        self.features['canvasXpress'] = True

        plot_data = (
            f"var data = {self.decompress_code(self.compress_data(data_structure))};"
            f"var conf = {json.dumps(config)};"
            f"var events = {json.dumps(events)};"
            f"var info = {json.dumps(info)};"
            f"var afterRender = {json.dumps(afterRender)};"
            f"var C{object_id} = new CanvasXpress(\"{object_id}\", data, conf, events, info, afterRender);\n{extracode}\n")

        self.dynamic_js.append(
            (f"        $(document).ready(function () {{\n"
            f"            {plot_data}"
            f"        }});\n")
        )        

        responsive = ''
        if options['responsive']: responsive = "responsive='true'" 
        html = f"<canvas  id=\"{object_id}\" width=\"{options['width']}\" height=\"{options['height']}\" aspectRatio='1:1' {responsive}></canvas>"
        return html
    
    def static_plot_main(self, **user_options):
        # Handle arguments
        #------------------------------------------
        options = {
            'id': None,
            'func': None,
            'plotting_function': None,
            'config_chart': None,
            'fields': [],
            'smp_attr': [],
            'var_attr': [],
            'segregate': [],
            'show_factors': [],
            'header': False,    
            'row_names': False,
            'add_header_row_names': True,
            'transpose': False,
            'height': 600,
            'width': 600,
            'dpi': 100,
            'whole': False,
            'raw': False,
            'theme': 'ggplot'
        }
        options.update(user_options)

        # Data manipulation
        #------------------------------------------
        if options['raw'] == False:
            values, smp_attr, var_attr, samples, variables = self.get_data_for_plot(options)
            if values == None: return f"<div width=\"{options['width']}\" height=\"{options['height']}\" > <p>NO DATA<p></div>"
            
            dataframe = pd.DataFrame(values, columns = samples, index = variables)
            for attr in var_attr:
                dataframe[attr[0]] = attr[1:]

            if options.get('melt') != None:
                melt_columns, new_column_names = options['melt']
                factor_column, values_column = new_column_names
                dataframe = pd.melt(dataframe, id_vars = [column for column in dataframe.columns if column not in melt_columns], 
                                                value_vars=melt_columns, var_name=factor_column, value_name=values_column) 
                
        else: 
            dataframe = self.hash_vars[options['id']]

        object_id = f"obj_{self.count_objects}_"
        self.count_objects += 1

        plotters = {"sns": sns, "plt": plt}
        plt.style.use(options["theme"])
        fig, ax = plt.subplots( figsize=(options['width']/100, options['height']/100), dpi = options['dpi'])

        if options['plotting_function'] != None:               
            if options["whole"] == True:
                values = dataframe if options["raw"] == True else pd.DataFrame(values, columns = samples, index = variables)
                ax = options['plotting_function'](values, plotters)
            else:
                ax = options['plotting_function'](dataframe, plotters)
        else:
            return f"<div width=\"{options['width']}\" height=\"{options['height']}\" > <p>NO PLOTTING FUNCTION<p></div>"
        
        if options.get("x_label"): plt.xlabel(options['x_label'])
        if options.get("title"): plt.title(options['title'])
        if options.get("y_label"): plt.ylabel(options['y_label'])

        plt.show()
        tmpfile = BytesIO()
        plt.savefig(tmpfile, format='png')
        encoded = base64.b64encode(tmpfile.getvalue()).decode('utf-8')
        html = self.embed_img(tmpfile, img_attribs=f"id=\'{object_id}\' width=\'{options['width']}\' height=\'{options['height']}\'", bytesIO=True)
        plt.close('all')
        return html

    def initialize_extracode(self, options):
        extcode = options.get('extracode')
        if extcode == None:
            extracode =""
        else:
            extracode = f"{extcode}"
        return extracode +"\n"

    def add_canvas_attr(self, hash_attr, attr2add):
        for attrs in attr2add:
            attr_name = attrs.pop(0)
            hash_attr[attr_name] = attrs

    def segregate_data(self, obj_id, segregate):
        string =""
        for data_type, names in  segregate.items():
            names_string = ",".join([f"'{name}'" for name in names])
            if data_type == 'var':
                string += f"{obj_id}.segregateVariables([{names_string}]);\n"
            elif data_type == 'smp':
                string += f"{obj_id}.segregateSamples([{names_string}]);\n"
        return string

    def reshape(self, samples, variables, x, values):
        sample_names_copy = samples.copy()
        for n in range(len(variables) -1 ):
            samples.extend([ f"{sample_name}_{n}" for sample_name in sample_names_copy ])
        for factor, annotations in x.items():
            current_annotations = annotations.copy()
            for times in range(len(variables) -1): 
                annotations.extend(current_annotations)
        series_annot = []
        for var in variables:
            for times in sample_names_copy:
                series_annot.append(var)
        x['Factor'] = series_annot
        variables.clear()
        variables.append('vals')
        vals = [item for sublist in values for item in sublist]
        values.clear()
        values.append(vals)

    def assign_rgb(self, link_data):
        colors = {
            'red' : [255, 0, 0],
            'green' : [0, 255, 0],
            'black' : [0, 0, 0],
            'yellow' : [255, 255, 0],
            'blue' : [0, 0, 255],
            'gray' : [128, 128, 128],
            'orange' : [255, 165, 0],
            'cyan' : [0, 255, 255],
            'magenta' : [255, 0, 255]
        }
        for link in link_data:
            code = colors.get(link[0])
            if code != None:
                link[0] = f"rgb({(',').join([str(c) for c in code])})"
            else:
                raise Exception(f"Color link {link[0]} is not allowed. The allowed color names are: #{' '.join(colors.keys())}")
    
    # Chart methods
    #-------------------------------------------------------------------------------------
    def barplot(self, **user_options):
        def config_chart(options, config, samples, variables, values, object_id, x, z):
            config['graphType'] = 'Bar'
            if options.get("colorScale"):
                x[options['x_label']] = values[0]
                config["colorBy"] = options['x_label']
        default_options = { 'row_names': True, 'config_chart' : config_chart }
        default_options.update(user_options)
        html_string = self.canvasXpress_main(default_options)
        return html_string

    def line(self, **user_options):
        def config_chart(options, config, samples, variables, values, object_id, x, z):
            config['graphType'] = 'Line'
        default_options = { 'row_names': True, 'config_chart' : config_chart }
        default_options.update(user_options)
        html_string = self.canvasXpress_main(default_options)
        return html_string
    
    def barline(self, **user_options): #TODO: test this method
        def config_chart(options, config, samples, variables, values, object_id, x, z):
            config['graphType'] = 'BarLine'
            config["lineType"] = "spline"
            if options.get('xAxis') == None: 
                config['xAxis'] = [variables[n] for n in range(len(variables)//2)]
            else:
                config['xAxis'] = options['xAxis']       
            if options.get('xAxis2') == None: 
                config['xAxis2'] = [variables[n] for n in range(len(variables)//2, len(variables))]
            else:
                config['xAxis2'] = options['xAxis2']
        default_options = { 'row_names': True, 'config_chart' : config_chart }
        default_options.update(user_options)
        html_string = self.canvasXpress_main(default_options)
        return html_string
    
    def dotline(self, **user_options):
        def config_chart(options, config, samples, variables, values, object_id, x, z):
            config['graphType'] = 'DotLine'
            config["lineType"] = "spline"
            if options.get('xAxis') == None: 
                config['xAxis'] = [variables[n] for n in range(len(variables)//2)]
            else:
                config['xAxis'] = options['xAxis']       
            if options.get('xAxis2') == None: 
                config['xAxis2'] = [variables[n] for n in range(len(variables)//2, len(variables))]
            else:
                config['xAxis2'] = options['xAxis2']
        default_options = { 'row_names': True, 'config_chart' : config_chart }
        default_options.update(user_options)
        html_string = self.canvasXpress_main(default_options)
        return html_string
    
    def arealine(self, **user_options):
        def config_chart(options, config, samples, variables, values, object_id, x, z):
            config['graphType'] = 'AreaLine'
            config["lineType"] = "rect"
            config.update({"objectBorderColor":"false",
                            "objectColorTransparency":0.7})
            if options.get('xAxis') == None: 
                config['xAxis'] = [variables[n] for n in range(len(variables)//2)]
            else:
                config['xAxis'] = options['xAxis']       
            if options.get('xAxis2') == None: 
                config['xAxis2'] = [variables[n] for n in range(len(variables)//2, len(variables))]
            else:
                config['xAxis2'] = options['xAxis2']
        default_options = { 'row_names': True, 'config_chart' : config_chart }
        default_options.update(user_options)
        html_string = self.canvasXpress_main(default_options)
        return html_string
    
    def area(self, **user_options):
        def config_chart(options, config, samples, variables, values, object_id, x, z):
            config.update({'graphType': 'Area',
                            "lineType":"rect",
                            "objectBorderColor":"false",
                            "objectColorTransparency":0.7})
            
        default_options = { 'row_names': True, 'config_chart' : config_chart }
        default_options.update(user_options)
        html_string = self.canvasXpress_main(default_options)
        return html_string

    def stacked(self, **user_options):
        def config_chart(options, config, samples, variables, values, object_id, x, z):
            config['graphType'] = 'Stacked'
        default_options = { 'row_names': True, 'config_chart' : config_chart }
        default_options.update(user_options)
        html_string = self.canvasXpress_main(default_options)
        return html_string
    
    def stackedline(self, **user_options):
        def config_chart(options, config, samples, variables, values, object_id, x, z):
            config['graphType'] = 'StackedLine'
            config["lineType"] = "spline"
            if options.get('xAxis') == None: 
                config['xAxis'] = [variables[n] for n in range(len(variables)//2)]
            else:
                config['xAxis'] = options['xAxis']       
            if options.get('xAxis2') == None: 
                config['xAxis2'] = [variables[n] for n in range(len(variables)//2, len(variables))]
            else:
                config['xAxis2'] = options['xAxis2']
        default_options = { 'row_names': True, 'config_chart' : config_chart }
        default_options.update(user_options)
        html_string = self.canvasXpress_main(default_options)
        return html_string
    

    def corplot(self, **user_options):
        default_options = { 'transpose': False, 'correlationAxis': 'samples' }
        default_options.update(user_options)
        def config_chart(options, config, samples, variables, values, object_id, x, z):
            config['graphType'] = 'Correlation'
            config['correlationAxis'] = default_options['correlationAxis']
        default_options['config_chart'] = config_chart
        html_string = self.canvasXpress_main(default_options)
        return html_string

    def pie(self, **user_options): 
        def config_chart(options, config, samples, variables, values, object_id, x, z):
            config['graphType'] = 'Pie'
            if len(samples) > 1:
                config['showPieGrid'] = True
                config['xAxis'] = samples 
                if config.get('layout') == None: config['layout'] = f"{math.ceil(len(samples)/2)}X2"
                if config.get('showPieSampleLabel') == None: config['showPieSampleLabel'] = True 
        default_options = { 'transpose' : False, 'config_chart' : config_chart }
        default_options.update(user_options)
        html_string = self.canvasXpress_main(default_options) 
        return html_string

    def scatter2D(self, **user_options):
        default_options = { 'row_names': False, 'transpose': False}
        default_options.update(user_options)
        def config_chart(options, config, samples, variables, values, object_id, x, z):
            config['graphType'] = 'Scatter2D'
            if options.get('xAxis') == None: 
                config['xAxis'] = [samples[0]]
            else:
                config['xAxis'] = options['xAxis']       
            if options.get('yAxis') == None: 
                config['yAxis'] = [samples[n] for n in range(1, len(samples))]
            else:
                config['yAxis'] = options['yAxis']
                
            if default_options.get('y_label') == None :
                config['yAxisTitle'] = 'y_axis'
            else:
                config['yAxisTitle'] = default_options['y_label']
            if options.get('regressionLine') == True:
                options['extracode'] = f"C{object_id}.addRegressionLine();"
            
            if options.get('pointSize') != None:
                config['sizeBy'] = options['pointSize']
                sampleIndex = samples.index(options['pointSize'])
                #samples.pop(sampleIndex)
                z[options['pointSize']] = [row[sampleIndex] for row in values]

            if options.get('colorScaleBy') != None:
                config['colorBy'] = options['colorScaleBy']
                sampleIndex = samples.index(options['colorScaleBy'])
                #samples.pop(sampleIndex)
                z[options['colorScaleBy']] = [row[sampleIndex] for row in values]

            if options.get("add_densities") == True:
                config.update({
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
                
        default_options['config_chart'] = config_chart
        html_string = self.canvasXpress_main(default_options)
        return html_string
    

    def scatter3D(self, **user_options):
        default_options = { 'row_names': False, 'transpose': False}
        default_options.update(user_options)
        def config_chart(options, config, samples, variables, values, object_id, x, z):
            config['graphType'] = 'Scatter3D'
            
            if options.get('xAxis') == None: 
                config['xAxis'] = [samples[0]]
            else:
                config['xAxis'] = options['xAxis']    

            if options.get('yAxis') == None: 
                config['yAxis'] = [samples[1]]
            else:
                config['yAxis'] = options['yAxis']

            if options.get('zAxis') == None: 
                config['zAxis'] = [samples[2]]
            else:
                config['zAxis'] = options['zAxis']
                
            if default_options.get('y_label') == None :
                config['yAxisTitle'] = 'y_axis'
            else:
                config['yAxisTitle'] = default_options['y_label']

            if default_options.get('z_label') == None :
                config['zAxisTitle'] = 'z_axis'
            else:
                config['zAxisTitle'] = default_options['z_label']
            
            if options.get('regressionLine') == True:
                options['extracode'] = f"C{object_id}.addRegressionLine();"

            if options.get('pointSize') != None:
                config['sizeBy'] = options['pointSize']
                sampleIndex = samples.index(options['pointSize'])
                #samples.pop(sampleIndex)
                z[options['pointSize']] = [row[sampleIndex] for row in values]

            if options.get('colorScaleBy') != None:
                config['colorBy'] = options['colorScaleBy']
                sampleIndex = samples.index(options['colorScaleBy'])
                #samples.pop(sampleIndex)
                z[options['colorScaleBy']] = [row[sampleIndex] for row in values]

            if options.get('shapeBy') != None:
                config['shapeBy'] = options['shapeBy']

        default_options['config_chart'] = config_chart
        html_string = self.canvasXpress_main(default_options)
        return html_string

    def scatterbubble2D(self, **user_options):
        default_options = { 'row_names': True, 'transpose': False}
        default_options.update(user_options)
        def config_chart(options, config, samples, variables, values, object_id, x, z):
            config['graphType'] = 'ScatterBubble2D'
            if options.get('xAxis') == None: 
                config['xAxis'] = [samples[0]]
            else:
                config['xAxis'] = options['xAxis']
            if options.get('yAxis') == None:
                config['yAxis'] = [samples[1]]
            else:
                config['yAxis'] = options['yAxis']
            if options.get('zAxis') == None:
                config['zAxis'] = [samples[2]]
            else:
                config['zAxis'] = options['zAxis']
            if options.get('y_label') == None:
                config['yAxisTitle'] = 'y_axis'
            else:
                config['yAxisTitle'] = options['y_label']
            if options.get('z_label') == None:
                config['zAxisTitle'] = 'z_axis'
            else:
                config['zAxisTitle'] = options['z_label']
            if options.get('upper_limit') != None and options.get('lower_limit') != None and options.get('ranges') != None:
                diff = (options['upper_limit'] - options['lower_limit'])/options['ranges']
                sizes = [ options['lower_limit'] + n * diff for n in range(options['ranges'])]
                config['sizes'] = sizes
        default_options['config_chart'] = config_chart
        html_string = self.canvasXpress_main(default_options)
        return html_string
    
    def hexplot(self, **user_options):        
        default_options = { 'row_names': False, 'transpose': False, "bins": 30}
        default_options.update(user_options)
        def config_chart(options, config, samples, variables, values, object_id, x, z):
            config['graphType'] = 'Scatter2D'
            config.update({"binplotShape": "hexagon", "binplotBins":f"{options['bins']}",
                          "scatterType":"bin2d", "showScatterDensity":True})
            config['xAxis'] = [samples[0]] if options.get('xAxis') == None else options['xAxis']
            config['yAxis'] = [samples[1]] if options.get('yAxis') == None else options['yAxis']
            config["yAxisTitle"] = "y_axis" if options.get('y_label') == None else options['y_label']
            config["xAxisTitle"] = "x_axis" if options.get('x_label') == None else options['x_label']
            
        default_options['config_chart'] = config_chart
        html_string = self.canvasXpress_main(default_options)
        return html_string

    def radar(self, **user_options):
        default_options = {"subtype": ["line"]}
        default_options.update(user_options)
        def config_chart(options, config, samples, variables, values, object_id, x, z):
            config.update({'graphType': 'Circular', "circularType": "radar", 
                           "ringGraphType": options["subtype"], "smpOverlays": []})
            if len(options["show_factors"]) > 0:
                for factor in options['show_factors']:
                    if factor in x.keys() or factor == "-": config["smpOverlays"].append(factor)
        default_options['config_chart'] = config_chart
        html_string = self.canvasXpress_main(default_options)
        return html_string
    
    def ridgeline(self, **user_options):
        default_options = {"transpose": False, "bins": 30, "ridgelineScale":2}
        default_options.update(user_options)
        def config_chart(options, config, samples, variables, values, object_id, x, z):
            config['graphType'] = 'Scatter2D'
            config.update({"colorBy":"Factor", "ridgeBy":"Factor", "graphType":"Scatter2D",
                "hideHistogram":True, "histogramBins": f"{options['bins']}",
                "ridgelineScale": options['ridgelineScale'],
                "showFilledHistogramDensity":True, "showHistogramDensity":True
            })

            if options.get('group') == None:
                options['mod_data_structure'] = 'ridgeline'
            else:
                config["ridgeBy"] = options['group']
                config["colorBy"] = options['group']
        
        default_options['config_chart'] = config_chart
        html_string = self.canvasXpress_main(default_options)
        return html_string
    
    def density(self, **user_options):
        default_options = {"transpose": False, "fillDensity": False, "median": False}
        default_options.update(user_options)
        def config_chart(options, config, samples, variables, values, object_id, x, z):
            config['graphType'] = 'Scatter2D'
            config.update({
                    "graphType":"Scatter2D",
                    "hideHistogram":True,
                    "showHistogram": options.get('group') or True,
                    "showFilledHistogramDensity":options['fillDensity'],
                    "showHistogramDensity":True,
                    "showHistogramMedian":options['median'],
            })
        
        default_options['config_chart'] = config_chart
        html_string = self.canvasXpress_main(default_options)
        return html_string        


    def dotplot(self, **user_options):
        default_options = { 'row_names': True, 'connect': False}
        default_options.update(user_options)
        def config_chart(options, config, samples, variables, values, object_id, x, z):
            config['graphType'] = 'Dotplot'
            if default_options.get('connect'):
                config['dotplotType'] = "stacked"
                config['connectBy'] = "Connect"
                z['Connect'] = [1] * len(variables)
        default_options['config_chart'] = config_chart
        html_string = self.canvasXpress_main(default_options)
        return html_string

    def heatmap(self, **user_options):
        def config_chart(options, config, samples, variables, values, object_id, x, z):
            config['graphType'] = 'Heatmap' 
        default_options = { 'row_names' : True, 'config_chart' : config_chart }
        default_options.update(user_options)
        html_string = self.canvasXpress_main(default_options)
        return html_string

    def boxplot(self, **user_options):
        default_options = { 'row_names' : True, 'header' : True }
        default_options.update(user_options)
        def config_chart(options, config, samples, variables, values, object_id, x, z):
            config['graphType'] = 'Boxplot'
            if default_options.get('group') == None:
                options['mod_data_structure'] = 'boxplot'
            else:
                #This option is used when your table in shaped in wide format https://en.wikipedia.org/wiki/Wide_and_narrow_data
                # In this case, variable names are used as series (the levels of the factor or the diferent boxes inside a plot) and the group option (a string) is used to segregate the plots
                #The function performs a reshape of the data to long format before plotting.
                if type(default_options.get('group')) is str:
                    self.reshape(samples, variables, x, values)
                    group = default_options.get('group')
                    series = 'Factor'
                #This option is used when your table in shaped in long format https://en.wikipedia.org/wiki/Wide_and_narrow_data
                # In this case a list is provided. If only one variable is provided in the list, it is used as series.
                # If two variables are provided, the first one is used as series and the second one as group to segregate the plots
                elif type(default_options.get('group')) is list:
                    if len(default_options.get('group')) == 2:
                        series, group = default_options.get('group')
                    if len(default_options.get('group')) == 1:
                        series = default_options['group']
                        group = None

                if config.get("groupingFactors") == None: # if config is defined, we assume that the user set this property to the value that he/she desires
                    if group == None:
                        config["groupingFactors"] = [series]
                    else:
                        config["groupingFactors"] = [series, group]
                if config.get("colorBy") == None: config["colorBy"] = series 
                if group != None and config.get("segregateSamplesBy") == None: config["segregateSamplesBy"] = [group] 
            if options.get('extracode') == None and default_options.get('group') == None:
                options['extracode'] = f"C{object_id}.groupSamples([\"Factor\"]);"
                #config["groupingFactors"] = ["Factor"] Both options are valid, altough not the same behaviour is achieved with segregateSamplesBy...

            if options.get('add_violin') == True:
                config.update({ "showBoxplotIfViolin":True,
                                "showBoxplotOriginalData":True,
                                "showViolinBoxplot":True,
                                "jitter":True})
        default_options['config_chart'] = config_chart
        html_string = self.canvasXpress_main(default_options)
        return html_string

    def circular(self, **user_options):
        default_options = { 'ring_assignation': [], 'ringsType': [], 'ringsWeight': [] }
        default_options.update(user_options)
        def config_chart(options, config, samples, variables, values, object_id, x, z):
            options['mod_data_structure'] = 'circular'
            config['graphType'] = 'Circular'
            config['segregateVariablesBy'] = ['Ring']
            if len(default_options['ringsType']) == 0:
                config['ringGraphType'] = ['heatmap'] * len(variables)
            else:
                config['ringGraphType'] = default_options['ringsType']
            if len(default_options['ringsWeight']) == 0:
                size = math.trunc(100/len(variables))
                config['ringGraphWeight'] = [size] * len(variables)
            else:
                config['ringGraphWeight'] = default_options['ringsWeight']
            if len(default_options['ring_assignation']) == 0:
                options['ring_assignation'] = [ str(i+1) for i in range(len(variables)) ]
            else:
                options['ring_assignation'] = [ str(i) for i in default_options['ring_assignation'] ]
            links_id = default_options.get('links')
            if links_id != None:
                link_data = self.hash_vars.get(links_id)
                if link_data != None and len(link_data) > 0:
                    link_data, _, _ = self.get_data({'id' : links_id, 'fields' : [], 'add_header_row_names' : False, 'text' : True, 'transpose': False}) 
                    self.assign_rgb(link_data)
                    config['connections'] = link_data
        default_options['config_chart'] = config_chart
        html_string = self.canvasXpress_main(default_options) 
        return html_string
    
    def circular_genome(self, **user_options): #TODO: test this method
        default_options = { 'ring_assignation': [], 'ringsType': [], 'ringsWeight': [] }
        default_options.update(user_options)
        
        def config_chart(options, config, samples, variables, values, object_id, x, z):
            config['graphType'] = 'Circular'
            config["arcSegmentsSeparation"] = 3
            config["colorScheme"] = "Tableau"
            config["colors"] = ["#332288","#6699CC","#88CCEE","#44AA99","#117733","#999933","#DDCC77","#661100","#CC6677","#AA4466","#882255","#AA4499"]
            config["showIdeogram"] = True

            coordinates = default_options["genomic_coordinates"]
            chrm = []
            pos = []
            tags2remove = []
            for i, var in enumerate(variables):
                coord = coordinates.get(var)
                if coord != None:
                    tag = re.sub(r"[^\dXY]", "", coord[0])
                    #tag = coord[0].gsub(/[^\dXY]/,'')
                    if tag == 'X' or tag == 'Y' or (int(tag) > 0 and int(tag) <= 22):
                        chrm.append(re.sub(r"[^\dXY]", "", coord[0]))
                        pos.append(coord[-1] - 1)
                    else:
                        tags2remove.append(i)
                else:
                    tags2remove.append(i)
            for i in tags2remove[::-1]:
                ent = variables.pop(i)
                warnings.warn(f"Feature {ent} has not valid coordinates") # Remove entities with invalid coordinates
            z['chr'] = chrm
            z['pos'] = pos
        default_options['config_chart'] = config_chart
        html_string = self.canvasXpress_main(default_options) 

        return html_string

    #-------------------------------------------------------------------------------------
    # CANVASXPRESS METHODS
    #-------------------------------------------------------------------------------------
    def network(self, **user_options):
        options = {
            'id': None,
            'func': None,
            'fields': [],
            'height': '600px',
            'width': '600px',
            'header': False,
            'row_names': False,
            'text' : True,
            'add_header_row_names' : True,
            'transpose': False,
            'method': 'elgrapho',
            'reference_nodes': [],
            'group_nodes': {},
        }
        options.update(user_options)
        net_data = self.hash_vars[options['id']]
        if type(net_data) is list:
            values, _, _, _, _ = self.get_data_for_plot(options)
            if values == None: return f"<div width=\"{options['width']}\" height=\"{options['height']}\" > <p>NO DATA<p></div>"
            graph = nx.Graph()
            graph.add_edges_from([tuple(pair) for pair in values])
            for n in graph.nodes: graph.nodes[n]['layer'] = 'single'
            layers = ['single']
            reference_nodes = options['reference_nodes']
            group_nodes = options['group_nodes']
        elif type(net_data) is dict:
            graph = net_data['graph']
            layers = net_data['layers']
            reference_nodes = net_data['reference_nodes']
            group_nodes = net_data['group_nodes']

        node_names = []
        self.features[options['method']] = True
        if options['method'] == 'cytoscape':
            temp_file = 'cytoscape.txt'
            model = self.cytoscape_network(options, graph, layers, reference_nodes, group_nodes)
        elif options['method'] == 'elgrapho':
            temp_file = 'elgrapho.txt'
            model = self.elgrapho_network(options, graph, layers, reference_nodes, group_nodes)
        elif options['method'] == 'sigma':
            temp_file = 'sigma.txt'
            model = self.sigma_network(options, graph, layers, reference_nodes, group_nodes)
        elif options['method'] == 'pyvis':
            temp_file = 'pyvis.txt'
            model, node_names = self.pyvis_network(options, graph, layers, reference_nodes, group_nodes)
        
        template_file = str(files(Py_report_html.TEMPLATES).joinpath(temp_file))
        templ = Template(filename=template_file) 
        network = base64.b64encode(zlib.compress(json.dumps(model).encode('UTF-8'))).decode('UTF-8')
        string = templ.render(plotter=self, options=options, network=network, count_objects=self.count_objects, node_names=node_names)
        self.count_objects += 1
        return string

    #TODO: test this method
    def get_nodes_colors(self, options, graph, layers, reference_nodes, group_nodes):
        colors = plt.get_cmap("tab10")
        groups_nodes_index = defaultdict(lambda: 0)
        add = 1 if len(reference_nodes) == 0 else 2 # If there are ref nodes, reserve group index 1 for them
        
        if options.get('group') == 'layer':
            for nodeID, attr in graph.nodes(data=True):
                groups_nodes_index[nodeID] = layers.index(attr['layer']) + add
        else:
            if len(group_nodes) > 0: 
                for i, gr in enumerate(group_nodes.values()):
                    for gr_node in gr: groups_nodes_index[gr_node] = i + add
        return groups_nodes_index, lambda color: matplotlib.colors.rgb2hex(colors(color))        

    def cytoscape_network(self, options, graph, layers, reference_nodes, group_nodes):
        model = {'nodes': [], 'edges': []}
        groups_index, get_colors = self.get_nodes_colors(options, graph, layers, reference_nodes, group_nodes)
        for nodeID in graph.nodes:
            color = 1 if nodeID in reference_nodes else groups_index[nodeID]
            model['nodes'].append({  'data': {'id': nodeID}, "style": {"background-color": get_colors(color)}  })
        #for n in graph.nodes: model['nodes'].append({'data': {'id' : n}}) #This is the former loop before adding colors
        for e in graph.edges: model['edges'].append({'data': {'source': e[0], 'target': e[1]}})
        return model 

    def elgrapho_network(self, options, graph, layers, reference_nodes, group_nodes):
        model = {'nodes': [], 'edges': []} 
        if options.get('layout') == 'forcedir':
            model['steps'] = 30 if options.get('steps') == None else options['steps']
        nodesIndex = {}
        groups_index, get_colors = self.get_nodes_colors(options, graph, layers, reference_nodes, group_nodes)
        for i, nodeID in enumerate(graph.nodes):
            nodesIndex[nodeID] = i
            group = 1 if nodeID in reference_nodes else groups_index[nodeID]
            model['nodes'].append({'group': group})
        for e in graph.edges: model['edges'].append({'from': nodesIndex[e[0]], 'to': nodesIndex[e[1]]})
        return model

    def sigma_network(self, options, graph, layers, reference_nodes, group_nodes):
        model = {'nodes': [], 'edges': []} 
        groups_index, get_colors = self.get_nodes_colors(options, graph, layers, reference_nodes, group_nodes)
        for nodeID in graph.nodes:
            color = 1 if nodeID in reference_nodes else groups_index[nodeID]
            model['nodes'].append({'id': nodeID, 'color': get_colors(color), 'x': random.randrange(1000),  'y': random.randrange(1000), 'size': 1})
        for i, e in enumerate(graph.edges): 
            model['edges'].append({'id': i, 'source': e[0], 'target': e[1], 'color': '#202020', 'size': 0.1})
        return model

    def pyvis_network(self, options, graph, layers, reference_nodes, group_nodes):
        model = {'nodes': [], 'edges': []}
        groups_index, get_colors = self.get_nodes_colors(options, graph, layers, reference_nodes, group_nodes)
        node_names = []
        for nodeID in graph.nodes:
            color_group = 1 if nodeID in reference_nodes else groups_index[nodeID]
            model['nodes'].append({'id': nodeID, 'label': nodeID, 'group': color_group, 'color': get_colors(color_group), 'size': 10, 'shape': 'dot'})
            node_names.append(nodeID)

        for i, e in enumerate(graph.edges): 
            model['edges'].append({'from': e[0], 'to': e[1], 'width': 1})
        return model, node_names

    ##################################################################################
    # DIAGRAM CHART REPRESENTATION
    ###################################################################################
    def mermaid_chart(self, chart_sintaxis):
        self.features['mermaid'] = True #Mermaid graph objects
        mermaid_string = f"<pre class=\"mermaid\">\n{chart_sintaxis}\n</pre>"
        return mermaid_string
        
    #################################################################################
    # EMBED FILES
    ###################################################################################

    def embed_img(self, img_file, img_attribs = None, bytesIO = False):
        if bytesIO:
            img_base64 = base64.b64encode(img_file.getvalue()).decode('UTF-8')
            format = "png"
        else:
            with open(img_file, 'rb') as f:
                img_base64 = base64.b64encode(f.read()).decode('UTF-8')
            format = os.path.basename(img_file).split('.')[-1]
        
        img_string = f"<img {img_attribs} src=\"data:image/{format};base64,{img_base64}\">"
        return img_string

    def embed_pdf(self, pdf_file, pdf_attribs = None):
        with open(pdf_file, 'rb') as f:
                pdf_base64 = base64.b64encode(f.read()).decode('UTF-8')
        pdf_string = f"<embed {pdf_attribs} src=\"data:application/pdf;base64,{pdf_base64}\" type=\"application/pdf\"></embed>"
        return pdf_string

    def embed_html(self, html_file, html_attribs = None):
        #with open(html_file, 'rb') as f:
        #        html_base64 = base64.b64encode(f.read()).decode('UTF-8')
        #html_string = f"<embed {html_attribs} src=\"data:text/html;base64,{html_base64}\" type=\"text/html\" height=\"100%\" width=\"100%\" ></embed>"
        html_string = f"<iframe {html_attribs} src=\"{html_file}\" height=\"100%\" width=\"100%\"></iframe>"
        return html_string

    #################################################################################
    # FIGURE AND TABLE NUMBERING
    ###################################################################################
    def add_figure(self, name):
        n_figure = f"{len(self.figures) + 1}"
        self.figures[name] = n_figure
        return n_figure

    def get_figure(self, name):
        n_figure = self.figures.get(name)
        if n_figure == None: n_figure = "NOT FOUND"
        return n_figure

    def add_table(self, name):
        n_table = f"{len(self.tables) + 1}"
        self.tables[name] = n_table
        return n_table

    def get_table(self, name):
        n_table = self.tables.get(name)
        if n_table == None: n_table = "NOT FOUND"
        return n_table

    #################################################################################
    # CLICKABLE ELEMENTS
    ###################################################################################
    def create_title(self, text, id=None, hlevel=1, indexable=True, clickable=False, t_id=None, clickable_text = '(Click me)'):
        if indexable: self.headers.append([id, text, hlevel])
        if clickable:
            header = f"<h{hlevel} id=\"{id}\" class=\"py_accordion\" onclick=\"hide_show_element('{t_id}')\">{text} {clickable_text}</h{hlevel}>"
        else:
            header = f"<h{hlevel} id=\"{id}\">{text}</h{hlevel}>"
        return header

    def create_collapsable_container(self, id, html_code, display='none'): #display ='block'
        return f"<div style=\"display:{display}\" id=\"{id}\">\n{html_code}\n</div>"

    def create_autocomplete_box(self, box_id, item_list, js_function_name, button_text = 'Search'):
        string = (
        f"<div>\n"
            f"<input id=\"{box_id}\" type=\"text\">\n"
            f"<button id=\"button_{box_id}\" onclick=\"{js_function_name}\" class=\"btn btn-secondary\" >{button_text}</button>\n"
        f"</div>\n"
        )
        self.dynamic_js.append(
            (f"document.addEventListener(\"DOMContentLoaded\", function(event){{\n" # Needed to wait to create DOM objects and add listeners to them
                f"autocomplete(document.getElementById(\"{box_id}\"), {self.decompress_code(self.compress_data(item_list))});\n"
            f"}});\n")
        )
        return string

    def create_header_index(self):
        if self.header_index:
            index = f"<h1>Table of contents</h1>\n<div>\n"
            last_level = 0
            for t_id, text, level in self.headers:
                if level > last_level: index += "<ul>\n"
                if level < last_level: 
                    diff = last_level - level
                    for i in range(diff): index += "</ul>\n"
                index += f"<li><a href=#{t_id}>{text}</a></li>\n"
                last_level = level
            index += f"</ul>\n</div>\n"
        else:
            index=''
        return index

    def set_header(self):
        self.header_index = True

        
    ##################################################################################
    # UTILS
    ###################################################################################

    @staticmethod
    def get_color_palette(num, cmap="gist_rainbow"):
        cm = pylab.get_cmap(cmap)
        colors = []
        for i in range(num):
            color = cm(1.*i/num)  # color will now be an RGBA tuple
            colors.append(color)
        return colors