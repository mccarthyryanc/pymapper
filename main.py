#!/usr/bin/env python
#
#
# 
import numpy as np
from PIL import Image
import requests
from io import BytesIO
from collections import OrderedDict

from bokeh import events
from bokeh.layouts import layout, widgetbox, row, column, Spacer
from bokeh.models import PolyDrawTool, BoxEditTool, ColumnDataSource
from bokeh.models.widgets import Button, TextInput
from bokeh.plotting import figure, curdoc

_url = 'https://i.redd.it/kri5p84v18s11.jpg'

left = figure(plot_width=800, plot_height=800,
              x_range=(0, 10), y_range=(0, 10),
              tools='pan,wheel_zoom,reset,hover,box_select')
right = figure(plot_width=800, plot_height=800,
               x_range=(0, 10), y_range=(0, 10))
url_input = TextInput(value=_url)
cmap_min_input = TextInput(value='-1', title='min')
cmap_max_input = TextInput(value='-1', title='max')
cmap_min_color = TextInput(value='', title='Min Color')
cmap_max_color = TextInput(value='', title='Max Color')
get_image = Button(label="Import", button_type="success")
make_image = Button(label="ReBuild", button_type="success")
output_image = Button(label="Export", button_type="success")

line_src = ColumnDataSource({'x': [[]], 'y': [[]]})
box_src = ColumnDataSource({'x': [], 'y': [], 'width': [], 'height': []})

new_cmap = None
curr_image = None
c_bins = 100
x_bins = 400
y_bins = 800
c_min = 0
c_max = 100

cmap_data = np.array((c_bins, 3), dtype=np.int)
new_raster = np.array((y_bins, x_bins), dtype=np.float)

def line(t,xs,ys):
    x1,x2 = xs
    y1,y2 = ys
    dx = x2-x1
    dy = y2-y1
    x = x1 + t*dx
    y = y1 + t*dy
    return x,y

def get_image_size(url):
    """
    Function to get the image size.
    """
    global curr_image
    response = requests.get(url)
    curr_image = Image.open(BytesIO(response.content))
    return curr_image.size

def update_plot():
    global left, url_input
    
    width,height = get_image_size(url_input.value)
    left.image_url(url=[url_input.value], x=[0], y=[0],
                w=width, h=height)
    left.x_range.start = 0
    left.x_range.end = width
    left.y_range.start = -height
    left.y_range.end = 0

# def set_cmap(event):
#     """
#     Function to set a cmap bound after a DoubleTap event on the
#     image plot
#     """
#     global c_min, c_max



def get_cmap():
    """
    Function to get the current cmap line position and query the image
    pixels to build a cmap.
    """
    global curr_image, line_src, c_min, c_max

    print(f'line Xs: {line_src.data["x"][0]}')

    xs = line_src.data['x'][0]
    ys = line_src.data['y'][0]
    if len(xs) == 0:
        print('No line drawn for color map')
        return

    cmap_pix = (line(t,xs,ys) for t in np.linspace(0,1,bins))
    step = (c_max-c_min)/bins

    new_cmap = OrderedDict()
    for pix, value in zip(cmap_pix, np.arange(c_min, c_max+step, step)):
        new_cmap[curr_image.getpixel(pix)] = value

    print(f'New cmap: {new_cmap}')

def print_event(attributes=[]):
    """
    Function that returns a Python callback to pretty print the events.
    """
    def python_callback(event):
        cls_name = event.__class__.__name__
        attrs = ', '.join(['{attr}={val}'.format(attr=attr,val=event.__dict__[attr])
                       for attr in attributes])
        print('{cls_name}({attrs})'.format(cls_name=cls_name, attrs=attrs))
    return python_callback

# def set_cmap_event():


left.on_event(events.DoubleTap,
              print_event(attributes=['x', 'y']))
left.on_event(events.SelectionGeometry,
              print_event(attributes=['geometry', 'final']))
get_image.on_click(update_plot)
make_image.on_click(get_cmap)

# init plot
update_plot()

# need lines for cmap and square for image
cmap_line = left.multi_line('x','y', line_width=2, alpha=0.4, source=line_src,
                         color='black')
# draw_cmap = PolyDrawTool(renderers=[cmap_line])
# renderer = left.rect('x', 'y', 'width', 'height', source=box_src, alpha=0.1)
# draw_box = BoxEditTool(renderers=[renderer], empty_value=1)
# left.add_tools(draw_cmap, draw_box)

# p.toolbar.active_drag = draw_tool



# l = layout([
#     [get_image, url_input],
#     [left, right],
#     [Spacer(sizing_mode='scale_width'), output_image]
#     ])
l_layout = column([row([get_image, url_input]),
                   row([cmap_min_input, cmap_max_input]),
                   row([cmap_min_color, cmap_max_color]),
                   left,
                   make_image])
r_layout = column([Spacer(sizing_mode='stretch_both'),
                   right,
                   output_image])
l = layout(row(l_layout, r_layout))
curdoc().add_root(l)