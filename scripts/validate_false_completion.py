#!/usr/bin/env python3
"""Scan implementation and tests for false-completion patterns."""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = ROOT / "validation" / "false_completion_rules.json"


def _relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _is_docstring(node: ast.stmt) -> bool:
    return isinstance(node, ast.Expr) and isinstance(getattr(node, "value", None), ast.Constant) and isinstance(node.value.value, str)


def _body_without_docstring(node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> list[ast.stmt]:
    return [statement for statement in node.body if not _is_docstring(statement)]


def _route_handler(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute) and isinstance(decorator.func.value, ast.Name):
            if decorator.func.value.id in {"router", "admin_router", "app"}:
                return True
    return False


def _empty_literal(value: ast.expr | None) -> bool:
    if value is None:
        return True
    if isinstance(value, ast.Constant) and value.value in (None, ""):
        return True
    return isinstance(value, (ast.Dict, ast.List, ast.Set)) and len(value.elts if hasattr(value, "elts") else value.keys) == 0


def _constant_success_dict(value: ast.expr | None) -> bool:
    if not isinstance(value, ast.Dict):
        return False
    pairs = {
        key.value: item.value
        for key, item in zip(value.keys, value.values)
        if isinstance(key, ast.Constant) and isinstance(key.value, str)
        and isinstance(item, ast.Constant)
    }
    return pairs.get("status") in {"ok", "success", "sent", "accepted", "completed"}


def _violation(rule: str, path: Path, line: int, detail: str) -> dict[str, str | int]:
    return {"rule": rule, "file": _relative(path), "line": line, "detail": detail}


def scan_false_completion(rules_path: Path = RULES_PATH) -> dict:
    rules = json.loads(rules_path.read_text(encoding="utf-8"))
    if rules.get("ruleset_id") != "opportunity-radar-false-completion":
        raise ValueError("false-completion ruleset ID is invalid")
    files: list[Path] = []
    for root_name in rules.get("scan_roots", []):
        root = ROOT / root_name
        if not root.is_dir():
            raise ValueError(f"false-completion scan root does not exist: {root_name}")
        files.extend(path for path in root.rglob("*") if path.is_file() and path.suffix in {".py", ".ts"})
    files.sort()
    violations: list[dict[str, str | int]] = []
    allowlisted: list[dict[str, str | int]] = []
    not_implemented_allowlist = rules.get("not_implemented_allowlist", {})
    empty_class_allowlist = rules.get("empty_class_allowlist", {})
    forbidden_markers = [str(marker) for marker in rules.get("forbidden_markers", [])]
    forbidden_test_patterns = [str(pattern) for pattern in rules.get("forbidden_test_patterns", [])]

    for path in files:
        relative = _relative(path)
        source = path.read_text(encoding="utf-8")
        for line_number, line in enumerate(source.splitlines(), start=1):
            for marker in forbidden_markers:
                if marker in line:
                    violations.append(_violation("forbidden-marker", path, line_number, marker))
            if relative.startswith("backend/tests/"):
                for pattern in forbidden_test_patterns:
                    if pattern in line:
                        violations.append(_violation("skipped-or-trivial-test", path, line_number, pattern))
        if path.suffix != ".py":
            continue
        try:
            tree = ast.parse(source, filename=relative)
        except SyntaxError as exc:
            violations.append(_violation("python-parse", path, exc.lineno or 1, str(exc)))
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                body = _body_without_docstring(node)
                if len(body) == 1 and isinstance(body[0], ast.Pass):
                    allow_key = f"{relative}:{node.name}" if isinstance(node, ast.ClassDef) else None
                    if allow_key in empty_class_allowlist:
                        allowlisted.append(_violation("empty-class-allowlist", path, node.lineno, str(empty_class_allowlist[allow_key])))
                    else:
                        violations.append(_violation("empty-body", path, node.lineno, f"{type(node).__name__} {node.name}"))
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and _route_handler(node) and len(body) == 1 and isinstance(body[0], ast.Return) and _empty_literal(body[0].value):
                    violations.append(_violation("empty-api-result", path, node.lineno, f"route handler {node.name} returns an empty literal"))
            if isinstance(node, ast.Raise) and (
                (isinstance(node.exc, ast.Name) and node.exc.id == "NotImplementedError")
                or (isinstance(node.exc, ast.Call) and isinstance(node.exc.func, ast.Name) and node.exc.func.id == "NotImplementedError")
            ):
                if relative in not_implemented_allowlist:
                    allowlisted.append(_violation("not-implemented-allowlist", path, node.lineno, str(not_implemented_allowlist[relative])))
                else:
                    violations.append(_violation("unapproved-not-implemented", path, node.lineno, "NotImplementedError is not allowlisted"))
            if isinstance(node, ast.ExceptHandler) and rules.get("forbid_pass_only_exception_handlers") and _relative(path).startswith("backend/app/"):
                body = [statement for statement in node.body if not _is_docstring(statement)]
                if len(body) == 1 and isinstance(body[0], ast.Pass):
                    violations.append(_violation("swallowed-exception", path, node.lineno, "exception handler contains only pass"))
            if (
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and rules.get("forbid_product_api_constant_success")
                and _relative(path).startswith("backend/app/api/")
                and _route_handler(node)
                and len(_body_without_docstring(node)) == 1
                and isinstance(_body_without_docstring(node)[0], ast.Return)
                and _constant_success_dict(_body_without_docstring(node)[0].value)
            ):
                violations.append(_violation("fake-success-api-result", path, node.lineno, f"route handler {node.name} returns a constant success result"))

    return {
        "ruleset_id": rules["ruleset_id"],
        "ruleset_version": rules.get("ruleset_version"),
        "status": "PASS" if not violations else "FAIL",
        "scanned_files": len(files),
        "violation_count": len(violations),
        "allowlisted_count": len(allowlisted),
        "violations": violations,
        "allowlisted": allowlisted,
    }


def main() -> int:
    try:
        result = scan_false_completion()
        report_path = ROOT / "validation" / "false_completion_scan.json"
        report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FALSE_COMPLETION_SCAN_FAIL: {exc}", file=sys.stderr)
        return 1
    if result["violations"]:
        print(f"FALSE_COMPLETION_SCAN_FAIL: {result['violation_count']} violations")
        for violation in result["violations"]:
            print(f"- {violation['file']}:{violation['line']} {violation['rule']}: {violation['detail']}")
        return 1
    print(f"FALSE_COMPLETION_SCAN_PASS: {result['scanned_files']} files, {result['allowlisted_count']} explicit contract exceptions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
