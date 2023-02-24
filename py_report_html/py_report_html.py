import os
import json
import base64
from mako.template import Template

JS_FOLDER = os.path.abspath(os.path.join(__file__, '..', '..', '..', 'js'))

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


    def build(self, template):
        templ = Template(template)
        renderered_template = templ.render() #TEMPLATES=Net_plotter.TEMPLATES, options=options, net=self
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
                "<script>\n"
                "    var initPage = function () {\n"
                "        % for plot_data in self.plots_data:\n"
                "            ${plot_data}\n"
                "        % endfor\n"
                "    }\n"
                "</script>\n")

        #DT tables
        if len(self.dt_tables) > 0:
            self.all_report += (
                "<script>\n"
                "    % for dt_table in @dt_tables:\n"
                "        $(document).ready(function () {\n"
                "            $('#${ dt_table }').DataTable();\n"
                "        });\n"
                "    % endfor\n"
                "</script>\n")

        self.all_report +=  "</head>\n"

    def build_body(self, template):
        if len(self.plots_data) > 0:
            self.all_report += f"<body onload=\"initPage();\">\n{template}\n</body>\n"
        else:
            self.all_report += f"<body>\n{template}\n</body>\n"

    def get_report(self): #return all html string
        templ = Template(self.all_report)
        return templ.render()

    def write(self, file):
        with open(file, 'w') as f: f.write(self.get_report())
