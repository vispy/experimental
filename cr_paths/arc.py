import math
import numpy as np

def elliptical_arc(x0, y0, rx, ry, angle, large_arc_flag, sweep_flag, x2, y2):
    """
    """

    radii_ok = True
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    if rx < 0.0: rx = -rx
    if ry < 0.0: ry = -rx

    # Calculate the middle point between 
    # the current and the final points
    # ------------------------
    dx2 = (x0 - x2) / 2.0
    dy2 = (y0 - y2) / 2.0

    # Calculate (x1, y1)
    # ------------------------
    x1 =  cos_a * dx2 + sin_a * dy2
    y1 = -sin_a * dx2 + cos_a * dy2

    # Check that radii are large enough
    # ------------------------
    prx,pry = rx * rx, ry * ry
    px1,py1 = x1 * x1, y1 * y1

    radii_check = px1/prx + py1/pry
    if radii_check > 1.0:
        rx = math.sqrt(radii_check) * rx
        ry = math.sqrt(radii_check) * ry
        prx = rx * rx
        pry = ry * ry
        if radii_check > 10.0:
            radii_ok = False

    # Calculate (cx1, cy1)
    # ------------------------
    if large_arc_flag == sweep_flag:
        sign = -1
    else:
        sign = +1
    sq   = (prx*pry - prx*py1 - pry*px1) / (prx*py1 + pry*px1)
    coef = sign*math.sqrt( max(sq,0) )
    cx1  = coef *  ((rx * y1) / ry)
    cy1  = coef * -((ry * x1) / rx)

    # Calculate (cx, cy) from (cx1, cy1)
    # ------------------------
    sx2 = (x0 + x2) / 2.0
    sy2 = (y0 + y2) / 2.0
    cx = sx2 + (cos_a * cx1 - sin_a * cy1)
    cy = sy2 + (sin_a * cx1 + cos_a * cy1)

    # Calculate the start_angle (angle1) and the sweep_angle (dangle)
    # ------------------------
    ux =  (x1 - cx1) / rx
    uy =  (y1 - cy1) / ry
    vx = (-x1 - cx1) / rx
    vy = (-y1 - cy1) / ry

    # Calculate the angle start
    # ------------------------
    n = math.sqrt(ux*ux + uy*uy)
    p = ux;
    if uy < 0:
        sign = -1.0
    else:
        sign = +1.0
    v = p / n
    if v < -1.0:
        v = -1.0
    if v >  1.0:
        v =  1.0
    start_angle = sign * math.acos(v)

    # Calculate the sweep angle
    # ------------------------
    n = math.sqrt((ux*ux + uy*uy) * (vx*vx + vy*vy))
    p = ux * vx + uy * vy
    if ux * vy - uy * vx < 0:
        sign = -1.0
    else:
        sign = +1.0
    v = p / n
    v = min(max(v,-1.0),+1.0)
    sweep_angle = sign * math.acos(v)
    if not sweep_flag and sweep_angle > 0:
        sweep_angle -= math.pi * 2.0
    elif sweep_flag and sweep_angle < 0:
        sweep_angle += math.pi * 2.0

    start_angle = math.fmod(start_angle, 2.0 * math.pi)
    if sweep_angle >=  2.0 * math.pi:
        sweep_angle =  2.0 * math.pi
    if sweep_angle <= -2.0 * math.pi:
        sweep_angle = -2.0 * math.pi

    V = arc( cx, cy, rx, ry, start_angle, start_angle+sweep_angle, sweep_flag )
    c = math.cos(angle)
    s = math.sin(angle)
    X,Y = V[:,0]-cx, V[:,1]-cy
    V[:,0] = c*X - s*Y + cx
    V[:,1] = s*X + c*Y + cy
    return V


def arc(cx, cy, rx, ry, a1, a2, ccw=False):
    """
    """
    scale = 1.0
    ra = (abs(rx) + abs(ry)) / 2.0
    da = math.acos(ra / (ra + 0.125 / scale)) * 2.0
    if ccw:
        while a2 < a1:
            a2 += math.pi * 2.0
    else:
        while a1 < a2:
            a1 += math.pi * 2.0
        da = -da
    a_start = a1
    a_end   = a2

    vertices =[]
    angle = a_start
    while (angle < a_end - da/4) == ccw:
        x = cx + math.cos(angle) * rx
        y = cy + math.sin(angle) * ry
        vertices.append( (x,y) )
        angle += da
    x = cx + math.cos(a_end) * rx
    y = cy + math.sin(a_end) * ry
    vertices.append( (x,y) )
    return np.array(vertices).reshape(len(vertices),2)

