from unittest import TestCase
# import io
# from a38.builder import Builder
# from a38.fattura import IdFiscaleIVA, DatiAnagrafici
from a38 import fields
from a38 import validation

NS = "http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.2"


class TestField(TestCase):
    def test_empty(self):
        f = fields.Field()
        f.set_name("test")
        with self.assertRaises(validation.ValidationError):
            f.validate(None)
        self.assertIsNone(f.clean_value(None))
        self.assertEqual(f.get_xmltag(), "Test")

    def test_nullable(self):
        f = fields.Field(null=True)
        f.set_name("test")
        self.assertIsNone(f.validate(None))
        self.assertIsNone(f.clean_value(None))
        self.assertEqual(f.get_xmltag(), "Test")

    def test_value(self):
        f = fields.Field()
        f.set_name("test")
        self.assertEqual(f.validate("value"), "value")


class TestStringField(TestCase):
    def test_empty(self):
        f = fields.StringField()
        f.set_name("test")
        with self.assertRaises(validation.ValidationError):
            f.validate(None)
        self.assertIsNone(f.clean_value(None))
        self.assertEqual(f.get_xmltag(), "Test")

    def test_nullable(self):
        f = fields.StringField(null=True)
        f.set_name("test")
        self.assertIsNone(f.validate(None))
        self.assertIsNone(f.clean_value(None))
        self.assertEqual(f.get_xmltag(), "Test")

    def test_value(self):
        f = fields.StringField()
        f.set_name("test")
        self.assertEqual(f.validate("value"), "value")
        self.assertEqual(f.validate(12), "12")

    def test_length(self):
        f = fields.StringField(length=3)
        f.set_name("test")
        with self.assertRaises(validation.ValidationError):
            f.validate("va")
        with self.assertRaises(validation.ValidationError):
            f.validate("valu")
        with self.assertRaises(validation.ValidationError):
            f.validate(1.15)
        self.assertEqual(f.validate("val"), "val")
        self.assertEqual(f.validate(1.2), "1.2")

    def test_min_length(self):
        f = fields.StringField(min_length=3)
        f.set_name("test")
        with self.assertRaises(validation.ValidationError):
            f.validate("va")
        self.assertEqual(f.validate("valu"), "valu")
        self.assertEqual(f.validate("val"), "val")
        self.assertEqual(f.validate(1.2), "1.2")
        self.assertEqual(f.validate(1.15), "1.15")

    def test_max_length(self):
        f = fields.StringField(max_length=3)
        f.set_name("test")
        self.assertEqual(f.validate("v"), "v")
        self.assertEqual(f.validate("va"), "va")
        self.assertEqual(f.validate("val"), "val")
        with self.assertRaises(validation.ValidationError):
            f.validate("valu")

    def test_choices(self):
        f = fields.StringField(choices=("A", "B"))
        f.set_name("test")
        self.assertEqual(f.validate("A"), "A")
        self.assertEqual(f.validate("B"), "B")
        with self.assertRaises(validation.ValidationError):
            f.validate("C")
        with self.assertRaises(validation.ValidationError):
            f.validate("a")
        with self.assertRaises(validation.ValidationError):
            f.validate(None)

    def test_choices_nullable(self):
        f = fields.StringField(choices=("A", "B"), null=True)
        f.set_name("test")
        self.assertEqual(f.validate("A"), "A")
        self.assertEqual(f.validate("B"), "B")
        self.assertEqual(f.validate(None), None)
        with self.assertRaises(validation.ValidationError):
            f.validate("C")
        with self.assertRaises(validation.ValidationError):
            f.validate("a")
