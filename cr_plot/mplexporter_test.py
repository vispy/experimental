import string
import random

from mplexporter.exporter import Exporter
from mplexporter.renderers import Renderer, FakeRenderer, FullFakeRenderer

import numpy as np

from plot import PlotCanvas, MarkerVisual, LineVisual

randstr = lambda: ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))

_color_dict = dict(r='#FF0000',
                   g='#00FF00',
                   b='#0000FF',
                   white='#FFFFFF',
                   silver='#C0C0C0',
                   gray='#808080',
                   black='#000000',
                   red='#FF0000',
                   maroon='#800000',
                   yellow='#FFFF00',
                   olive='#808000',
                   lime='#00FF00',
                   green='#008000',
                   aqua='#00FFFF',
                   teal='#008080',
                   blue='#0000FF',
                   navy='#000080',
                   fuchsia='#FF00FF',
                   purple='#800080',
                   )

def _string_to_rgb(color):
    """Convert user string or hex color to color array (length 3 or 4)"""
    if not color.startswith('#'):
        if color.lower() not in _color_dict:
            raise ValueError('Color "%s" unknown' % color)
        color = _color_dict[color]
        assert color[0] == '#'
    # hex color
    color = color[1:]
    lc = len(color)
    if lc in (3, 4):
        color = ''.join(c + c for c in color)
        lc = len(color)
    if lc not in (6, 8):
        raise ValueError('Hex color must have exactly six or eight '
                         'elements following the # sign')
    color = np.array([int(color[i:i+2], 16) / 255. for i in range(0, lc, 2)])
    return color


class VispyRenderer(Renderer):
    def open_figure(self, fig, props):
        """
        Begin commands for a particular figure.

        Parameters
        ----------
        fig : matplotlib.Figure
            The Figure which will contain the ensuing axes and elements
        props : dictionary
            The dictionary of figure properties
        """
        self.canvas = PlotCanvas()

    def close_figure(self, fig):
        """
        Finish commands for a particular figure.

        Parameters
        ----------
        fig : matplotlib.Figure
            The figure which is finished being drawn.
        """
        pass

    def open_axes(self, ax, props):
        """
        Begin commands for a particular axes.

        Parameters
        ----------
        ax : matplotlib.Axes
            The Axes which will contain the ensuing axes and elements
        props : dictionary
            The dictionary of axes properties
        """
        pass

    def close_axes(self, ax):
        """
        Finish commands for a particular axes.

        Parameters
        ----------
        ax : matplotlib.Axes
            The Axes which is finished being drawn.
        """
        pass

    def open_legend(self, legend, props):
        """
        Beging commands for a particular legend.

        Parameters
        ----------
        legend : matplotlib.legend.Legend
                The Legend that will contain the ensuing elements
        props : dictionary
                The dictionary of legend properties
        """
        pass

    def close_legend(self, legend):
        """
        Finish commands for a particular legend.

        Parameters
        ----------
        legend : matplotlib.legend.Legend
                The Legend which is finished being drawn
        """
        pass

    def draw_markers(self, data, coordinates, style, label, mplobj=None):
        """
        Draw a set of markers. By default, this is done by repeatedly
        calling draw_path(), but renderers should generally overload
        this method to provide a more efficient implementation.

        In matplotlib, markers are created using the plt.plot() command.

        Parameters
        ----------
        data : array_like
            A shape (N, 2) array of datapoints.
        coordinates : string
            A string code, which should be either 'data' for data coordinates,
            or 'figure' for figure (pixel) coordinates.
        style : dictionary
            a dictionary specifying the appearance of the markers.
        mplobj : matplotlib object
            the matplotlib plot element which generated this marker collection
        """
        
        pos = data.astype(np.float32)
        n = pos.shape[0]
        
        # TODO: uniform instead
        color = np.tile(_string_to_rgb(style['facecolor']), (n, 1)).astype(np.float32)
        
        # TODO: uniform instead
        size = np.ones(n, np.float32) * style['markersize']
        
        # TODO: marker style, linewidth, linecolor, etc.
        # TODO: take 'coordinates' into account
        
        self.canvas.add_visual(label, 
            MarkerVisual(pos=pos, color=color, size=size))

    def draw_path(self, data, coordinates, pathcodes, style,
                  offset=None, offset_coordinates="data", mplobj=None):
        """
        Draw a path.

        In matplotlib, paths are created by filled regions, histograms,
        contour plots, patches, etc.

        Parameters
        ----------
        data : array_like
            A shape (N, 2) array of datapoints.
        coordinates : string
            A string code, which should be either 'data' for data coordinates,
            'figure' for figure (pixel) coordinates, or "points" for raw
            point coordinates (useful in conjunction with offsets, below).
        pathcodes : list
            A list of single-character SVG pathcodes associated with the data.
            Path codes are one of ['M', 'm', 'L', 'l', 'Q', 'q', 'T', 't',
                                   'S', 's', 'C', 'c', 'Z', 'z']
            See the SVG specification for details.  Note that some path codes
            consume more than one datapoint (while 'Z' consumes none), so
            in general, the length of the pathcodes list will not be the same
            as that of the data array.
        style : dictionary
            a dictionary specifying the appearance of the line.
        offset : list (optional)
            the (x, y) offset of the path. If not given, no offset will
            be used.
        offset_coordinates : string (optional)
            A string code, which should be either 'data' for data coordinates,
            or 'figure' for figure (pixel) coordinates.
        mplobj : matplotlib object
            the matplotlib plot element which generated this path
        """
        pos = data.astype(np.float32)
        n = pos.shape[0]
        
        color = np.array(_string_to_rgb(style['edgecolor']), dtype=np.float32)
        
        self.canvas.add_visual('line'+randstr(), 
            LineVisual(pos=pos, color=color))
        
    def draw_path_collection(self, paths, path_coordinates, path_transforms,
                             offsets, offset_coordinates, offset_order,
                             styles, mplobj=None):
        """
        Draw a collection of paths. The paths, offsets, and styles are all
        iterables, and the number of paths is max(len(paths), len(offsets)).

        By default, this is implemented via multiple calls to the draw_path()
        function. For efficiency, Renderers may choose to customize this
        implementation.

        Examples of path collections created by matplotlib are scatter plots,
        histograms, contour plots, and many others.

        Parameters
        ----------
        paths : list
            list of tuples, where each tuple has two elements:
            (data, pathcodes).  See draw_path() for a description of these.
        path_coordinates: string
            the coordinates code for the paths, which should be either
            'data' for data coordinates, or 'figure' for figure (pixel)
            coordinates.
        path_transforms: array_like
            an array of shape (*, 3, 3), giving a series of 2D Affine
            transforms for the paths. These encode translations, rotations,
            and scalings in the standard way.
        offsets: array_like
            An array of offsets of shape (N, 2)
        offset_coordinates : string
            the coordinates code for the offsets, which should be either
            'data' for data coordinates, or 'figure' for figure (pixel)
            coordinates.
        offset_order : string
            either "before" or "after". This specifies whether the offset
            is applied before the path transform, or after.  The matplotlib
            backend equivalent is "before"->"data", "after"->"screen".
        styles: dictionary
            A dictionary in which each value is a list of length N, containing
            the style(s) for the paths.
        mplobj : matplotlib object
            the matplotlib plot element which generated this collection
        """
        print "path collec"
        
        
def show_vispy(fig):
    renderer = VispyRenderer()
    exporter = Exporter(renderer)
    exporter.run(fig)
    renderer.canvas.show()
    
        
if __name__ == '__main__':
    
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    n = 100
    
    pos = 0.25 * np.random.randn(n, 2).astype(np.float32)
    
    x = np.linspace(-1.0, +1.0, n)
    y = np.random.uniform(-0.5, +0.5, n)
    
    fig, ax = plt.subplots()
    ax.plot(x, y, 'r')
    ax.plot(pos[:,0], pos[:,1], 'ob')
    
    show_vispy(fig)
    