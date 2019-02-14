from unittest import TestCase
from a38 import fields
from a38 import models


class Sample(models.Model):
    name = fields.StringField()
    value = fields.IntegerField()


class TestModel(TestCase):
    def test_assignment(self):
        o = Sample()
        # Values are cleaned on assignment
        o.name = 12
        o.value = "42"
        self.assertEqual(o.name, "12")
        self.assertEqual(o.value, 42)
