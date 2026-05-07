import os
import re

import Sketcher

from .Expr import *
from . import Stroke

## usage:
##
## > import SketchSvg
## > sketch = doc.addObject('Sketcher::SketchObject', 'Sketch')
## > SketchSvg.add(dict(X = 10, y = 20), sketch, "m 1,2; h X; v Y; z", export="output.pdf")
##
## expressions with +-/* are also supported
##
## this makes a right triangle with vertices at 1,2; 1+10,2; 1+10,2+20
## saved to output.pdf and output.svg
##
## https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Attribute/d
## but it only supports MmLlHhVvZzAa commands. Reminder:
## - lowercase is relative
## - uppercase is absolute
## - m moves without drawing
##
## (embedded)postscript is also similar
##
## previous "embedded domain specific language (eDSL)" versions:
## https://gist.github.com/aavogt/9ed063aea689fb3a144df1113e0f41fc waterfall-cad/haskell 2d with offset
## https://gist.github.com/aavogt/8fb7162e572d72049748e1e42b12bbd2 Ribbon3.py cadquery 3d version
## https://gist.github.com/aavogt/69de763ea7e9d525b1abfc84ceb27096 LLine.py build123d version
def add(vals, sketch, path_str, export=None):
    if export is not None:
        if export.lower().endswith(".svg"):
            Stroke.svg_handle = open(export, "w")
        else:
            base, ext = os.path.splitext(export)
            Stroke.svg_handle = open(base + ".svg", "w")
        Stroke.svg_handle.write(" " * _MAXLEN_SVGHEAD)

    x = y = 0.0
    start = (x, y)
    last_geom = None
    last_end = None
    path_start_geom = None
    path_start_end = None

    def _track_segment(geom):
        nonlocal last_geom, last_end, path_start_geom, path_start_end
        if geom is None:
            return
        if last_geom is not None and last_end is not None:
            sketch.addConstraint(
                Sketcher.Constraint("Coincident", last_geom, last_end, geom, 1)
            )
        if path_start_geom is None:
            path_start_geom = geom
            path_start_end = 1
        last_geom = geom
        last_end = 2

    def _track_close(geom):
        nonlocal last_geom, last_end, path_start_geom, path_start_end
        if geom is None:
            return
        if last_geom is not None and last_end is not None:
            sketch.addConstraint(
                Sketcher.Constraint("Coincident", last_geom, last_end, geom, 1)
            )
        if path_start_geom is not None and path_start_end is not None:
            sketch.addConstraint(
                Sketcher.Constraint("Coincident", path_start_geom, path_start_end, geom, 2)
            )
        last_geom = geom
        last_end = 2

    # Split only on ';' or newline. Command is first non-space char in each stmt.
    statements = [st.strip() for st in re.split(r'[;\n]+', path_str) if st.strip()]

    for st in statements:
        i = 0
        n = len(st)
        while i < n and st[i].isspace():
            i += 1
        if i >= n:
            continue

        op = st[i]
        if op == "#":
            continue
        if op not in "MmLlHhVvZzAa":
            raise ValueError(f"Unknown SVG path command in statement: {st!r}")

        raw = st[i + 1:].strip()

        if op in "Zz":
            geom = Stroke.seg(sketch, x, y, *start)
            _track_close(geom)
            x, y = start
            continue

        nums = parse_numbers(raw, vals)

        if op == 'M':
            if len(nums) < 2:
                raise ValueError(f"'M' requires at least 2 numbers: {st!r}")
            x, y = nums[0], nums[1]
            start = (x, y)
            last_geom = None
            last_end = None
            path_start_geom = None
            path_start_end = None
            # extra pairs behave like implicit absolute L
            if (len(nums) - 2) % 2 != 0:
                raise ValueError(f"'M' extra arguments must be pairs: {st!r}")
            for j in range(2, len(nums), 2):
                x2, y2 = nums[j], nums[j + 1]
                geom = Stroke.seg(sketch, x, y, x2, y2)
                _track_segment(geom)
                x, y = x2, y2

        elif op == 'm':
            if len(nums) < 2:
                raise ValueError(f"'m' requires at least 2 numbers: {st!r}")
            x += nums[0]
            y += nums[1]
            start = (x, y)
            last_geom = None
            last_end = None
            path_start_geom = None
            path_start_end = None
            # extra pairs behave like implicit relative l
            if (len(nums) - 2) % 2 != 0:
                raise ValueError(f"'m' extra arguments must be pairs: {st!r}")
            for j in range(2, len(nums), 2):
                x2, y2 = x + nums[j], y + nums[j + 1]
                geom = Stroke.seg(sketch, x, y, x2, y2)
                _track_segment(geom)
                x, y = x2, y2

        elif op == 'L':
            if len(nums) < 2 or len(nums) % 2 != 0:
                raise ValueError(f"'L' requires one or more coordinate pairs: {st!r}")
            for j in range(0, len(nums), 2):
                x2, y2 = nums[j], nums[j + 1]
                geom = Stroke.seg(sketch, x, y, x2, y2)
                _track_segment(geom)
                x, y = x2, y2

        elif op == 'l':
            if len(nums) < 2 or len(nums) % 2 != 0:
                raise ValueError(f"'l' requires one or more coordinate pairs: {st!r}")
            for j in range(0, len(nums), 2):
                x2, y2 = x + nums[j], y + nums[j + 1]
                geom = Stroke.seg(sketch, x, y, x2, y2)
                _track_segment(geom)
                x, y = x2, y2

        elif op == 'H':
            if len(nums) < 1:
                raise ValueError(f"'H' requires one or more numbers: {st!r}")
            for x2 in nums:
                geom = Stroke.seg(sketch, x, y, x2, y)
                _track_segment(geom)
                x = x2

        elif op == 'h':
            if len(nums) < 1:
                raise ValueError(f"'h' requires one or more numbers: {st!r}")
            for dx in nums:
                x2 = x + dx
                geom = Stroke.seg(sketch, x, y, x2, y)
                _track_segment(geom)
                x = x2

        elif op == 'v':
            if len(nums) < 1:
                raise ValueError(f"'v' requires one or more numbers: {st!r}")
            for dy in nums:
                y2 = y + dy
                geom = Stroke.seg(sketch, x, y, x, y2)
                _track_segment(geom)
                y = y2

        elif op == 'V':
            if len(nums) < 1:
                raise ValueError(f"'V' requires one or more numbers: {st!r}")
            for y2 in nums:
                geom = Stroke.seg(sketch, x, y, x, y2)
                _track_segment(geom)
                y = y2

        elif op == 'a':
            if len(nums) < 7 or len(nums) % 7 != 0:
                raise ValueError(f"'a' requires one or more 7-number arc sets: {st!r}")
            for j in range(0, len(nums), 7):
                rx, ry, angle, large_arc, sweep, dx, dy = nums[j:j + 7]
                x2, y2 = x + dx, y + dy
                geom = Stroke.arc(sketch, x, y, x2, y2, rx, ry, angle, int(large_arc), int(sweep))
                _track_segment(geom)
                x, y = x2, y2

        elif op == 'A':
            if len(nums) < 7 or len(nums) % 7 != 0:
                raise ValueError(f"'A' requires one or more 7-number arc sets: {st!r}")
            for j in range(0, len(nums), 7):
                rx, ry, angle, large_arc, sweep, x2, y2 = nums[j:j + 7]
                geom = Stroke.arc(sketch, x, y, x2, y2, rx, ry, angle, int(large_arc), int(sweep))
                _track_segment(geom)
                x, y = x2, y2

    if export is not None:
        Stroke.svg_handle.write(svgtail)
        Stroke.svg_handle.seek(0)
        Stroke.svg_handle.write(svghead())
        Stroke.svg_handle.close()
        if not export.endswith(".svg"):
            base, ext = os.path.splitext(export)
            _ = os.system(f"convert {base}.svg {export}")

# get the bounding box with one pass through the commands.
# leave space and seek back to the front to add the header with viewBox later.
# more than enough blank space to be replaced later
# other options would be to get the bounding box in a first pass
_MAXLEN_SVGHEAD = 200

def svghead():
    r = f"""<svg id="svg_css_ex1" viewBox="{Stroke.xmin} {Stroke.ymin} {Stroke.xmax-Stroke.xmin} {Stroke.ymax-Stroke.ymin}" xmlns="http://www.w3.org/2000/svg"> <path fill="none" stroke="red" d=" """
    assert(len(r) < _MAXLEN_SVGHEAD)
    return r

svgtail = """\nZ   " /> </svg>"""
