from unittest import TestCase
from a38 import fields
from a38 import models
from a38 import validation


class Sample(models.Model):
    name = fields.StringField()
    value = fields.IntegerField()


class Sample1(models.Model):
    name = fields.StringField()
    type = fields.StringField(choices=("A", "B"))


class TestModel(TestCase):
    def test_assignment(self):
        o = Sample()
        # Values are cleaned on assignment
        o.name = 12
        o.value = "42"
        self.assertEqual(o.name, "12")
        self.assertEqual(o.value, 42)

    def test_clean_value(self):
        val = Sample.clean_value(Sample1("foo", "A"))
        self.assertIsInstance(val, Sample)
        self.assertEqual(val.name, "foo")
        self.assertIsNone(val.value)

        self.assertIsNone(Sample.clean_value(None))
        with self.assertRaises(validation.ValidationError):
            Sample.clean_value("foo")

    def test_compare(self):
        self.assertEqual(Sample("test", 7), Sample("test", 7))
        self.assertNotEqual(Sample("test", 7), Sample("test", 6))
        self.assertLess(Sample("test", 6), Sample("test", 7))
        self.assertLessEqual(Sample("test", 6), Sample("test", 7))
        self.assertLessEqual(Sample("test", 7), Sample("test", 7))
        self.assertGreater(Sample("test", 7), Sample("test", 6))
        self.assertGreaterEqual(Sample("test", 7), Sample("test", 6))
        self.assertGreaterEqual(Sample("test", 7), Sample("test", 7))
