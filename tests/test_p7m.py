from unittest import TestCase
from a38.crypto import P7M


class TestAnagrafica(TestCase):
    def test_load(self):
        p7m = P7M("tests/data/test.txt.p7m")
        data = p7m.get_payload()
        self.assertEqual(
                data,
                "This is only a test payload.\n"
                "\n"
                "Questo è solo un payload di test.\n".encode("utf8"))
