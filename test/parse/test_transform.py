import json
import unittest


class TestParseTransform(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        with open(
            "data/test_data/receipt_parsed_sample.json", "r", encoding="utf-8"
        ) as file:
            self.receipt_parsed_sample = json.loads(file.read())

    def test_loaded_sample(self):
        self.assertEqual(len(self.receipt_parsed_sample), 2)

        trans = self.receipt_parsed_sample[0]
        self.assertEqual(
            sorted(trans.keys()),
            ["date", "date_raw", "id", "idx", "receipt_data"],
            f"bad keys for transaction {trans['id']}",
        )

    @unittest.skip("not implemented")
    def test_everything_else(self):
        # TODO finish
        pass
