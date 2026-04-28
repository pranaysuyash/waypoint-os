#!/usr/bin/env python3
"""Temporary analysis script for code quality review."""
import ast, os, re, sys

BASE = "/Users/pranay/Projects/travel_agency_agent"

def calc_complexity(node):
    score = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.IfExp)):
            score += 1
        elif isinstance(child, (ast.For, ast.While, ast.AsyncFor)):
            score += 1
        elif isinstance(child, ast.BoolOp):
            score += len(child.values) - 1
        elif isinstance(child, ast.ExceptHandler):
            score += 1
        elif isinstance(child, (ast.With, ast.AsyncWith)):
            score += 1
    return score

def max_nesting(node):
    depths = []
    def walk(n, depth):
        for child in ast.iter_child_nodes(n):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try, ast.AsyncFor, ast.AsyncWith)):
                depths.append(depth + 1)
                walk(child, depth + 1)
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                pass
            else:
                walk(child, depth)
    walk(node, 0)
    return max(depths) if depths else 0

def get_files():
    result = []
    for d in ['src', 'spine_api']:
        for root, dirs_w, files in os.walk(os.path.join(BASE, d)):
            if '__pycache__' in root or '.venv' in root:
                continue
            for f in files:
                if f.endswith('.py'):
                    result.append(os.path.join(root, f))
    return sorted(result)

# 1. Cyclomatic complexity
print("=== CYCLOMATIC COMPLEXITY > 10 ===")
for path in get_files():
    try:
        with open(path) as fh:
            tree = ast.parse(fh.read())
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                c = calc_complexity(node)
                if c > 10:
                    rel = os.path.relpath(path, BASE)
                    print(f"  {rel}:{node.lineno} | complexity={c} | {node.name}")
    except:
        pass

# 2. Long parameter lists
print("\n=== LONG PARAMETER LISTS (>5) ===")
for path in get_files():
    try:
        with open(path) as fh:
            tree = ast.parse(fh.read())
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                params = []
                args = node.args
                params.extend([a.arg for a in args.args])
                params.extend([a.arg for a in args.kwonlyargs])
                if args.vararg: params.append('*' + args.vararg.arg)
                if args.kwarg: params.append('**' + args.kwarg.arg)
                if len(params) > 5:
                    rel = os.path.relpath(path, BASE)
                    print(f"  {rel}:{node.lineno} | params={len(params)} | {node.name}({', '.join(params)})")
    except:
        pass

# 3. God classes
print("\n=== GOD CLASSES (>15 methods) ===")
for path in get_files():
    try:
        with open(path) as fh:
            tree = ast.parse(fh.read())
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                if len(methods) > 15:
                    rel = os.path.relpath(path, BASE)
                    print(f"  {rel}:{node.lineno} | {node.name} has {len(methods)} methods: {methods}")
    except:
        pass

# 4. Deep nesting
print("\n=== DEEP NESTING (>4 levels) ===")
for path in get_files():
    try:
        with open(path) as fh:
            tree = ast.parse(fh.read())
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                depth = max_nesting(node)
                if depth > 4:
                    rel = os.path.relpath(path, BASE)
                    print(f"  {rel}:{node.lineno} | nesting={depth} | {node.name}")
    except:
        pass

# 5. Magic numbers (hardcoded numeric literals in function bodies)
print("\n=== MAGIC NUMBERS ===")
skip = {0, 1, 2, -1, 10, 100, 60, 24, 365, 200, 201, 204, 301, 400, 404, 500, 401, 403}
for path in get_files():
    try:
        with open(path) as fh:
            tree = ast.parse(fh.read())
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for child in ast.walk(node):
                    if isinstance(child, ast.Constant) and isinstance(child.value, (int, float)):
                        val = child.value
                        if val not in skip and abs(val) > 2:
                            rel = os.path.relpath(path, BASE)
                            # Filter out common patterns
                            print(f"  {rel}:{child.lineno} | value={val}")
    except:
        pass

# 6. Empty except handlers
print("\n=== EMPTY/GENERIC EXCEPTION HANDLERS ===")
for path in get_files():
    try:
        with open(path) as fh:
            source = fh.read()
            tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                body_text = ast.get_source_segment(source, node)
                rel = os.path.relpath(path, BASE)
                if node.type is None:
                    print(f"  {rel}:{node.lineno} | bare except (no type)")
                elif isinstance(node.type, ast.Name) and node.type.id == 'Exception':
                    # Check if body is just pass or single logging
                    if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                        print(f"  {rel}:{node.lineno} | except Exception: pass (silently swallowed)")
                    elif len(node.body) <= 2:
                        # Check for just pass or log
                        for stmt in node.body:
                            if isinstance(stmt, ast.Pass):
                                print(f"  {rel}:{node.lineno} | except Exception: pass (silently swallowed)")
    except:
        pass

# 7. Naming convention issues (camelCase function names)
print("\n=== NAMING CONVENTION ISSUES ===")
for path in get_files():
    try:
        with open(path) as fh:
            tree = ast.parse(fh.read())
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = node.name
                if name.startswith('_'):
                    name = name.lstrip('_')
                # Check for camelCase (has uppercase letter not at start, not __init__ etc.)
                if re.search(r'[a-z][A-Z]', node.name) and not node.name.startswith('__'):
                    rel = os.path.relpath(path, BASE)
                    print(f"  {rel}:{node.lineno} | camelCase function: {node.name} -> should be snake_case")
    except:
        pass

# 8. print() usage instead of logging
print("\n=== print() USAGE (should use logging) ===")
for path in get_files():
    try:
        with open(path) as fh:
            lines = fh.readlines()
        rel = os.path.relpath(path, BASE)
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if 'print(' in stripped and not stripped.startswith('#'):
                print(f"  {rel}:{i} | {stripped[:100]}")
    except:
        pass