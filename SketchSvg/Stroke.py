import math
import FreeCAD
import Part

svg_handle = None

xmin = None
xmax = None
ymin = None
ymax = None

def seg(sk, x1, y1, x2, y2):
    if svg_handle is not None:
        svg_handle.write(f"\nM {x1},{y1}\nL {x2},{y2}")
        _update_bounds(x1, y1)
        _update_bounds(x2, y2)
    if (x1 != x2 or y1 != y2):
        return sk.addGeometry(
            Part.LineSegment(
                FreeCAD.Vector(x1, y1, 0),
                FreeCAD.Vector(x2, y2, 0)
            ),
            False
        )
    return None

def arc(sk, x1, y1, x2, y2, rx, ry, angle_deg, large_arc, sweep):
    geom_sweep = 0 if sweep else 1
    if rx == 0 or ry == 0:
        return seg(sk, x1, y1, x2, y2)

    rx = abs(rx)
    ry = abs(ry)
    phi = math.radians(angle_deg % 360.0)
    cos_phi = math.cos(phi)
    sin_phi = math.sin(phi)

    dx2 = (x1 - x2) / 2.0
    dy2 = (y1 - y2) / 2.0
    x1p = cos_phi * dx2 + sin_phi * dy2
    y1p = -sin_phi * dx2 + cos_phi * dy2

    rx2 = rx * rx
    ry2 = ry * ry
    x1p2 = x1p * x1p
    y1p2 = y1p * y1p

    lam = x1p2 / rx2 + y1p2 / ry2
    if lam > 1.0:
        scale = math.sqrt(lam)
        rx *= scale
        ry *= scale
        rx2 = rx * rx
        ry2 = ry * ry

    sign = -1.0 if bool(large_arc) == bool(geom_sweep) else 1.0
    num = rx2 * ry2 - rx2 * y1p2 - ry2 * x1p2
    denom = rx2 * y1p2 + ry2 * x1p2
    if denom == 0:
        return seg(sk, x1, y1, x2, y2)

    coef = sign * math.sqrt(max(0.0, num / denom))
    cxp = coef * (rx * y1p / ry)
    cyp = coef * (-ry * x1p / rx)

    cx = cos_phi * cxp - sin_phi * cyp + (x1 + x2) / 2.0
    cy = sin_phi * cxp + cos_phi * cyp + (y1 + y2) / 2.0

    ux = (x1p - cxp) / rx
    uy = (y1p - cyp) / ry
    vx = (-x1p - cxp) / rx
    vy = (-y1p - cyp) / ry

    start_angle = _vector_angle(1.0, 0.0, ux, uy)
    delta_angle = _vector_angle(ux, uy, vx, vy)

    if not geom_sweep and delta_angle > 0:
        delta_angle -= 2.0 * math.pi
    elif geom_sweep and delta_angle < 0:
        delta_angle += 2.0 * math.pi

    end_angle = start_angle + delta_angle

    if svg_handle is not None:
        svg_handle.write(
            f"\nM {x1},{y1}\nA {rx},{ry} {angle_deg} {int(bool(large_arc))},{int(bool(sweep))} {x2},{y2}"
        )
        _update_bounds(x1, y1)
        _update_bounds(x2, y2)
        _update_bounds(cx + rx, cy)
        _update_bounds(cx - rx, cy)
        _update_bounds(cx, cy + ry)
        _update_bounds(cx, cy - ry)

    ellipse = Part.Ellipse(FreeCAD.Vector(cx, cy, 0), rx, ry)
    if angle_deg:
        ellipse.rotate( FreeCAD.Base.Placement(FreeCAD.Vector(cx, cy, 0),  FreeCAD.Vector(0, 0, 1), angle_deg))
    arc = Part.ArcOfEllipse(ellipse, start_angle, end_angle)
    return sk.addGeometry(arc, False)


def _vector_angle(ux, uy, vx, vy):
    dot = ux * vx + uy * vy
    det = ux * vy - uy * vx
    return math.atan2(det, dot)

def _update_bounds(x, y):
    global xmin, xmax, ymin, ymax
    if xmin is None:
        xmin = xmax = x
        ymin = ymax = y
    else:
        xmin = min(xmin, x)
        xmax = max(xmax, x)
        ymin = min(ymin, y)
        ymax = max(ymax, y)

