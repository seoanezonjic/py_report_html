import sys
import os
import json
import base64
import numpy as np
import math
import base64
from mako.template import Template

JS_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'js')
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
            data = self.extract_fields(ids, options.get('fields'), del_fields = options.get('smp_attr'), del_rows = options.get('var_attr'))
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
        indexes.sort(reverse=True)
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
                    indexes = range(1, len(delete_items) +1)
                    self.delete_items(attrib, list(indexes))
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
            'func': None
        }
        options.update(user_options)
        table_attr = self.prepare_table_attribs(options['attrib'])
        array_data, _, _ = self.get_data(options)
        if options.get('func') != None: options['func'](array_data)
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

    #-------------------------------------------------------------------------------------
    # CANVASXPRESS METHODS
    #-------------------------------------------------------------------------------------

    # Support methods
    #-------------------------------------------------------------------------------------
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
            'sample_attributes': {},
            'config': {},
            'after_render': [],
            'treeBy': 's'
        }
        options.update(user_options)
        config = {
            'toolbarType' : 'under',
            'xAxisTitle' : options['x_label'],
            'title' : options['title']
        }
        if  options.get('tree') != None : self.set_tree(options, config)

        config.update(options['config'])
        # Data manipulation
        #------------------------------------------
        no_data_string = f"<div width=\"{options['width']}\" height=\"{options['height']}\" > <p>NO DATA<p></div>"
        data_array, smp_attr, var_attr = self.get_data(options)

        if len(data_array) == 0: return no_data_string 
        if options.get('func') != None: options['func'](data_array)
        if data_array == None: raise Exception(f"ID {options['id']} has not data") 
        samples = data_array.pop(0)
        samples.pop(0) # We obtain sample names with first pop, the second remove vars title
        if len(data_array) == 0: return no_data_string 
        vars = [ row.pop(0) for row in data_array ]
        values = data_array
        object_id = f"obj_{self.count_objects}_"

        x = {}
        z = {}
        if var_attr != None and len(var_attr) > 0: self.add_canvas_attr(x, var_attr) 
        if smp_attr != None and len(smp_attr) > 0: self.add_canvas_attr(z, smp_attr) 
        options['config_chart'](options, config, samples, vars, values, object_id, x, z) # apply custom chart method to configure plot
        # Build JSON objects and Javascript code
        #-----------------------------------------------
        self.count_objects += 1
        data_structure = {
            'y' : {
                'vars' : vars,
                'smps' : samples,
                'data' : values
            },
            'x' : x,
            'z' : z
        }
        events = False
        info = False
        afterRender = options['after_render']
        if options.get('mod_data_structure') == 'boxplot':
            data_structure['y']['smps'] = None
            data_structure.update({ 'x' : {'Factor' : samples}})
        elif options.get('mod_data_structure') == 'circular':
            data_structure.update({ 'z' : {'Ring' : options['ring_assignation']}})

        if len(options['sample_attributes']) > 0: self.add_sample_attributes(data_structure, options) 
        extracode = self.initialize_extracode(options)
        if len(options['segregate']) > 0: extracode += self.segregate_data(f"C{object_id}", options['segregate']) + "\n"
        if options.get('group_samples') != None: extracode += f"C{object_id}.groupSamples({options['group_samples']})\n"
        plot_data = (
            f"var data = {json.dumps(data_structure)};"
            f"var conf = {json.dumps(config)};"
            f"var events = {json.dumps(events)};"
            f"var info = {json.dumps(info)};"
            f"var afterRender = {json.dumps(afterRender)};"
            f"var C{object_id} = new CanvasXpress(\"{object_id}\", data, conf, events, info, afterRender);\n{extracode}")
        self.plots_data.append(plot_data)
        
        responsive = ''
        if options['responsive']: responsive = "responsive='true'" 
        html = f"<canvas  id=\"{object_id}\" width=\"{options['width']}\" height=\"{options['height']}\" aspectRatio='1:1' {responsive}></canvas>"
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

    def reshape(self, samples, vars, x, values):
        item_names = samples.copy()
        for n in range(len(vars) -1 ):
            samples.extend([ f"{i}_{n}" for i in item_names ])
        for factor, annotations in x.items():
            current_annotations = annotations.copy()
            for i in range(len(vars) -1): 
                annotations.extend(current_annotations)
        series_annot = []
        for var in vars:
            for i in item_names:
                series_annot.append(var)
        x['factor'] = series_annot
        vars.clear()
        vars.append('vals')
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
        def config_chart(options, config, samples, vars, values, object_id, x, z):
            config['graphType'] = 'Bar'
        default_options = { 'row_names': True, 'config_chart' : config_chart }
        default_options.update(user_options)
        html_string = self.canvasXpress_main(default_options)
        return html_string

    def line(self, **user_options):
        def config_chart(options, config, samples, vars, values, object_id, x, z):
            config['graphType'] = 'Line'
        default_options = { 'row_names': True, 'config_chart' : config_chart }
        default_options.update(user_options)
        html_string = self.canvasXpress_main(default_options)
        return html_string

    def stacked(self, **user_options):
        def config_chart(options, config, samples, vars, values, object_id, x, z):
            config['graphType'] = 'Stacked'
        default_options = { 'row_names': True, 'config_chart' : config_chart }
        default_options.update(user_options)
        html_string = self.canvasXpress_main(default_options)
        return html_string

    def corplot(self, **user_options):
        default_options = { 'transpose': False, 'correlationAxis': 'samples' }
        default_options.update(user_options)
        def config_chart(options, config, samples, vars, values, object_id, x, z):
            config['graphType'] = 'Correlation'
            config['correlationAxis'] = default_options['correlationAxis']
        default_options['config_chart'] = config_chart
        html_string = self.canvasXpress_main(default_options)
        return html_string

    def pie(self, **user_options): 
        def config_chart(options, config, samples, vars, values, object_id, x, z):
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
        def config_chart(options, config, samples, vars, values, object_id, x, z):
            config['graphType'] = 'Scatter2D'
            if config.get('xAxis') == None: config['xAxis'] = [samples[0]]    
            if config.get('yAxis') == None: config['yAxis'] = [samples[n] for n in range(1, len(samples))] 
            if default_options.get('y_label') == None :
                config['yAxisTitle'] = 'y_axis'
            else:
                config['yAxisTitle'] = default_options['y_label']
            if options.get('regressionLine') == True:
                options['extracode'] = f"C{object_id}.addRegressionLine();"
        default_options['config_chart'] = config_chart
        html_string = self.canvasXpress_main(default_options)
        return html_string

    def scatterbubble2D(self, **user_options):
        default_options = { 'row_names': True, 'transpose': False}
        default_options.update(user_options)
        def config_chart(options, config, samples, vars, values, object_id, x, z):
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
            if default_options.get('y_label') == None:
                config['yAxisTitle'] = 'y_axis'
            else:
                config['yAxisTitle'] = default_options['y_label']
            if default_options.get('z_label') == None:
                config['zAxisTitle'] = 'z_axis'
            else:
                config['zAxisTitle'] = default_options['z_label']
            if options.get('upper_limit') != None and options.get('lower_limit') != None and options.get('ranges') != None:
                diff = (options['upper_limit'] - options['lower_limit'])/options['ranges']
                sizes = [ options['lower_limit'] + n * diff for n in range(options['ranges'])]
                config['sizes'] = sizes
        default_options['config_chart'] = config_chart
        html_string = self.canvasXpress_main(default_options)
        return html_string

    def dotplot(self, **user_options):
        default_options = { 'row_names': True, 'connect': False}
        default_options.update(user_options)
        def config_chart(options, config, samples, vars, values, object_id, x, z):
            config['graphType'] = 'Dotplot'
            if default_options.get('connect'):
                config['dotplotType'] = "stacked"
                config['connectBy'] = "Connect"
                z['Connect'] = [1] * len(vars)
        default_options['config_chart'] = config_chart
        html_string = self.canvasXpress_main(default_options)
        return html_string

    def heatmap(self, **user_options):
        def config_chart(options, config, samples, vars, values, object_id, x, z):
            config['graphType'] = 'Heatmap' 
        default_options = { 'row_names' : True, 'config_chart' : config_chart }
        default_options.update(user_options)
        html_string = self.canvasXpress_main(default_options)
        return html_string

    def boxplot(self, **user_options):
        default_options = { 'row_names' : True, 'header' : True }
        default_options.update(user_options)
        def config_chart(options, config, samples, vars, values, object_id, x, z):
            config['graphType'] = 'Boxplot'
            if default_options.get('group') == None:
                options['mod_data_structure'] = 'boxplot'
            else:
                if type(default_options.get('group')) is str:
                    self.reshape(samples, vars, x, values)
                    group = default_options.get('group')
                    series = 'factor'
                else:
                    series, group = default_options['group']
                if config.get("groupingFactors") == None: # if config is defined, we assume that the user set this property to the value that he/she desires
                    if group == None:
                        config["groupingFactors"] = [series]
                    else:
                        config["groupingFactors"] = [series, group]
                if config.get("colorBy") == None: config["colorBy"] = series 
                if group != None and config.get("segregateSamplesBy") == None: config["segregateSamplesBy"] = [group] 
            if options.get('extracode') == None and default_options.get('group') == None:
                options['extracode'] = f"C{object_id}.groupSamples([\"Factor\"]);"
        default_options['config_chart'] = config_chart
        html_string = self.canvasXpress_main(default_options)
        return html_string

    def circular(self, **user_options):
        default_options = { 'ring_assignation': [], 'ringsType': [], 'ringsWeight': [] }
        default_options.update(user_options)
        def config_chart(options, config, samples, vars, values, object_id, x, z):
            options['mod_data_structure'] = 'circular'
            config['graphType'] = 'Circular'
            config['segregateVariablesBy'] = ['Ring']
            if len(default_options['ringsType']) == 0:
                config['ringGraphType'] = ['heatmap'] * len(vars)
            else:
                config['ringGraphType'] = default_options['ringsType']
            if len(default_options['ringsWeight']) == 0:
                size = math.trunc(100/len(vars))
                config['ringGraphWeight'] = [size] * len(vars)
            else:
                config['ringGraphWeight'] = default_options['ringsWeight']
            if len(default_options['ring_assignation']) == 0:
                options['ring_assignation'] = [ str(i+1) for i in range(len(vars)) ]
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

    ##################################################################################
    # EMBED FILES
    ###################################################################################

    def embed_img(self, img_file, img_attribs = None):
        with open(img_file, 'rb') as f:
                img_base64 = base64.b64encode(f.read()).decode('UTF-8')
        format = os.path.basename(img_file).split('.')[-1]
        img_string = f"<img {img_attribs} src=\"data:image/{format};base64,{img_base64}\">"
        return img_string

    def embed_pdf(self, pdf_file, pdf_attribs = None):
        with open(img_file, 'rb') as f:
                pdf_base64 = base64.b64encode(f.read()).decode('UTF-8')
        pdf_string = f"<embed {pdf_attribs} src=\"data:application/pdf;base64,{pdf_base64}\" type=\"application/pdf\"></embed>"
        return pdf_string
