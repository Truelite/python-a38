from typing import Optional
from .validation import ValidationError, ValidationErrors
import datetime
import decimal
from decimal import Decimal
from contextlib import contextmanager
import time


def to_xmltag(name: str, xmlns: Optional[str] = None):
    tag = "".join(x.title() for x in name.split("_"))
    if xmlns is None:
        return tag
    return "{" + xmlns + "}" + tag


class Field:
    """
    Description of a value that can be validated and serialized to XML.

    It does not contain the value itself.
    """
    # True for fields that can hold a sequence of values
    multivalue = False

    def __init__(self, xmlns=None, xmltag=None, null=False, default=None):
        self.name = None
        self.xmlns = xmlns
        self.xmltag = xmltag
        self.null = null
        self.default = default

    def set_name(self, name: str):
        """
        Set the field name.

        Used by the Model metaclass to set the field name from the metaclass
        attribute that defines it
        """
        self.name = name

    def get_construct_default(self):
        """
        Get the default value for when a field is constructed in the Model
        constructor, and no value for it has been passed
        """
        return None

    def has_value(self, value):
        """
        Return True if this value represents a field that has been set
        """
        return value is not None

    def validate(self, value):
        """
        Raise ValidationError(s) if the given value is not valid for this field.

        Return the cleaned value.
        """
        value = self.clean_value(value)
        if not self.null and value is None:
            self.validation_error("value is None")
        return value

    def validation_error(self, msg):
        """
        Raise ValidationError for this field
        """
        raise ValidationError(self.name, msg)

    @contextmanager
    def annotate_validation_errors(self, *extra_names):
        try:
            yield
        except (ValidationError, ValidationErrors) as e:
            if extra_names:
                e.add_container_name(".".join(str(x) for x in tuple(self.name, *extra_names)))
            else:
                e.add_container_name(self.name)
            raise

    def clean_value(self, value):
        """
        Return a cleaned version of the given value
        """
        if value is None:
            return self.default
        return value

    def get_xmltag(self):
        """
        Return the XML tag to use for this field
        """
        if self.xmltag is not None:
            return self.xmltag
        return to_xmltag(self.name, self.xmlns)

    def to_xml(self, builder, value):
        """
        Add this field to an XML tree
        """
        value = self.clean_value(value)
        if value is None:
            return
        builder.add(self.get_xmltag(), self.to_str(value))

    def to_dict(self, value):
        """
        Return a json-able value for this field
        """
        return self.clean_value(value)

    def to_str(self, value):
        return str(value)

    def from_etree(self, el):
        return self.clean_value(el.text)


class ChoicesMixin:
    def __init__(self, choices=None, **kw):
        super().__init__(**kw)
        if choices is not None:
            choices = [self.clean_value(c) for c in choices]
        self.choices = choices

    def validate(self, value):
        value = super().validate(value)
        if value is not None and self.choices is not None and value not in self.choices:
            self.validation_error("'{}' is not a valid choice for this field".format(value))
        return value


class IntegerField(ChoicesMixin, Field):
    def __init__(self, max_length=None, **kw):
        super().__init__(**kw)
        self.max_length = max_length

    def clean_value(self, value):
        value = super().clean_value(value)
        if value is None:
            return value
        try:
            return int(value)
        except ValueError as e:
            self.validation_error("'{}' cannot be converted to int: {}".format(value, str(e)))

    def validate(self, value):
        value = super().validate(value)
        if value is None:
            return value
        if not isinstance(value, int):
            self.validation_error("'{}' should be an int", repr(value))
        if self.max_length is not None and len(str(value)) > self.max_length:
            self.validation_error("'{}' should be no more than {} digits long".format(value, self.max_length))
        return value


class DecimalField(ChoicesMixin, Field):
    def __init__(self, max_length=None, decimals=2, **kw):
        super().__init__(**kw)
        self.max_length = max_length
        self.decimals = decimals
        self.quantize_sample = Decimal(10) ** -decimals

    def clean_value(self, value):
        value = super().clean_value(value)
        if value is None:
            return value
        try:
            return Decimal(value)
        except decimal.InvalidOperation as e:
            self.validation_error("'{}' cannot be converted to Decimal: {}".format(value, str(e)))

    def to_str(self, value):
        if value is None:
            return "None"
        return str(self.clean_value(value).quantize(self.quantize_sample))

    def to_dict(self, value):
        """
        Return a json-able value for this field
        """
        return self.to_str(self.clean_value(value))

    def validate(self, value):
        value = super().validate(value)
        if value is None:
            return value
        if not isinstance(value, Decimal):
            self.validation_error("'{}' should be a Decimal", repr(value))
        if self.max_length is not None:
            xml_value = self.to_str(value)
            if len(xml_value) > self.max_length:
                self.validation_error("'{}' should be no more than {} digits long".format(xml_value, self.max_length))
        return value


class StringField(ChoicesMixin, Field):
    def __init__(self, length=None, min_length=None, max_length=None, **kw):
        super().__init__(**kw)
        if length is not None:
            if min_length is not None or max_length is not None:
                raise ValueError("length cannot be used with min_length or max_length")
            self.min_length = self.max_length = length
        else:
            self.min_length = min_length
            self.max_length = max_length

    def clean_value(self, value):
        value = super().clean_value(value)
        if value is None:
            return value
        return str(value)

    def validate(self, value):
        value = super().validate(value)
        if value is None:
            return value
        if self.min_length is not None and len(value) < self.min_length:
            self.validation_error("'{}' should be at least {} characters long".format(value, self.min_length))
        if self.max_length is not None and len(value) > self.max_length:
            self.validation_error("'{}' should be no more than {} characters long".format(value, self.max_length))
        return value


class DateField(ChoicesMixin, Field):
    def clean_value(self, value):
        value = super().clean_value(value)
        if value is None:
            return value
        if isinstance(value, str):
            try:
                return datetime.datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError as e:
                self.validation_error("'{}' is not a valid date: {}".format(value, str(e)))
        elif isinstance(value, datetime.datetime):
            return value.date()
        elif isinstance(value, datetime.date):
            return value
        else:
            self.validation_error("'{}' is not an instance of str, datetime.date or datetime.datetime".format(repr(value)))

    def validate(self, value):
        value = super().validate(value)
        if value is None:
            return value
        if not isinstance(value, datetime.date):
            self.validation_error("value must be an instance of datetime.date")
        return value

    def to_dict(self, value):
        """
        Return a json-able value for this field
        """
        return self.to_str(self.clean_value(value))

    def to_str(self, value):
        if value is None:
            return "None"
        return value.strftime("%Y-%m-%d")


class ProgressivoInvioField(StringField):
    CHARS = "+-./0123456789=@ABCDEFGHIJKLMNOPQRSTUVWXYZ_"
    TS_RANGE = 2 ** (54 - 16)
    SEQUENCE_RANGE = 2 ** 16
    last_ts = None
    sequence = 0

    def __init__(self, **kw):
        kw["max_length"] = 10
        super().__init__(**kw)

    def _encode_b56(self, value, places):
        res = []
        while value > 0:
            res.append(self.CHARS[value % 43])
            value //= 43
        return "".join(res[::-1])

    def get_construct_default(self):
        ts = int(time.time())
        if self.last_ts is None or self.last_ts != ts:
            self.sequence = 0
            self.last_ts = ts
        else:
            self.sequence += 1
            if self.sequence > (64 ** 3):
                raise OverflowError("Generated more than {} fatture per second, overflowing local counter".format(64 ** 3))

        value = (ts << 16) + self.sequence
        return self._encode_b56(value, 10)


class ModelField(Field):
    """
    Field containing the structure from a Model
    """
    def __init__(self, model, **kw):
        super().__init__(**kw)
        self.model = model

    def get_construct_default(self):
        return self.model()

    def clean_value(self, value):
        value = super().clean_value(value)
        if value is None:
            return value
        with self.annotate_validation_errors():
            return self.model.clean_value(value)

    def has_value(self, value):
        if value is None:
            return False

        for name, field in self.model._meta.items():
            if field.has_value(getattr(value, name)):
                return True
        return False

    def get_xmltag(self):
        if self.xmltag is not None:
            return self.xmltag
        return self.model.get_xmltag()

    def validate(self, value):
        value = super().validate(value)
        if value is None:
            return value

        if not isinstance(value, self.model):
            self.validation_error("{} is not an instance of {}".format(repr(value), self.model.__name__))

        with self.annotate_validation_errors():
            value.validate_fields()

        value.validate_model()
        return value

    def to_xml(self, builder, value):
        value = self.clean_value(value)
        if not self.has_value(value):
            return
        value.to_xml(builder)

    def to_dict(self, value):
        value = self.clean_value(value)
        if value is None:
            return None
        return value.to_dict()

    def from_etree(self, el):
        res = self.model()
        res.from_etree(el)
        return res


class ModelListField(Field):
    """
    Field containing a list of model instances
    """
    multivalue = True

    def __init__(self, model, **kw):
        super().__init__(**kw)
        self.model = model

    def get_construct_default(self):
        return []

    def clean_value(self, value):
        value = super().clean_value(value)
        if value is None:
            return value
        with self.annotate_validation_errors():
            return [self.model.clean_value(val) for val in value]

    def has_value(self, value):
        if value is None:
            return False

        for el in value:
            for name, field in self.model._meta.items():
                if field.has_value(getattr(el, name)):
                    return True
        return False

    def get_xmltag(self):
        if self.xmltag is not None:
            return self.xmltag
        return self.model.get_xmltag()

    def validate(self, value):
        value = super().validate(value)
        if value is None:
            return None

        if not isinstance(value, list):
            self.validation_error("{} is not a list".format(repr(value)))
        for idx, val in enumerate(value):
            if not isinstance(val, self.model):
                self.validation_error("list element {} '{}' is not an instance of {}".format(idx, repr(val), self.model.__name__))

            with self.annotate_validation_errors(idx):
                val.validate_fields()

            val.validate_model()
        return value

    def to_xml(self, builder, value):
        value = self.clean_value(value)
        if not self.has_value(value):
            return
        for val in value:
            val.to_xml(builder)

    def to_dict(self, value):
        value = self.clean_value(value)
        if value is None:
            return None
        return [val.to_dict() for val in value]

    def from_etree(self, elements):
        values = []
        for el in elements:
            value = self.model()
            value.from_etree(el)
            values.append(value)
        return values
