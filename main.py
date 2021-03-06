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
new_cmap = None
curr_image = None
c_bins = 256
x_bins = 300
y_bins = 800
c_flag = True
white_threshold = 20
img = np.ones((y_bins,x_bins))*np.nan
cmap_data = np.array((c_bins, 3), dtype=np.int)
new_raster = np.array((y_bins, x_bins), dtype=np.float)

left = figure(plot_width=800, plot_height=800,
              x_range=(0, 10), y_range=(0, 10),
              tools='pan,wheel_zoom,reset,hover,box_select')
right = figure(plot_width=800, plot_height=800,
               x_range=(0, x_bins), y_range=(0, y_bins))
url_input = TextInput(value=_url)
cmap_min_input = TextInput(value='-78.8', title='min')
cmap_max_input = TextInput(value='-40.0', title='max')
cmap_min_c_pos = TextInput(value='', title='Min Color Pos')
cmap_max_c_pos = TextInput(value='', title='Max Color Pos')
get_image = Button(label="Import", button_type="success")
make_image = Button(label="ReBuild", button_type="success")
output_image = Button(label="Export", button_type="success")

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

def color_dist_sq(x,y):
    """
    Simple squared euclidean distance for color tuples
    """
    return (x[0]-y[0])**2 + (x[1]-y[1])**2 + (x[2]-y[2])**2

def update_image():
    global left, url_input

    print('updating left image')
    
    width,height = get_image_size(url_input.value)
    left.image_url(url=[url_input.value], x=[0], y=[0],
                w=width, h=height)
    left.x_range.start = 0
    left.x_range.end = width
    left.y_range.start = -height
    left.y_range.end = 0

def update_plot():
    global right, img
    print('updating right plot')
    right.image(image=[img], x=0, y=0, dw=x_bins, dh=y_bins,
                palette="Viridis256")


def build_image(event):
    """
    Function to build a new image after rectangular selection event 
    """
    global new_cmap, curr_image, img, right

    # First get the image pix bounds
    x0 = event.__dict__['geometry']['x0']
    x1 = event.__dict__['geometry']['x1']
    y0 = abs(event.__dict__['geometry']['y0'])
    y1 = abs(event.__dict__['geometry']['y1'])
    
    print(f'building : {x0}-{x1}, {y0}-{y1}')

    for j,img_j in enumerate(np.linspace(x0,x1,x_bins)):
        for i,img_i in enumerate(np.linspace(y0,y1,y_bins)):
            # print(f'looking at pixel({i},{j})')
            # get the pixel value at i,j pixel
            c = curr_image.getpixel((int(img_j),int(img_i)))
            # get the closest non-white color
            if color_dist_sq((255,255,255),c) < white_threshold:
                value = np.nan
            else:
                nearest = min(new_cmap.keys(), key=lambda x: color_dist_sq(x,c))
                value = new_cmap[nearest]
            # print(f'got value: {value}')
            img[i,j] = value

    print('finished rebuilding image')
    update_plot()

def get_cmap():
    """
    Function to get the current cmap line position and query the image
    pixels to build a cmap.
    """
    global curr_image, c_min, c_max, cmap_min_c_pos, cmap_max_c_pos, new_cmap

    print(f'building new color map')

    c_min = float(cmap_min_input.value)
    c_max = float(cmap_max_input.value)

    min_pos = [int(i) for i in cmap_min_c_pos.value.split(',')]
    max_pos = [int(i) for i in cmap_max_c_pos.value.split(',')]

    xs = [min_pos[0], max_pos[0]]
    ys = [min_pos[1], max_pos[1]]

    cmap_pix = (line(t,xs,ys) for t in np.linspace(0,1,c_bins))
    step = (c_max-c_min)/c_bins

    new_cmap = OrderedDict()
    for pix, value in zip(cmap_pix, np.arange(c_min, c_max+step, step)):
        new_cmap[curr_image.getpixel(pix)] = value

def set_colorbar(event):
    """
    Set the min/max color values after a double-click event.
    """
    global c_flag, curr_image, cmap_min_c_pos, cmap_max_c_pos

    if c_flag:
        print('setting colorbar start location')
    else:
        print('setting colorbar end location')

    # get the x,y coords of the event
    x = int(event.__dict__['x'])
    y = abs(int(event.__dict__['y']))

    # index the image to get the color
    if c_flag:
        cmap_min_c_pos.value = f'{x},{y}'
    else:
        cmap_max_c_pos.value = f'{x},{y}'
        get_cmap()
    c_flag = not c_flag

# def print_event(attributes=[]):
#     """
#     Function that returns a Python callback to pretty print the events.
#     """
#     def python_callback(event):
#         cls_name = event.__class__.__name__
#         attrs = ', '.join(['{attr}={val}'.format(attr=attr,val=event.__dict__[attr])
#                        for attr in attributes])
#         print('{cls_name}({attrs})'.format(cls_name=cls_name, attrs=attrs))
#     return python_callback

left.on_event(events.DoubleTap, set_colorbar)
left.on_event(events.SelectionGeometry, build_image)
get_image.on_click(update_image)

# init plot
update_image()
update_plot()

l_layout = column([row([get_image, url_input]),
                   row([cmap_min_input, cmap_max_input]),
                   row([cmap_min_c_pos, cmap_max_c_pos]),
                   left])
r_layout = column([Spacer(sizing_mode='stretch_both'),
                   right,
                   output_image])
l = layout(row(l_layout, r_layout))
curdoc().add_root(l)