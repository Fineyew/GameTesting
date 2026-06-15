import ast
import unittest
from pathlib import Path


MODULE_ROOT = Path(__file__).resolve().parents[1] / "app" / "modules"
ALLOWED_SHARED_MODULES = {"contracts", "registry"}


class ModuleBoundaryTests(unittest.TestCase):
    def test_gameplay_modules_do_not_import_each_other_internals(self) -> None:
        violations: list[str] = []

        for path in sorted(MODULE_ROOT.glob("*/**/*.py")):
            module_key = path.relative_to(MODULE_ROOT).parts[0]
            if module_key in ALLOWED_SHARED_MODULES:
                continue

            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                imported_module = _imported_module_name(node)
                if imported_module is None:
                    continue

                parts = imported_module.split(".")
                if parts[:3] != ["backend", "app", "modules"] or len(parts) < 4:
                    continue

                imported_key = parts[3]
                if imported_key != module_key and imported_key not in ALLOWED_SHARED_MODULES:
                    violations.append(
                        f"{path}: module '{module_key}' imports '{imported_module}'"
                    )

        self.assertEqual([], violations)


def _imported_module_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.ImportFrom):
        return node.module
    if isinstance(node, ast.Import) and node.names:
        return node.names[0].name
    return None


if __name__ == "__main__":
    unittest.main()
