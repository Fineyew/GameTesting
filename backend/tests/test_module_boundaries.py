import ast
import unittest
from pathlib import Path

from backend.app.modules.registry import MODULES


MODULE_ROOT = Path(__file__).resolve().parents[1] / "app" / "modules"
ALLOWED_SHARED_MODULES = {"contracts", "registry"}
FORBIDDEN_GAMEPLAY_IMPORT_PREFIXES = (
    "backend.app.db",
    "backend.app.db.models",
    "backend.app.db.session",
)


class ModuleBoundaryTests(unittest.TestCase):
    def test_gameplay_modules_do_not_import_each_other_internals(self) -> None:
        violations: list[str] = []

        for path in sorted(MODULE_ROOT.glob("*/**/*.py")):
            module_key = path.relative_to(MODULE_ROOT).parts[0]
            if module_key in ALLOWED_SHARED_MODULES:
                continue

            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                for imported_module in _imported_module_names(node):
                    parts = imported_module.split(".")
                    if parts[:3] != ["backend", "app", "modules"] or len(parts) < 4:
                        continue

                    imported_key = parts[3]
                    if imported_key != module_key and imported_key not in ALLOWED_SHARED_MODULES:
                        violations.append(
                            f"{path}: module '{module_key}' imports '{imported_module}'"
                        )

        self.assertEqual([], violations)

    def test_gameplay_modules_do_not_import_global_database_infrastructure(self) -> None:
        violations: list[str] = []

        for path in sorted(MODULE_ROOT.glob("*/**/*.py")):
            module_key = path.relative_to(MODULE_ROOT).parts[0]
            if module_key in ALLOWED_SHARED_MODULES:
                continue

            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                for imported_module in _imported_module_names(node):
                    if imported_module.startswith(FORBIDDEN_GAMEPLAY_IMPORT_PREFIXES):
                        violations.append(
                            f"{path}: module '{module_key}' imports '{imported_module}'"
                        )

        self.assertEqual([], violations)

    def test_registry_dependencies_reference_known_boundaries(self) -> None:
        known_boundaries = {module.key for module in MODULES} | {"events", "loot"}
        violations = [
            f"{module.key}: unknown dependency '{dependency}'"
            for module in MODULES
            for dependency in module.allowed_dependencies
            if dependency not in known_boundaries
        ]

        self.assertEqual([], violations)


def _imported_module_names(node: ast.AST) -> list[str]:
    if isinstance(node, ast.ImportFrom):
        return [node.module] if node.module else []
    if isinstance(node, ast.Import) and node.names:
        return [alias.name for alias in node.names]
    return []


if __name__ == "__main__":
    unittest.main()
