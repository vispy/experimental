from vispy import gloo
from vispy import app
import os
import numpy as np
import math

from dash_atlas import DashAtlas
from transforms import orthographic

join = { 'miter' : 0,
         'round' : 1,
         'bevel' : 2 }

caps = { ''             : 0,
         'none'         : 0,
         '.'            : 0,
         'round'        : 1,
         ')'            : 1,
         '('            : 1,
         'o'            : 1,
         'triangle in'  : 2,
         '<'            : 2,
         'triangle out' : 3,
         '>'            : 3,
         'square'       : 4,
         '='            : 4,
         'butt'         : 4,
         '|'            : 5 }
         
def bake(vtype, vertices, closed=False):
    """
    Bake a list of 2D vertices for rendering them as thick line. Each line
    segment must have its own vertices because of antialias (this means no
    vertex sharing between two adjacent line segments).
    """

    n = len(vertices)
    P = np.array(vertices).reshape(n,2).astype(float)

    dx,dy = P[0] - P[-1]
    d = np.sqrt(dx*dx+dy*dy)

    # If closed, make sure first vertex = last vertex (+/- epsilon=1e-10)
    if closed and d > 1e-10:
        P = np.append(P, P[0]).reshape(n+1,2)
        n+= 1

    V = np.zeros(len(P), dtype = vtype)
    V['a_position'] = P

    # Tangents & norms
    T = P[1:] - P[:-1]
    
    N = np.sqrt(T[:,0]**2 + T[:,1]**2)
    # T /= N.reshape(len(T),1)
    V['a_tangents'][+1:, :2] = T
    if closed: V['a_tangents'][0  , :2] = T[-1]
    else:      V['a_tangents'][0  , :2] = T[0]
    V['a_tangents'][:-1, 2:] = T
    if closed: V['a_tangents'][ -1, 2:] = T[0]
    else:      V['a_tangents'][ -1, 2:] = T[-1]

    # Angles
    T1 = V['a_tangents'][:,:2]
    T2 = V['a_tangents'][:,2:]
    A = np.arctan2( T1[:,0]*T2[:,1]-T1[:,1]*T2[:,0],
                    T1[:,0]*T2[:,0]+T1[:,1]*T2[:,1])
    V['a_angles'][:-1,0] = A[:-1] 
    V['a_angles'][:-1,1] = A[+1:]

    # Segment
    L = np.cumsum(N)
    V['a_segment'][+1:,0] = L
    V['a_segment'][:-1,1] = L
    #V['a_lengths'][:,2] = L[-1]

    # Step 1: A -- B -- C  =>  A -- B, B' -- C
    V = np.repeat(V,2,axis=0)[+1:-1]
    V['a_segment'][1:] = V['a_segment'][:-1] 
    V['a_angles'][1:] = V['a_angles'][:-1] 
    V['a_texcoord'][0::2] = -1
    V['a_texcoord'][1::2] = +1

    # Step 2: A -- B, B' -- C  -> A0/A1 -- B0/B1, B'0/B'1 -- C0/C1
    V = np.repeat(V,2,axis=0)
    V['a_texcoord'][0::2,1] = -1
    V['a_texcoord'][1::2,1] = +1

    I = np.resize( np.array([0,1,2,1,2,3], dtype=np.uint32), (n-1)*(2*3))
    I += np.repeat( 4*np.arange(n-1), 6)

    return V, I, L[-1]

vtype = np.dtype( [('a_position', 'f4', 2),
                    ('a_tangents', 'f4', 4),
                    ('a_segment',  'f4', 2),
                    ('a_angles',   'f4', 2),
                    ('a_texcoord', 'f4', 2) ])

x = np.linspace(-1., 1., 1000)
y = .5*np.sin(20*x)
vertices = np.c_[x,y]
            
dash_pattern = 'solid'
linecaps = ('round','round')
dash_caps = ('round', 'round')
linejoin = 'bevel'

da = DashAtlas()
dash_index, dash_period = da[dash_pattern]
u_dash_atlas = da._data

closed = 0.
V,I,length = bake(vtype, vertices, closed=closed)

uniforms = dict(
    u_view = np.eye(4).astype( np.float32 ),
    u_matrix = np.eye(4).astype( np.float32 ),
    closed = closed,
    color = (0.,0.,0.,1),
    linewidth = 10,
    antialias = 1.0,
    miter_limit = 4.0,
    translate = (400.,300.) ,
    scale = 300,
    theta = 0.0,
    dash_phase = 0.0,
    length=length,
    dash_index=dash_index,
    dash_period=dash_period,
    
    linejoin    = join.get(linejoin, 'round'),
    
    linecaps    = (caps.get(linecaps[0], 'round'),
                   caps.get(linecaps[1], 'round')),
                   
    dash_caps   = (caps.get(dash_caps[0], 'round'),
                   caps.get(dash_caps[1], 'round'))
    )


VERT_SHADER = open('path.vert', 'r').read()
FRAG_SHADER = open('path.frag', 'r').read()


class Canvas(app.Canvas):
    def __init__(self):
        app.Canvas.__init__(self, size=(800, 600), close_keys='escape')
        self.program = gloo.Program(VERT_SHADER, FRAG_SHADER)
        self.program.bind(gloo.VertexBuffer(V))
        for n, v in uniforms.iteritems():
            self.program[n] = v
        self.program['u_dash_atlas'] = gloo.Texture2D(u_dash_atlas)
        self.index = gloo.IndexBuffer(I)

    def on_initialize(self, event):
        gloo.set_state(clear_color=(1, 1, 1, 1), blend=True, 
                       blend_func=('src_alpha', 'one_minus_src_alpha'))

    def on_resize(self, event):
        self.width, self.height = event.size
        gloo.set_viewport(0, 0, self.width, self.height)
        self.program['u_proj'] = orthographic( 0, self.width, 0, self.height, -1, +1 ),

    def on_draw(self, event):
        gloo.clear(color=(1.0, 1.0, 1.0, 1.0))
        self.program.draw('triangles', indices=self.index)

c = Canvas()
c.show()
app.run()
