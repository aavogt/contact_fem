import os
import re
import ast
import operator as _op
import FreeCAD
import Part
# import Uncross
# Uncross can take multiple passes, so add will have to accumulate

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
## but it only supports MmLlHhVvZz commands. Reminder:
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
    global _svg_handle, _xmin, _ymin, _xmax, _ymax
    if export is not None:
        if export.lower().endswith(".svg"):
            _svg_handle = open(export, "w")
        else:
            base, ext = os.path.splitext(export)
            _svg_handle = open(base + ".svg", "w")
        _svg_handle.write(" " * _MAXLEN_SVGHEAD)

    x = y = 0.0
    start = (x, y)

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
        if op not in "MmLlHhVvZz":
            raise ValueError(f"Unknown SVG path command in statement: {st!r}")

        raw = st[i + 1:].strip()

        if op in "Zz":
            _seg(sketch, x, y, *start)
            x, y = start
            continue

        nums = _parse_numbers(raw, vals)

        if op == 'M':
            if len(nums) < 2:
                raise ValueError(f"'M' requires at least 2 numbers: {st!r}")
            x, y = nums[0], nums[1]
            start = (x, y)
            # extra pairs behave like implicit absolute L
            if (len(nums) - 2) % 2 != 0:
                raise ValueError(f"'M' extra arguments must be pairs: {st!r}")
            for j in range(2, len(nums), 2):
                x2, y2 = nums[j], nums[j + 1]
                _seg(sketch, x, y, x2, y2)
                x, y = x2, y2

        elif op == 'm':
            if len(nums) < 2:
                raise ValueError(f"'m' requires at least 2 numbers: {st!r}")
            x += nums[0]
            y += nums[1]
            start = (x, y)
            # extra pairs behave like implicit relative l
            if (len(nums) - 2) % 2 != 0:
                raise ValueError(f"'m' extra arguments must be pairs: {st!r}")
            for j in range(2, len(nums), 2):
                x2, y2 = x + nums[j], y + nums[j + 1]
                _seg(sketch, x, y, x2, y2)
                x, y = x2, y2

        elif op == 'L':
            if len(nums) < 2 or len(nums) % 2 != 0:
                raise ValueError(f"'L' requires one or more coordinate pairs: {st!r}")
            for j in range(0, len(nums), 2):
                x2, y2 = nums[j], nums[j + 1]
                _seg(sketch, x, y, x2, y2)
                x, y = x2, y2

        elif op == 'l':
            if len(nums) < 2 or len(nums) % 2 != 0:
                raise ValueError(f"'l' requires one or more coordinate pairs: {st!r}")
            for j in range(0, len(nums), 2):
                x2, y2 = x + nums[j], y + nums[j + 1]
                _seg(sketch, x, y, x2, y2)
                x, y = x2, y2

        elif op == 'H':
            if len(nums) < 1:
                raise ValueError(f"'H' requires one or more numbers: {st!r}")
            for x2 in nums:
                _seg(sketch, x, y, x2, y)
                x = x2

        elif op == 'h':
            if len(nums) < 1:
                raise ValueError(f"'h' requires one or more numbers: {st!r}")
            for dx in nums:
                x2 = x + dx
                _seg(sketch, x, y, x2, y)
                x = x2

        elif op == 'V':
            if len(nums) < 1:
                raise ValueError(f"'V' requires one or more numbers: {st!r}")
            for y2 in nums:
                _seg(sketch, x, y, x, y2)
                y = y2

        elif op == 'v':
            if len(nums) < 1:
                raise ValueError(f"'v' requires one or more numbers: {st!r}")
            for dy in nums:
                y2 = y + dy
                _seg(sketch, x, y, x, y2)
                y = y2

    if export is not None:
        _svg_handle.write(svgtail)
        _svg_handle.seek(0)
        _svg_handle.write(svghead())
        _svg_handle.close()
        if not export.endswith(".svg"):
            base, ext = os.path.splitext(export)
            _ = os.system(f"convert {base}.svg {export}")


def _parse_numbers(raw, vals):
    # Parse a sequence of arithmetic expressions separated by commas and/or
    # expression boundaries introduced by sign-started terms.
    # Examples:
    #   "10,20"           -> ["10", "20"]
    #   "-W/2"            -> ["-W/2"]
    #   "N+B"             -> ["N+B"]
    #   "A, -B, C+D"      -> ["A", "-B", "C+D"]
    if not raw:
        return []

    s = raw.strip()
    tokens = []
    cur = []
    depth = 0
    i = 0
    n = len(s)

    def flush():
        tok = "".join(cur).strip()
        if tok:
            tokens.append(tok)
        cur.clear()

    while i < n:
        ch = s[i]

        if ch == '(':
            depth += 1
            cur.append(ch)
            i += 1
            continue
        if ch == ')':
            depth = max(0, depth - 1)
            cur.append(ch)
            i += 1
            continue

        # Comma always separates expressions at top level.
        if ch == ',' and depth == 0:
            flush()
            i += 1
            continue

        # At top level, whitespace may separate expressions.
        # Keep whitespace inside current token only when clearly internal.
        if ch.isspace() and depth == 0:
            j = i
            while j < n and s[j].isspace():
                j += 1

            # If next non-space starts a signed/new value and current token
            # already has content, split here.
            if j < n and s[j] in '+-' and cur:
                flush()
                i = j
                continue

            # Otherwise just skip top-level whitespace.
            i = j
            continue

        cur.append(ch)
        i += 1

    flush()

    out = []
    for tok in tokens:
        try:
            out.append(float(_safe_eval_expr(tok, vals)))
        except Exception as e:
            raise ValueError(
                f"Failed to parse numeric token {tok!r} from raw {raw!r}"
            ) from e
    return out

def _safe_eval_expr(expr, vars_map):
    # Safe arithmetic evaluator: + - * / // % ** and unary +/-
    allowed_bin = {
        ast.Add: _op.add,
        ast.Sub: _op.sub,
        ast.Mult: _op.mul,
        ast.Div: _op.truediv,
        ast.FloorDiv: _op.floordiv,
        ast.Mod: _op.mod,
        ast.Pow: _op.pow,
    }
    allowed_unary = {
        ast.UAdd: _op.pos,
        ast.USub: _op.neg,
    }

    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError(f"Non-numeric constant in expression: {expr!r}")
        if isinstance(node, ast.Name):
            if node.id in vars_map:
                v = vars_map[node.id]
                if isinstance(v, (int, float)):
                    return v
                return float(v)
            raise ValueError(f"Unknown variable {node.id!r} in expression: {expr!r}")
        if isinstance(node, ast.BinOp) and type(node.op) in allowed_bin:
            return allowed_bin[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in allowed_unary:
            return allowed_unary[type(node.op)](_eval(node.operand))
        raise ValueError(f"Unsupported expression: {expr!r}")

    try:
        tree = ast.parse(expr, mode='eval')
    except SyntaxError as e:
        raise ValueError(f"Invalid arithmetic expression: {expr!r}") from e
    return _eval(tree)


def _seg(sk, x1, y1, x2, y2):
    global _xmin, _xmax, _ymin, _ymax
    if _svg_handle is not None:
        _svg_handle.write(f"\nM {x1},{y1}\nL {x2},{y2}")
        if _xmin is None:
            _xmin = min(x1,x2)
            _xmax = max(x1,x2)
            _ymin = min(y1,y2)
            _ymax = max(y1,y2)
        else:
            _xmin = min(x1, x2, _xmin)
            _ymin = min(y1, y2, _ymin)
            _xmax= max(x1, x2, _xmax)
            _ymax = max(y1, y2, _ymax)
    sk.addGeometry(Part.LineSegment(
        FreeCAD.Vector(x1, y1, 0),
        FreeCAD.Vector(x2, y2, 0)
    ))

_svg_handle = None

_xmin = None
_xmax = None
_ymin = None
_ymax = None

# get the bounding box with one pass through the commands.
# leave space and seek back to the front to add the header with viewBox later.
# more than enough blank space to be replaced later
# other options would be to get the bounding box in a first pass
_MAXLEN_SVGHEAD = 200

def svghead():
    r = f"""<svg id="svg_css_ex1" viewBox="{_xmin} {_ymin} {_xmax-_xmin} {_ymax-_ymin}" xmlns="http://www.w3.org/2000/svg"> <path fill="none" stroke="red" d=" """
    assert(len(r) < _MAXLEN_SVGHEAD)
    return r

svgtail = """\nZ   " /> </svg>"""
