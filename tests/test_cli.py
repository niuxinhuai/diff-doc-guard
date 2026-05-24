import json
import unittest

import os
import tempfile

from diff_doc_guard.__main__ import changed_files, evaluate, init_rules_file, load_rules, result_data


class DiffDocGuardTest(unittest.TestCase):
    def test_changed_files_from_diff(self):
        diff = "diff --git a/src/api/order.ts b/src/api/order.ts\n+++ b/src/api/order.ts\n"
        self.assertEqual(changed_files(diff), ["src/api/order.ts"])

    def test_rule_hit_json_shape(self):
        rules = {"rules": [{"name": "API", "patterns": ["src/api/**"], "docs": ["docs/API.md"], "reason": "API changed"}]}
        hits = evaluate(["src/api/order.ts"], rules)
        data = result_data(["src/api/order.ts"], hits)
        self.assertTrue(data["needs_docs"])
        self.assertEqual(json.loads(json.dumps(data))["docs_to_check"][0]["docs"], ["docs/API.md"])

    def test_load_rules_auto_discovers_repo_config(self):
        with tempfile.TemporaryDirectory() as repo:
            config = os.path.join(repo, ".docguard.json")
            with open(config, "w", encoding="utf-8") as handle:
                handle.write('{"rules":[{"name":"Docs","patterns":["docs/**"],"docs":["README.md"],"reason":"docs changed"}]}')
            rules = load_rules(None, repo)
        self.assertEqual(rules["rules"][0]["name"], "Docs")

    def test_init_rules_file_writes_default_config(self):
        with tempfile.TemporaryDirectory() as repo:
            path = init_rules_file(repo)
            self.assertTrue(os.path.exists(path))
            rules = load_rules(None, repo)
        self.assertTrue(rules["rules"])


if __name__ == "__main__":
    unittest.main()
