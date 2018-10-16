#!/usr/bin/env python
#
#
# 
import numpy as np
from PIL import Image
import requests
from io import BytesIO

from bokeh.layouts import layout, widgetbox, row, column
from bokeh.models import PolyDrawTool, BoxEditTool, ColumnDataSource
from bokeh.models.widgets import Button, TextInput
from bokeh.plotting import figure, curdoc

_url = 'https://i.redd.it/kri5p84v18s11.jpg'

p = figure(plot_width=800, plot_height=800, x_range=(0, 10), y_range=(0, 10))
url_input = TextInput(value=_url)
get_image = Button(label="Import", button_type="success")
output_image = Button(label="Export", button_type="success")

line_src = ColumnDataSource({'x': [[]], 'y': [[]]})
box_src = ColumnDataSource({'x': [], 'y': [], 'width': [], 'height': []})

curr_image = None
bins = 100

def get_image_size(url):
    """
    Function to get the image size.
    """
    global curr_image
    response = requests.get(url)
    curr_image = Image.open(BytesIO(response.content))
    return curr_image.size

def update_plot():
    global p, url_input
    
    width,height = get_image_size(url_input.value)
    p.image_url(url=[url_input.value], x=[0], y=[0],
                w=width, h=height)
    p.x_range.start = 0
    p.x_range.end = width
    p.y_range.start = -height
    p.y_range.end = 0

def get_cmap():
    """
    Function to get the current cmap line position and query the image
    pixels to build a cmap.
    """
    global curr_image, line_src


get_image.on_click(update_plot)


# init plot
update_plot()

# need lines for cmap and square for image
cmap_line = p.multi_line('x','y', line_width=2, alpha=0.4, source=line_src,
                         color='black')
draw_cmap = PolyDrawTool(renderers=[cmap_line])
renderer = p.rect('x', 'y', 'width', 'height', source=box_src, alpha=0.1)
draw_box = BoxEditTool(renderers=[renderer], empty_value=1)
p.add_tools(draw_cmap, draw_box)
# p.toolbar.active_drag = draw_tool



# l = layout([
#     [get_image, url_input],
#     [p],
#     [output_image]], sizing_mode='stretch_both')
l = layout([
    [get_image, url_input],
    [p],[output_image]])

curdoc().add_root(l)