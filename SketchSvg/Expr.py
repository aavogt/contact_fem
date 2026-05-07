import ast
import operator as _op
def parse_numbers(raw, vals):
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

        # Ignore top-level whitespace so expressions are not split by spaces.
        if ch.isspace() and depth == 0:
            i += 1
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
