# tests.py
import unittest
from config_to_yaml import ConfigParser

class TestConfigParser(unittest.TestCase):
    def setUp(self):
        self.parser = ConfigParser()

    def test_remove_comments(self):
        text = """% Comment\n{
            name = value,
            /* Multi-line\n               comment */
            key = 42
        }"""
        expected = """{
            name = value,
            key = 42
        }"""
        self.assertEqual(self.parser.remove_comments(text).strip(), expected.strip())

    def test_constant_definition(self):
        self.parser.parse("def MAX = 10;")
        self.assertIn("MAX", self.parser.constants)
        self.assertEqual(self.parser.constants["MAX"], 10)

    def test_resolve_constant(self):
        self.parser.constants = {"VALUE": 42}
        result = self.parser.resolve_constant("^VALUE")
        self.assertEqual(result, 42)

    def test_parse_dict(self):
        text = "{ key = 42, name = \"example\" }"
        expected = {"key": 42, "name": "example"}
        self.assertEqual(self.parser.parse_dict(text), expected)

    def test_parse_list(self):
        text = "[1, 2, 3, 42]"
        expected = [1, 2, 3, 42]
        self.assertEqual(self.parser.parse_list(text), expected)

    def test_integration(self):
        text = """% Example
        def MAX = 10;
        {
            name = "example",
            values = [1, 2, ^MAX]
        }"""
        expected = {
            "name": "example",
            "values": [1, 2, 10]
        }
        result = self.parser.parse(text)
        self.assertEqual(result, expected)

    def test_parse_dict_with_nested_structures(self):
        text = "{ name = \"example\", values = [1, 2, 3], max = ^MAX_COUNT }"
        self.parser.constants = {"MAX_COUNT": 100}
        expected = {
            "name": "example",
            "values": [1, 2, 3],
            "max": 100
        }
        result = self.parser.parse_dict(text)
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
