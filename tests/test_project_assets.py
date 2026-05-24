import os
import unittest


ROOT = os.path.dirname(os.path.dirname(__file__))


class ProjectAssetsTest(unittest.TestCase):
    def assert_exists(self, path):
        self.assertTrue(os.path.exists(os.path.join(ROOT, path)), path)

    def test_release_assets_exist(self):
        for path in [
            "CHANGELOG.md",
            "SECURITY.md",
            "CODE_OF_CONDUCT.md",
            ".github/ISSUE_TEMPLATE/bug_report.yml",
            ".github/ISSUE_TEMPLATE/feature_request.yml",
            ".github/workflows/release.yml",
        ]:
            self.assert_exists(path)

    def test_pyproject_has_publish_metadata(self):
        with open(os.path.join(ROOT, "pyproject.toml"), "r", encoding="utf-8") as handle:
            text = handle.read()
        self.assertIn("[project.urls]", text)
        self.assertIn("build-backend", text)

    def test_release_workflow_is_safe_before_pypi_setup(self):
        with open(os.path.join(ROOT, ".github/workflows/release.yml"), "r", encoding="utf-8") as handle:
            text = handle.read()
        self.assertIn("softprops/action-gh-release", text)
        self.assertIn("vars.PUBLISH_TO_PYPI == 'true'", text)


if __name__ == "__main__":
    unittest.main()
