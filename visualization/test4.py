# from tornado import gen
# from functools import partial
# from bokeh.models import Button, NumeralTickFormatter
# from bokeh.palettes import RdYlBu3
# from bokeh.plotting import *
# from bokeh.core.properties import value
# from bokeh.models import ColumnDataSource, Label, Arrow, NormalHead, LabelSet
# from bokeh.models.widgets import DataTable, DateFormatter, TableColumn
# from bokeh.io import output_file, show
# from bokeh.layouts import row
# from bokeh.palettes import Reds9
# from bokeh.transform import factor_cmap
# from bokeh.models import LinearColorMapper

# import itertools
# import paho.mqtt.client as mqtt
# import time
# import numpy as np 
# from bokeh.plotting import figure, show, output_file
# from bokeh.models import ColumnDataSource, ColorBar
# from bokeh.palettes import Spectral6
# from bokeh.transform import linear_cmap

# output_file("styling_linear_mappers.html", title="styling_linear_mappers.py example")

# x = [1,2,3,4,5,7,8,9,10]
# y = [1,2,3,4,5,7,8,9,10]
# t = [1,2,3,4,5,7,8,9,10]

# #Use the field name of the column source
# mapper = linear_cmap(field_name='t',palette=Spectral6 ,low=min(t) ,high=max(t))
# print(mapper)
# mapper = linear_cmap(field_name='y', palette=Spectral6 ,low=min(y) ,high=max(y))
# print(mapper)

# source = ColumnDataSource(dict(x=x,y=y))

# p = figure(plot_width=300, plot_height=300, title="Linear Color Map Based on Y")

# p.circle(x='x', y='y', line_color=mapper,color=mapper, fill_alpha=1, size=12, source=source)

# color_bar = ColorBar(color_mapper=mapper['transform'], width=8,  location=(0,0))

# p.add_layout(color_bar, 'right')

# doc = curdoc()
# doc.add_root(p)


# from random import random
# import numpy as np

# from bokeh.layouts import column, row, widgetbox, layout
# from bokeh.models import Button
# from bokeh.palettes import RdYlBu3
# from bokeh.plotting import figure, curdoc
# from bokeh.models.widgets import MultiSelect, Dropdown, Select
# from bokeh.models import ColumnDataSource
# from bokeh.models.widgets import DataTable, DateFormatter, TableColumn

# p1 = figure(plot_width=300, plot_height=300)
# data = dict(x=[i for i in range(10)], y=[i for i in range(10)])
# source3 = ColumnDataSource(data)
# r1 = p1.circle('x', 'y', size=20, color="navy", alpha=0.5, source=source3)    

# labels = np.array(np.arange(10), dtype=str).tolist()
# menu = [('abc'+each1, 'abc'+each2) for each1, each2 in zip(labels,labels)]
# dropdown = Dropdown(label="Dropdown button", menu=menu)

# data = dict(downloads=['abc'+ str(i) for i in range(30)])
# source = ColumnDataSource(data)
# columns = [TableColumn(field="downloads", title="Downloads")]
# data_table = DataTable(source=source, columns=columns, width=300, height=300,
#                        selectable=True)

# # l = row(widgetbox(dropdown, data_table,width=350), p1)
# l = row(widgetbox(data_table,width=350), p1)
# curdoc().add_root(l)

# from bokeh.models import ColumnDataSource
# from bokeh.models.widgets import DataTable, TableColumn, HTMLTemplateFormatter
# from bokeh.io import curdoc

# dict1 = {
#     'x':[0]*6,
#     'y':[0,1,0,1,0,1]
# }
# source = ColumnDataSource(data=dict1)

# columns = [
#     TableColumn(field="x", title="x"),
#     TableColumn(field="y", title="y")
# ]

# data_table = DataTable(
#     source=source,
#     columns=columns,
#     width=800,
#     editable=True,
# )

# def on_change_data_source(attr, old, new):
#     print('-- OLD DATA: {}'.format(old))
#     print('-- NEW DATA: {}'.format(new))
#     print('-- SOURCE DATA: {}'.format(source.data))

#     # to check changes in the 'y' column:
#     indices = list(range(len(old['y'])))
#     changes = [(i,j,k) for i,j,k in zip(indices, old['y'], new['y']) if j != k]
#     if changes != []:
#         for t in changes:  # t = (index, old_val, new_val)
#             patch = {
#                 'y' : [(t[0], int(t[2])), ]   # the new value is received as a string
#             }
#             source.patch(patch)   # this will call to this callback again, ugly
#                                   # so you will need to update the values on another source variable
#         print('-- SOURCE DATA AFTER PATCH: {}'.format(source.data))

# source.on_change('data', on_change_data_source)

# curdoc().add_root(data_table)

# from bokeh.io import curdoc
# from bokeh.layouts import layout,row
# from bokeh.models import HoverTool,ColumnDataSource,Button,Select,TextInput,Slider,DataTable,TableColumn,DateFormatter,LinearAxis,Range1d,CustomJS,Rect
# from bokeh.plotting import figure,output_file,show
# from datetime import datetime, timedelta
# from bokeh.client import push_session
# import pandas as pd
# import numpy as np


# TOOLS='pan,wheel_zoom,box_zoom,reset,tap,save,lasso_select,xbox_select'

# # Select widget
# menu = Select(options=['AUDUSD','USDJPY'], value='USDJPY')

# # Function to get Order/Trade/Price Datasets
# def get_order_dataset(src,name):
#     df = src[(src.CCYPAIR == name) & (src.TYPE == 'ORDER') & (src.SIDE == 'B')].copy()
#     return ColumnDataSource(data=df)

# # Function to Make Plots
# def make_plot(source_order):
#     x  = 'DATE'
#     y  = 'PRICE'
#     size = 10
#     alpha = 0.5
#     hover = HoverTool(
#     tooltips = [
#         ('OrderId', '@ORDER_ID_108'),
#         ('Volume', '@Volume'),
#         ('Price', '@PRICE')
#         ]
#     )

#     plot = figure(plot_width=1000, plot_height=300, tools=[hover, TOOLS], 
#        title='Order/Execution Snapshot with Price Levels',
#        x_axis_label='Date', y_axis_label='Price',x_axis_type="datetime",active_drag="xbox_select")

#     plot.circle(x=x, y=y, size=size, alpha=alpha, color='blue',
#             legend='Orders', source=source_order,selection_color="orange")
#     plot.legend.location = 'top_left'
#     return plot

# def update_plot(attrname, old, new):
#     newccy = menu.value
#     src_order = get_order_dataset(Combined,newccy)
#     source_order.data.update(src_order.data)


# date_today = datetime.now()
# days = pd.date_range(date_today, date_today + timedelta(2), freq='D')
# Combined1 = {'DATE': days,
#      'CCYPAIR': ['USDJPY', 'USDJPY', 'USDJPY'],
#      'SIDE' : ['B', 'B', 'B'],
#      'PRICE': [100.00, 200.00, 300.00],
#      'TYPE' : ['ORDER', 'ORDER', 'ORDER'],
#      'Volume': [100, 200, 300],
#      'ORDER_ID_108':  [111,222,333]
#        }
# Combined = pd.DataFrame(Combined1)

# source_order = get_order_dataset(Combined,menu.value)

# plot =  make_plot(source_order)
# menu.on_change('value', update_plot)

# s2 = ColumnDataSource(data=dict(DATE=[], PRICE=[]))
# p2 = figure(plot_width=1000, plot_height=400,
#     tools="", title="Watch Here",x_axis_type="datetime", y_range=(90,310),x_range=(days[0],days[-1]))
# p2.circle('DATE', 'PRICE', source=s2, alpha=0.6, size=10)

# source_order.callback = CustomJS(args=dict(s2=s2), code="""
# var inds = cb_obj.selected['1d'].indices;
# console.log(inds)
# var d1 = cb_obj.data;
# var d2 = s2.data;
# d2['DATE'] = []
# d2['PRICE'] = []
# for (i = 0; i < inds.length; i++) {
#     d2['DATE'].push(d1['DATE'][inds[i]])
#     d2['PRICE'].push(d1['PRICE'][inds[i]])
# }
# s2.change.emit();""")

# layout = layout([menu],
#         [plot],
#         [p2])
# curdoc().add_root(layout)

# from bokeh.io import curdoc
# from bokeh.models.widgets import Div, Button
# from bokeh.layouts import row, widgetbox
# from bokeh.models import ColumnDataSource, Slider
# from bokeh.plotting import figure

# notifications = Div(text='initial text')#, name=name, width=width, height=height)
# button = Button(label="Click me to add text")
# def callback():
#     notifications.text += 'more text' + '</br>'
# button.on_click(callback)

# # Set up layout and add to document
# box = widgetbox(notifications, button)
# curdoc().add_root(row(box))


# from datetime import date
# from random import randint
# from bokeh.models import ColumnDataSource
# from bokeh.models.widgets import DataTable, DateFormatter, TableColumn

# import bokeh.layouts as layouts
# import bokeh.models.widgets as widgets
# from bokeh.io import curdoc

# # from bokeh.models.glyphs import Line
# # from bkcharts import Line
# import numpy as np
# from bokeh.plotting import figure

# data = dict(
#     dates=[date(2014, 3, i + 1) for i in range(10)],
#     downloads=[randint(0, 100) for i in range(10)],
# )
# d_source = ColumnDataSource(data)

# columns = [
#     TableColumn(field="dates", title="Date", formatter=DateFormatter()),
#     TableColumn(field="downloads", title="Downloads"),
# ]

# data_table = DataTable(source=d_source, columns=columns, width=400, height=280)
# #data_table.row_headers = False


# def table_select_callback(attr, old, new):
#     # print 'here'
#     # print new
#     # selected_row = new['1d']['indices'][0]
#     selected_row = new[0]
#     download_count = data['downloads'][selected_row]
#     chart_data = np.random.uniform(0, 100, size=download_count)
#     p = figure(title='bla')
#     r = p.line(x=range(len(chart_data)), y=chart_data)
#     root_layout.children[1] = p

# # d_source.on_change('selected', table_select_callback)
# d_source.selected.on_change('indices', table_select_callback)

# root_layout = layouts.Column(data_table, widgets.Div(text='Select Date'))
# curdoc().add_root(root_layout)

# from os.path import dirname, join

# import pandas as pd

# from bokeh.layouts import row, column
# from bokeh.models import ColumnDataSource, CustomJS
# from bokeh.models.widgets import RangeSlider, Button, DataTable, TableColumn, NumberFormatter
# from bokeh.io import curdoc

# df = pd.read_csv(join(dirname(__file__), 'salary_data.csv'))

# source = ColumnDataSource(data=dict())

# def update():
#     current = df[(df['salary'] >= slider.value[0]) & (df['salary'] <= slider.value[1])].dropna()
#     source.data = {
#         'name'             : current.name,
#         'salary'           : current.salary,
#         'years_experience' : current.years_experience,
#     }

# slider = RangeSlider(title="Max Salary", start=10000, end=110000, value=(10000, 50000), step=1000, format="0,0")
# slider.on_change('value', lambda attr, old, new: update())

# button = Button(label="Download", button_type="success")
# button.callback = CustomJS(args=dict(source=source),
#                            code=open(join(dirname(__file__), "download.js")).read())

# columns = [
#     TableColumn(field="name", title="Employee Name"),
#     TableColumn(field="salary", title="Income", formatter=NumberFormatter(format="$0,0.00")),
#     TableColumn(field="years_experience", title="Experience (years)")
# ]

# data_table = DataTable(source=source, columns=columns, width=800)

# controls = column(slider, button)

# curdoc().add_root(row(controls, data_table))
# curdoc().title = "Export CSV"

# update()

# from bokeh.layouts import row
# from bokeh.models.widgets import MultiSelect
# from bokeh.io import curdoc
# from bokeh.models import ColumnDataSource, HoverTool
# from bokeh.plotting import figure

# import pandas as pd

# df_test = pd.DataFrame({
#     'x': [1, 2, 3, 4],
#     'height': [2, 3, 4, 5],
#     'col1': ['a', 'b', 'c', 'd'],
#     'col2': [2, 4, 6, 8],
#     'col3': ['mon', 'tues', 'wed', 'fri']
# })
# df_test['y'] = df_test.height / 2.0

# # facets select
# ms = MultiSelect(title="column selection",
#                  options=['col1', 'col2', 'col3'],
#                  value=[], width=200)

# def create_plot():
#     # create data source for plot based on multi select values
#     v = ms.value
#     df_plot = df_test[['x', 'y', 'height']+v]
#     datasource = ColumnDataSource(df_plot)
#     # create figure for plot and add glyphs
#     # took out x_range=datasource.data['x'], x_range takes only takes a tuple or range model
#     p = figure(width=800, height=500)
#     p.rect(x="x", y="y", width=0.8, height="height",
#            source=datasource, color="#2171b5", alpha=0.6)
#     # create hover tool based on multi select values
#     tt = [(x, '@'+x) for x in v]
#     p.add_tools(HoverTool(tooltips=[("x", "@x"), ("y", "@y")]+tt))
#     return p

# def update(attribute, old, new):
#     # replace the plot in our layout with a shiny new plot
#     l.children[1] = create_plot()

# ms.on_change('value', update)

# # changed layout to row, for my own familiarty
# l = row(ms, create_plot())

# curdoc().add_root(l)
# curdoc().title = "bokeh app"

''' Present an interactive function explorer with slider widgets.
Scrub the sliders to change the properties of the ``sin`` curve, or
type into the title text box to update the title of the plot.
Use the ``bokeh serve`` command to run the example by executing:
    bokeh serve sliders.py
at your command prompt. Then navigate to the URL
    http://localhost:5006/sliders
in your browser.
'''
# import numpy as np

# from bokeh.io import curdoc
# from bokeh.layouts import row, column
# from bokeh.models import ColumnDataSource
# from bokeh.models.widgets import Slider, TextInput
# from bokeh.plotting import figure

# # Set up data
# N = 200
# x = np.linspace(0, 4*np.pi, N)
# y = np.sin(x)
# source = ColumnDataSource(data=dict(x=x, y=y))


# # Set up plot
# plot = figure(plot_height=400, plot_width=400, title="my sine wave",
#               tools="crosshair,pan,reset,save,wheel_zoom",
#               x_range=[0, 4*np.pi], y_range=[-2.5, 2.5])

# plot.line('x', 'y', source=source, line_width=3, line_alpha=0.6)


# # Set up widgets
# text = TextInput(title="title", value='my sine wave')
# offset = Slider(title="offset", value=0.0, start=-5.0, end=5.0, step=0.1)
# amplitude = Slider(title="amplitude", value=1.0, start=-5.0, end=5.0, step=0.1)
# phase = Slider(title="phase", value=0.0, start=0.0, end=2*np.pi)
# freq = Slider(title="frequency", value=1.0, start=0.1, end=5.1, step=0.1)


# # Set up callbacks
# def update_title(attrname, old, new):
#     plot.title.text = text.value

# text.on_change('value', update_title)

# def update_data(attrname, old, new):

#     # Get the current slider values
#     a = amplitude.value
#     b = offset.value
#     w = phase.value
#     k = freq.value

#     # Generate the new curve
#     x = np.linspace(0, 4*np.pi, N)
#     y = a*np.sin(k*x + w) + b

#     source.data = dict(x=x, y=y)

# for w in [offset, amplitude, phase, freq]:
#     w.on_change('value', update_data)


# # Set up layouts and add to document
# inputs = column(text, offset, amplitude, phase, freq)

# curdoc().add_root(row(inputs, plot, width=800))
# curdoc().title = "Sliders"

# Set up data
N = 200
x = np.linspace(0, 4*np.pi, N)
y = np.sin(x)
s = np.ones_like(y) * 6
source = ColumnDataSource(data=dict(x=x, y=y, size=s))
r = plot.circle('x', 'y', size='size', source=source, 
                line_alpha=0.6, color = text3.value, legend = 'test')
def update_size(attrname, old, new):
    source.data['size'] = np.ones_like(y) * int(text2.value)
