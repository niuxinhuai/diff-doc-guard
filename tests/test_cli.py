import json
import unittest

from diff_doc_guard.__main__ import changed_files, evaluate, result_data


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


if __name__ == "__main__":
    unittest.main()
