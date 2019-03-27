# interactive widget bokeh figure
from bokeh.io import curdoc
from bokeh.layouts import row, widgetbox
from bokeh.models import ColumnDataSource, Range1d, LabelSet, Label
from bokeh.models.widgets import Slider, TextInput
from bokeh.plotting import figure

# # data

# x = [-4, 3, 2, 4, 10, 11, -2, 6]
# y = [-3, 2, 2, 9, 11, 12, -5, 6]
# names = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
# colors =['r', 'y', 'y', 'r', 'g', 'g', 'g', 'g']

# # create a CDS by hand
# source = ColumnDataSource(data=dict(x=x, y=y, names=names, colors=colors))

# p = figure(plot_height=400, plot_width=400, title="a little interactive chart",
#            tools="crosshair,pan,reset,save,wheel_zoom",
#            x_range=[-10, 10], y_range=[-10, 10])

# print(p.top_right)
# print(p.top_left)
# print(p.bottom_left)
# print(p.bottom_right)

# # pass the CDS here, and column names (not the arrays themselves)
# p.circle('x', 'y', fill_color="red", line_color="red", size=6, source=source)

# # pass the CDS here too
# labels = LabelSet(x='x', y='y', text='names', level='glyph',
#          x_offset=5, y_offset=5, source=source)
# p.add_layout(labels)

# # Set up widgets
# text = TextInput(title="title", value='a little interavtive chart')

# # Set up callbacks
# def update_title(attrname, old, new):
#     p.title.text = text.value

# text.on_change('value', update_title)

# # # Set up layouts and add to document
# inputs = widgetbox(text)

# curdoc().add_root(row(inputs, p, width=800))
# curdoc().title = "Sliders"

from bokeh.io import output_notebook
from bokeh.palettes import brewer
from bokeh.plotting import figure, show
import pandas
import numpy as np

# Assumes df => data frame with columns: X_Data, Y_Data, Factor

# Create colors for each treatment 
# Rough Source: http://bokeh.pydata.org/en/latest/docs/gallery/brewer.html#gallery-brewer
# Fine Tune Source: http://bokeh.pydata.org/en/latest/docs/gallery/iris.html

# Get the number of colors we'll need for the plot.

doc = curdoc()
doc.title = 'Test'
MAX_X = 10
MAX_Y = 10
myReds = [
    '#000000', '#080000', '#100000', '#180000', '#200000', '#280000', '#300000', 
    '#380000', '#400000', '#480000', '#500000', '#580000', '#600000', '#680000', 
    '#700000', '#780000', '#800000', '#880000', '#900000', '#980000', '#A00000', 
    '#A80000', '#B00000', '#B80000', '#C00000', '#C80000', '#D00000', '#D80000', 
    '#E00000', '#E80000', '#F00000', '#F80000', '#FF0000']

x = np.random.randint(low=1, high=MAX_X, size=20)
y = np.random.randint(low=1, high=MAX_Y, size=20)
print(len(brewer["Spectral"]))
# color = brewer["Spectral"][len(x)]
color = myReds[0:len(x)]
nodes = ['node'+str(i) for i in range(1,21)]
x_label = [item-0.3 for item in x]
y_label = [item+0.8 for item in y]


source = ColumnDataSource(data=dict(x=x, y=y, color=color,nodes=nodes))



# Generate the figure.
p = figure(x_range=(0, MAX_X+1), y_range=(0, MAX_Y+1), plot_width=400, plot_height=400)

# add a circle renderer with a size, color, and alpha
p.circle( x='x', y='y', radius=0.5, fill_color='color',line_color='color',source=source)

# lab = LabelSet(x='x_label', y='y_label',text='nodes',text_font_style='bold',text_color='black',source=source)
# p.add_layout(lab)

doc.add_root(p)



# from bokeh.plotting import figure, show, output_file
# from bokeh.models import ColumnDataSource, Range1d, LabelSet, Label

# doc = curdoc()

# output_file("label.html", title="label.py example")

# source = ColumnDataSource(data=dict(height=[66, 71, 72, 68, 58, 62],
#                                     weight=[165, 189, 220, 141, 260, 174],
#                                     names=['Mark', 'Amir', 'Matt', 'Greg',
#                                            'Owen', 'Juan']))

# p = figure(title='Dist. of 10th Grade Students at Lee High',
#            x_range=Range1d(140, 275))
# p.scatter(x='weight', y='height', size=20, source=source)
# p.xaxis[0].axis_label = 'Weight (lbs)'
# p.yaxis[0].axis_label = 'Height (in)'

# labels = LabelSet(x='weight', y='height', text='names', level='glyph',
#               x_offset=5, y_offset=5, source=source, render_mode='canvas')

# # citation = Label(x=70, y=70, x_units='screen', y_units='screen',
# #                  text='Collected by Luke C. 2016-04-01', render_mode='css',
# #                  border_line_color='black', border_line_alpha=1.0,
# #                  background_fill_color='white', background_fill_alpha=1.0)

# p.add_layout(labels)
# # p.add_layout(citation)

# doc.add_root(p)