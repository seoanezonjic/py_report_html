import sys
import os
import json
import base64
import numpy as np
from mako.template import Template


JS_FOLDER = os.path.abspath(os.path.join(__file__, '..', '..', '..', 'js'))
TEMPLATES = os.path.join(os.path.dirname(__file__), 'templates')

class Py_report_html:

    def __init__(self, hash_vars, title = "report", data_from_files = False):
        self.all_report = ""
        self.title = title
        self.hash_vars = hash_vars
        self.data_from_files = data_from_files
        self.plots_data = []
        self.count_objects = 0
        self.dt_tables = [] #Tables to be styled with the DataTables js lib"
        self.bs_tables = [] #Tables to be styled with the bootstrap js lib"

    ###################################################################################
    # RENDER TEMPLATE METHODS
    ###################################################################################

    def build(self, template):
        templ = Template(template)
        renderered_template = templ.render(plotter=self)
        self.all_report += "<HTML>\n"
        self.make_head()
        self.build_body(renderered_template)
        self.all_report += "\n</HTML>"

    def load_js_libraries(self, js_libraries):
        loaded_libraries = []
        for js_lib in js_libraries:
            with open(os.path.join(JS_FOLDER, js_lib), 'rb') as f:
                loaded_libraries.append(base64.b64encode(f.read()).decode('UTF-8'))
        return loaded_libraries

    def load_css(self, css_files):
        loaded_css = []
        for css_lib in css_files:
            with open(os.path.join(JS_FOLDER, css_lib), 'r') as f:
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
        js_libraries = []
        css_files = []
        if len(self.plots_data) > 0:
            js_libraries.append('canvasXpress.min.js')
            css_files.append('canvasXpress.css')

        if len(self.dt_tables) > 0 or len(self.bs_tables) > 0: #Bootstrap for datatables or only for static tables. Use bootstrap version needed by datatables to avoid incompatibility issues
            self.all_report += '<link rel="stylesheet" type="text/css" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css"/>'+"\n"

        if len(self.dt_tables) > 0: # CDN load, this library is difficult to embed in html file
            self.all_report += '<link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.10.21/css/dataTables.bootstrap.min.css"/>'+"\n"
            self.all_report += '<script type="text/javascript" src="https://code.jquery.com/jquery-3.5.1.js"></script>' + "\n"
            self.all_report += '<script type="text/javascript" src="https://cdn.datatables.net/1.10.21/js/jquery.dataTables.min.js"></script>' + "\n"
            self.all_report += '<script type="text/javascript" src="https://cdn.datatables.net/1.10.21/js/dataTables.bootstrap.min.js"></script>' + "\n"

        # TODO add Pako library to handle compressed data
        loaded_js_libraries = self.load_js_libraries(js_libraries)
        loaded_css = self.load_css(css_files)
        for css in loaded_css:
            self.all_report += (
                f"<style type=\"text/css\"/>\n"
                f"{css}"
                f"\n</style>\n\n")
        for lib in loaded_js_libraries:
            self.all_report += f"<script src=\"data:application/javascript;base64,{lib}\" type=\"application/javascript\"></script>\n\n"
        
        # ADD CUSTOM FUNCTIONS TO USE LOADED JS LIBRARIES
        #canvasXpress objects
        if len(self.plots_data) > 0:
            self.all_report += (
                f"<script>\n"
                f"    var initPage = function () {{\n"
                f"        % for plot_data in plotter.plots_data:\n"
                f"            ${{plot_data}}\n"
                f"        % endfor\n"
                f"    }}\n"
                f"</script>\n")

        #DT tables
        if len(self.dt_tables) > 0:
            self.all_report += (
                f"<script>\n"
                f"    % for dt_table in plotter.dt_tables:\n"
                f"        $(document).ready(function () {{\n"
                f"            $('#${{ dt_table }}').DataTable();\n"
                f"        }});\n"
                f"    % endfor\n"
                f"</script>\n")

        self.all_report +=  "</head>\n"

    def build_body(self, template):
        if len(self.plots_data) > 0:
            self.all_report += f"<body onload=\"initPage();\">\n{template}\n</body>\n"
        else:
            self.all_report += f"<body>\n{template}\n</body>\n"

    def get_report(self): #return all html string
        templ = Template(self.all_report)
        return templ.render(plotter=self)

    def write(self, file):
        with open(file, 'w') as f: f.write(self.get_report())

    ###################################################################################
    # REPORT SYNTAX METHODS
    ###################################################################################

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
                if text == None or not text:
                    for r in range(rows):
                        for c in range(cols):
                            if r == 0 and options['header']: continue 
                            if c == 0 and options['row_names']: continue 
                            data[r][c] = float(data[r][c])

            self.add_header_row_names(data, options)
            if options['transpose']:
                data = np.array(data).T.tolist()
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

    def extract_data(self, options):
        data = []
        smp_attr = None
        var_attr = None
        ids = options['id']
        if type(ids) is str and ',' in ids: ids = ids.split(',')  # String syntax
        fields = options['fields']
        if type(ids) is list:
            if type(fields) is str: fields = [ [int(n) for n in data_fields.split(',') ] for data_fields in fields.split(';') ] # String syntax
            for n,id in enumerate(ids):
                data_file = self.extract_fields(id, fields[n])
                if len(data) == 0:
                    data.extend(data_file)
                else:
                    for n, row in enumerate(data):
                        data[n] = row + data_file[n]
        else:
            if 'smp_attr' in options and len(options['smp_attr']) > 0: smp_attr = self.process_attributes(self.extract_fields(ids, options['smp_attr']), options['var_attr'], aggregated = True) 
            if 'var_attr' in options and len(options['var_attr']) > 0: var_attr = self.process_attributes(self.extract_rows(ids, options['var_attr']), options['smp_attr'], aggregated = False) 
            data = self.extract_fields(ids, options['fields'], del_fields = options['smp_attr'], del_rows = options['var_attr'])
        return data, smp_attr, var_attr

    def extract_fields(self, id, fields, del_fields = [], del_rows = []):
        data = []
        for i, row in enumerate(self.hash_vars[id]):
            if del_rows != None and i in del_rows: continue 
            if len(fields) == 0:
                row = row.copy() # Copy generates a array copy that avoids to modify original objects on data manipulation creating graphs
                if del_fields != None: self.delete_items(row, del_fields)
                data.append(row)
            else:
                data.append([ row[field] for field in fields ]) # new list with extracted fields
        return data

    def delete_items(self, list2del, indexes):
        indexes.sort()
        indexes.reverse()
        for j in indexes: list2del.pop(j)        

    def extract_rows(self, id, rows):
        table = self.hash_vars[id]
        data = [ table[field] for field in rows ]
        return data

    def process_attributes(self, attribs, delete_items, aggregated = False):
        parsed_attr = []
        if aggregated:
            if delete_items != None and len(delete_items) > 0:
                indexes = [1] * len(delete_items)
                self.delete_items(attribs, indexes)
            for i in range(len(attribs[0])):
                parsed_attr.append([ at[i] for at in attribs ])
        else:
            for attrib in attribs:
                if delete_items != None and len(delete_items) > 0:
                    indexes = range(len(delete_items))
                    self.delete_items(attrib, indexes)
                parsed_attr.append(attrib)
        return parsed_attr

    # TABLE METHODS
    #-------------------------------------------------------------------------------------
    def table(self, **user_options): # , &block # https://treyhunner.com/2018/04/keyword-arguments-in-python/#Capturing_arbitrary_keyword_arguments
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
            'func': None
        }
        options.update(user_options)
        table_attr = self.prepare_table_attribs(options['attrib'])
        array_data, _, _ = self.get_data(options)
        if options.get('func') != None: options['func'](array_data)
        #block.call(array_data) if !block.nil? # TODO: hacer q reciba funciones para modificar datos de la tabla
        rowspan, colspan = self.get_col_n_row_span(array_data)
        table_id = 'table_' + str(self.count_objects)
        if options.get('styled') == 'dt': self.dt_tables.append(table_id) 
        if options.get('styled') == 'bs': self.bs_tables.append(table_id) 
        self.count_objects += 1
        templ = Template(filename=os.path.join(TEMPLATES, 'table.txt'))
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

    # CANVASXPRESS METHODS
    #-------------------------------------------------------------------------------------