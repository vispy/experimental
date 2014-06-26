import os
import os.path as op
import numpy as np
from scipy import sparse

import mne
import nibabel

from vispy import gloo
from vispy import app
from vispy.util.transforms import perspective, translate, rotate
from vispy.util._geom import _calculate_normals
from vispy.util import get_data_file

def mesh_edges(faces):
    """Returns sparse matrix with edges as an adjacency matrix

    Parameters
    ----------
    faces : array of shape [n_triangles x 3]
        The mesh faces

    Returns
    -------
    edges : sparse matrix
        The adjacency matrix
    """
    npoints = np.max(faces) + 1
    nfaces = len(faces)
    a, b, c = faces.T
    edges = sparse.coo_matrix((np.ones(nfaces), (a, b)),
                              shape=(npoints, npoints))
    edges = edges + sparse.coo_matrix((np.ones(nfaces), (b, c)),
                                      shape=(npoints, npoints))
    edges = edges + sparse.coo_matrix((np.ones(nfaces), (c, a)),
                                      shape=(npoints, npoints))
    edges = edges + edges.T
    edges = edges.tocoo()
    return edges

def smoothing_matrix(vertices, adj_mat, smoothing_steps=20, verbose=None):
    """Create a smoothing matrix which can be used to interpolate data defined
       for a subset of vertices onto mesh with an adjancency matrix given by
       adj_mat.

       If smoothing_steps is None, as many smoothing steps are applied until
       the whole mesh is filled with with non-zeros. Only use this option if
       the vertices correspond to a subsampled version of the mesh.

    Parameters
    ----------
    vertices : 1d array
        vertex indices
    adj_mat : sparse matrix
        N x N adjacency matrix of the full mesh
    smoothing_steps : int or None
        number of smoothing steps (Default: 20)
    verbose : bool, str, int, or None
        If not None, override default verbose level (see surfer.verbose).

    Returns
    -------
    smooth_mat : sparse matrix
        smoothing matrix with size N x len(vertices)
    """

    e = adj_mat.copy()
    e.data[e.data == 2] = 1
    n_vertices = e.shape[0]
    e = e + sparse.eye(n_vertices, n_vertices)
    idx_use = vertices
    smooth_mat = 1.0
    n_iter = smoothing_steps if smoothing_steps is not None else 1000
    for k in range(n_iter):
        e_use = e[:, idx_use]

        data1 = e_use * np.ones(len(idx_use))
        idx_use = np.where(data1)[0]
        scale_mat = sparse.dia_matrix((1 / data1[idx_use], 0),
                                      shape=(len(idx_use), len(idx_use)))

        smooth_mat = scale_mat * e_use[idx_use, :] * smooth_mat

        if smoothing_steps is None and len(idx_use) >= n_vertices:
            break

    # Make sure the smoothing matrix has the right number of rows
    # and is in COO format
    smooth_mat = smooth_mat.tocoo()
    smooth_mat = sparse.coo_matrix((smooth_mat.data,
                                    (idx_use[smooth_mat.row],
                                     smooth_mat.col)),
                                   shape=(n_vertices,
                                          len(vertices)))

    return smooth_mat

filename_lh = 'lh.inflated'
filename_rh = 'rh.inflated'

filename_lhcurv = 'lh.curv'
filename_rhcurv = 'rh.curv'

f = 'meg_source_estimate-lh.stc'

pos, faces = nibabel.freesurfer.read_geometry(filename_lh)

pos /= np.abs(pos).max()

normals = _calculate_normals(pos, faces)

curv = nibabel.freesurfer.io.read_morph_data(filename_lhcurv)

stc = mne.read_source_estimate(f)
stc_vert = stc.lh_vertno
stc_data = stc.lh_data[:,0]
stc_data = (stc_data-stc_data.min())/(stc_data.max()-stc_data.min())

adj_mat = mesh_edges(faces)
smooth_mat = smoothing_matrix(stc.lh_vertno, adj_mat)
a_stc = smooth_mat * stc.lh_data[:,0]
a_stc = (a_stc-a_stc.min())/(a_stc.max()-a_stc.min())

data = np.zeros(len(pos), dtype=[('a_position', 'f4', 3), 
                                 ('a_normal', 'f4', 3),
                                 ('a_curv', 'f4', 1),
                                 ('a_stc', 'f4', 1),
                                 ])
data['a_position'] = pos
data['a_normal'] = normals
data['a_curv'] = curv
data['a_stc'] = a_stc

    
VERT_SHADER = """
uniform mat4 u_model;
uniform mat4 u_view;
uniform mat4 u_projection;
uniform vec4 u_color;

attribute vec3 a_position;
attribute vec3 a_normal;
attribute float a_curv;
attribute float a_stc;

varying vec3 v_position;
varying vec3 v_normal;
varying vec4 v_color;

void main()
{
    v_normal = a_normal;
    v_position = a_position;
    if (a_curv>0.)
        v_color = u_color;
    else
        v_color = .25 * u_color;
        
    v_color = (1.-a_stc)*v_color + a_stc*vec4(1.,0.,0.,0.);
        
    gl_Position = u_projection * u_view * u_model * vec4(a_position,1.0);
}
"""

FRAG_SHADER = """
uniform mat4 u_model;
uniform mat4 u_view;
uniform mat4 u_normal;

uniform vec3 u_light_intensity;
uniform vec3 u_light_position;

varying vec3 v_position;
varying vec3 v_normal;
varying vec4 v_color;

void main()
{
    // Calculate normal in world coordinates
    vec3 normal = normalize(u_normal * vec4(v_normal,1.0)).xyz;

    // Calculate the location of this fragment (pixel) in world coordinates
    vec3 position = vec3(u_view*u_model * vec4(v_position, 1));

    // Calculate the vector from this pixels surface to the light source
    vec3 surfaceToLight = u_light_position - position;

    // Calculate the cosine of the angle of incidence (brightness)
    float brightness = dot(normal, surfaceToLight) /
                      (length(surfaceToLight) * length(normal));
    brightness = max(min(brightness,1.0),0.0);

    // Calculate final color of the pixel, based on:
    // 1. The angle of incidence: brightness
    // 2. The color/intensities of the light: light.intensities
    // 3. The texture and texture coord: texture(tex, fragTexCoord)

    // Specular lighting.
    vec3 surfaceToCamera = vec3(0.0, 0.0, 1.0) - position;
    vec3 K = normalize(normalize(surfaceToLight) + normalize(surfaceToCamera));
    float specular = clamp(pow(abs(dot(normal, K)), 40.), 0.0, 1.0);
    
    gl_FragColor = v_color * brightness * vec4(u_light_intensity, 1) +
                   specular * vec4(1.0, 1.0, 1.0, 1.0);
}
"""


class Canvas(app.Canvas):
    def __init__(self):
        app.Canvas.__init__(self, close_keys='escape')
        self.size = 800, 600

        self.program = gloo.Program(VERT_SHADER, FRAG_SHADER)
        
        self.theta, self.phi = 0, 0
        self.translate = 3
        
        # self.program.bind(gloo.VertexBuffer(data))
        # data['a_position'] = pos
        # data['a_normal'] = normals
        # data['a_curv'] = curv
        # data['a_stc'] = a_stc
        for _ in ('a_position', 'a_normal',
                  'a_curv', 'a_stc'):
            self.program[_] = data[_]
        
        self.faces = gloo.IndexBuffer(faces.ravel().astype(np.uint32))
        
        self.program['u_color'] = 1, 1, 1, 1
        self.program['u_light_position'] = (1., 1., 1.)
        self.program['u_light_intensity'] = (1., 1., 1.)
        
        self.update_matrices()

    def update_matrices(self):
        self.view = np.eye(4, dtype=np.float32)
        self.model = np.eye(4, dtype=np.float32)
        self.projection = np.eye(4, dtype=np.float32)
        
        rotate(self.model, self.theta, 1, 0, 0)
        rotate(self.model, self.phi, 0, 1, 0)
        
        translate(self.view, 0, 0, -self.translate)
        
        self.program['u_model'] = self.model
        self.program['u_view'] = self.view
        self.program['u_normal'] = np.array(np.matrix(np.dot(self.view, 
                                                             self.model)).I.T)
        
    def on_initialize(self, event):
        gloo.set_state(blend=False, depth_test=True, polygon_offset_fill=True)

    def on_mouse_move(self, event):
        if event.is_dragging:
            x0, y0 = event.press_event.pos
            x1, y1 = event.last_event.pos
            x, y = event.pos
            dx, dy = x - x1, y - y1
            self.phi += dx
            self.theta += -dy
            self.update_matrices()
            self.update()

    def on_resize(self, event):
        width, height = event.size
        gloo.set_viewport(0, 0, width, height)
        self.projection = perspective(45.0, width / float(height), 1.0, 20.0)
        self.program['u_projection'] = self.projection

    def on_mouse_wheel(self, event):
        self.translate += -event.delta[1]/5.
        # self.translate = max(2, self.translate)
        self.update_matrices()
        self.update()

    def on_draw(self, event):
        gloo.clear()
        self.program.draw('triangles', indices=self.faces)

if __name__ == '__main__':
    c = Canvas()
    c.show()
    app.run()
    
    from vispy_export import export_canvas_json
    export_canvas_json(c, 'test4.json')

