from typing import Optional, Any, TypeVar, Generic, Sequence, List
from dateutil.parser import isoparse
import datetime
import decimal
import re
from . import validation
from . import builder
from .diff import Diff
from decimal import Decimal
import base64
import time
import pytz
import logging

log = logging.getLogger("a38.fields")


def to_xmltag(name: str, xmlns: Optional[str] = None):
    tag = "".join(x.title() for x in name.split("_"))
    if xmlns is None:
        return tag
    return "{" + xmlns + "}" + tag


T = TypeVar("T")


class Field(Generic[T]):
    """
    Description of a value that can be validated and serialized to XML.

    It does not contain the value itself.
    """
    # True for fields that can hold a sequence of values
    multivalue = False

    def __init__(self,
                 xmlns: Optional[str] = None,
                 xmltag: Optional[str] = None,
                 null: bool = False,
                 default: Optional[T] = None):
        self.name: Optional[str] = None
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

    def get_construct_default(self) -> Optional[T]:
        """
        Get the default value for when a field is constructed in the Model
        constructor, and no value for it has been passed
        """
        return None

    def has_value(self, value: Optional[T]) -> bool:
        """
        Return True if this value represents a field that has been set
        """
        return value is not None

    def validate(self, validation: "validation.Validation", value: Any) -> Optional[T]:
        """
        Raise ValidationError(s) if the given value is not valid for this field.

        Return the cleaned value.
        """
        try:
            value = self.clean_value(value)
        except (TypeError, ValueError) as e:
            validation.add_error(self, str(e))

        if not self.null and not self.has_value(value):
            validation.add_error(self, "missing value")

        return value

    def clean_value(self, value: Any) -> Optional[T]:
        """
        Return a cleaned version of the given value
        """
        if value is None:
            return self.default
        return value

    def get_xmltag(self) -> str:
        """
        Return the XML tag to use for this field
        """
        if self.xmltag is not None:
            if self.xmlns is not None:
                return "{" + self.xmlns + "}" + self.xmltag
            else:
                return self.xmltag
        if self.name is None:
            raise RuntimeError("field with uninitialized name")
        else:
            return to_xmltag(self.name, self.xmlns)

    def to_xml(self, builder: "builder.Builder", value: Optional[T]):
        """
        Add this field to an XML tree
        """
        value = self.clean_value(value)
        if not self.has_value(value):
            return
        builder.add(self.get_xmltag(), self.to_str(value))

    def to_jsonable(self, value: Optional[T]) -> Any:
        """
        Return a json-able value for this field
        """
        return self.clean_value(value)

    def to_str(self, value: Optional[T]) -> str:
        """
        Return this value as a string that can be parsed by clean_value
        """
        return str(value)

    def to_repr(self, value: Optional[T]) -> str:
        """
        Return this value formatted for debugging
        """
        return repr(value)

    def to_python(self, value: Optional[T], **kw) -> str:
        """
        Return this value as a python expression
        """
        return repr(self.clean_value(value))

    def from_etree(self, el):
        """
        Return a value from an ElementTree Element
        """
        return self.clean_value(el.text)

    def diff(self, res: Diff, first: Optional[T], second: Optional[T]):
        """
        Report to res if there are differences between values first and second
        """
        first = self.clean_value(first)
        second = self.clean_value(second)
        has_first = self.has_value(first)
        has_second = self.has_value(second)
        if not has_first and not has_second:
            return
        elif has_first and not has_second:
            res.add_only_first(self, first)
        elif not has_first and has_second:
            res.add_only_second(self, second)
        elif first != second:
            res.add_different(self, first, second)


class NotImplementedField(Field[None]):
    """
    Field acting as a placeholder for a part of the specification that is not
    yet implemented.
    """
    def __init__(self, warn: bool = False, **kw):
        super().__init__(**kw)
        self.warn = warn

    def clean_value(self, value: Any) -> None:
        if self.warn:
            log.warning("%s: value received: %r", self.name, value)
        return None


class ChoicesField(Field[T]):
    def __init__(self, choices: Sequence[T] = None, **kw):
        super().__init__(**kw)
        self.choices: Optional[List[Optional[T]]]
        if choices is not None:
            self.choices = [self.clean_value(c) for c in choices]
        else:
            self.choices = None

    def validate(self, validation: "validation.Validation", value: Optional[T]):
        value = super().validate(validation, value)
        if value is not None and self.choices is not None and value not in self.choices:
            validation.add_error(self, "{} is not a valid choice for this field".format(self.to_repr(value)))
        return value


class ListField(Field[List[T]]):
    multivalue = True

    def __init__(self, field: Field[T], min_num=0, **kw):
        super().__init__(**kw)
        self.field = field
        self.min_num = min_num

    def set_name(self, name: str):
        super().set_name(name)
        self.field.xmltag = self.get_xmltag()

    def get_construct_default(self):
        res = []
        for i in range(self.min_num):
            res.append(None)
        return res

    def clean_value(self, value):
        value = super().clean_value(value)
        if value is None:
            return value
        res = [self.field.clean_value(val) for val in value]
        while len(res) > self.min_num and not self.field.has_value(res[-1]):
            res.pop()
        return res

    def has_value(self, value):
        if value is None:
            return False
        for el in value:
            if self.field.has_value(el):
                return True
        return False

    def validate(self, validation, value):
        value = super().validate(validation, value)
        if not self.has_value(value):
            return value
        if len(value) < self.min_num:
            validation.add_error(
                    self,
                    "list must have at least {} elements, but has only {}".format(
                        self.min_num, len(value)))
        for idx, val in enumerate(value):
            with validation.subfield(self.name + "." + str(idx)) as sub:
                self.field.validate(sub, val)
        return value

    def to_xml(self, builder, value):
        value = self.clean_value(value)
        if not self.has_value(value):
            return
        for val in value:
            self.field.to_xml(builder, val)

    def to_jsonable(self, value):
        value = self.clean_value(value)
        if not self.has_value(value):
            return None
        return [self.field.to_jsonable(val) for val in value]

    def to_python(self, value, **kw) -> str:
        value = self.clean_value(value)
        if not self.has_value(value):
            return repr(None)
        return "[" + ", ".join(self.field.to_python(v, **kw) for v in value) + "]"

    def diff(self, res: Diff, first, second):
        first = self.clean_value(first)
        second = self.clean_value(second)
        has_first = self.has_value(first)
        has_second = self.has_value(second)
        if not has_first and not has_second:
            return
        elif has_first and not has_second:
            res.add_only_first(self, first)
        elif not has_first and has_second:
            res.add_only_second(self, second)
        else:
            for idx, (el_first, el_second) in enumerate(zip(first, second)):
                with res.subfield(self.name + "." + str(idx)) as subres:
                    if el_first != el_second:
                        self.field.diff(subres, el_first, el_second)
            if len(first) != len(second):
                res.add_different_length(self, first, second)

    def from_etree(self, elements):
        values = []
        for el in elements:
            values.append(self.field.from_etree(el))
        return values


class IntegerField(ChoicesField[int]):
    def __init__(self, max_length=None, **kw):
        super().__init__(**kw)
        self.max_length = max_length

    def clean_value(self, value):
        value = super().clean_value(value)
        if value is None:
            return value
        return int(value)

    def validate(self, validation, value):
        value = super().validate(validation, value)
        if not self.has_value(value):
            return value
        if self.max_length is not None and len(str(value)) > self.max_length:
            validation.add_error(self, "'{}' should be no more than {} digits long".format(value, self.max_length))
        return value


class DecimalField(ChoicesField[Decimal]):
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
        except decimal.InvalidOperation:
            raise TypeError("{} cannot be converted to Decimal".format(repr(value)))

    def to_str(self, value):
        if not self.has_value(value):
            return "None"
        return str(self.clean_value(value).quantize(self.quantize_sample))

    def to_jsonable(self, value):
        """
        Return a json-able value for this field
        """
        value = self.clean_value(value)
        if not self.has_value(value):
            return None
        return self.to_str(value)

    def validate(self, validation, value):
        value = super().validate(validation, value)
        if not self.has_value(value):
            return value
        if self.max_length is not None:
            xml_value = self.to_str(value)
            if len(xml_value) > self.max_length:
                validation.add_error(
                        self,
                        "'{}' should be no more than {} digits long".format(xml_value, self.max_length))
        return value


class StringField(ChoicesField[str]):
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

    def validate(self, validation, value):
        value = super().validate(validation, value)
        if not self.has_value(value):
            return value
        if self.min_length is not None and len(value) < self.min_length:
            validation.add_error(self, "'{}' should be at least {} characters long".format(value, self.min_length))
        if self.max_length is not None and len(value) > self.max_length:
            validation.add_error(self, "'{}' should be no more than {} characters long".format(value, self.max_length))
        return value


class Base64BinaryField(Field[bytes]):
    def clean_value(self, value):
        value = super().clean_value(value)
        if value is None:
            return value
        if isinstance(value, bytes):
            return value
        if isinstance(value, str):
            return base64.b64decode(value)
        raise TypeError("'{}' is not an instance of str, or bytes".format(repr(value)))

    def to_jsonable(self, value: Optional[T]) -> Any:
        """
        Return a json-able value for this field
        """
        return self.to_str(self.clean_value(value))

    def to_str(self, value: Optional[T]) -> str:
        """
        Return this value as a string that can be parsed by clean_value
        """
        if value is None:
            return None
        return base64.b64encode(value).decode("utf8")


class DateField(ChoicesField[datetime.date]):
    re_clean_date = re.compile(r"^\s*(\d{4}-\d{1,2}-\d{1,2})")

    def clean_value(self, value):
        value = super().clean_value(value)
        if value is None:
            return value
        if isinstance(value, str):
            mo = self.re_clean_date.match(value)
            if not mo:
                raise ValueError("Date '{}' does not begin with YYYY-mm-dd".format(value))
            return datetime.datetime.strptime(mo.group(1), "%Y-%m-%d").date()
        elif isinstance(value, datetime.datetime):
            return value.date()
        elif isinstance(value, datetime.date):
            return value
        else:
            raise TypeError("'{}' is not an instance of str, datetime.date or datetime.datetime".format(repr(value)))

    def to_jsonable(self, value):
        """
        Return a json-able value for this field
        """
        value = self.clean_value(value)
        if not self.has_value(value):
            return None
        return self.to_str(value)

    def to_str(self, value):
        if value is None:
            return "None"
        return value.strftime("%Y-%m-%d")


class DateTimeField(ChoicesField[datetime.datetime]):
    tz_rome = pytz.timezone("Europe/Rome")

    def clean_value(self, value):
        value = super().clean_value(value)
        if value is None:
            return value
        if isinstance(value, str):
            res = isoparse(value)
            if res.tzinfo is None:
                res = self.tz_rome.localize(res)
            return res
        elif isinstance(value, datetime.datetime):
            if value.tzinfo is None:
                return self.tz_rome.localize(value)
            return value
        elif isinstance(value, datetime.date):
            return datetime.datetime.combine(value, datetime.time(0, 0, 0, tzinfo=self.tz_rome))
        else:
            raise TypeError("'{}' is not an instance of str, datetime.date or datetime.datetime".format(repr(value)))

    def to_jsonable(self, value):
        """
        Return a json-able value for this field
        """
        value = self.clean_value(value)
        if not self.has_value(value):
            return None
        return self.to_str(value)

    def to_python(self, value, **kw):
        value = self.clean_value(value)
        if not self.has_value(value):
            return repr(value)
        return repr(value.isoformat())

    def to_str(self, value):
        if not self.has_value(value):
            return "None"
        return value.isoformat()

    def to_repr(self, value):
        if not self.has_value(value):
            return "None"
        return value.isoformat()


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
                raise OverflowError(
                        "Generated more than {} fatture per second, overflowing local counter".format(64 ** 3))

        value = (ts << 16) + self.sequence
        return self._encode_b56(value, 10)


class ModelField(Field):
    """
    Field containing the structure from a Model
    """
    def __init__(self, model, **kw):
        super().__init__(**kw)
        self.model = model

    def __str__(self):
        return "ModelField({})".format(self.model.__name__)

    __repr__ = __str__

    def get_construct_default(self):
        return self.model()

    def clean_value(self, value):
        value = super().clean_value(value)
        if value is None:
            return value
        return self.model.clean_value(value)

    def has_value(self, value):
        if value is None:
            return False
        return value.has_value()

    def get_xmltag(self):
        if self.xmltag is not None:
            if self.xmlns is not None:
                return "{" + self.xmlns + "}" + self.xmltag
            else:
                return self.xmltag
        return self.model.get_xmltag()

    def validate(self, validation, value):
        value = super().validate(validation, value)
        if not self.has_value(value):
            return value

        with validation.subfield(self.name) as sub:
            value.validate_fields(sub)

        value.validate_model(validation)
        return value

    def to_xml(self, builder, value):
        value = self.clean_value(value)
        if not self.has_value(value):
            return
        value.to_xml(builder)

    def to_jsonable(self, value):
        value = self.clean_value(value)
        if not self.has_value(value):
            return None
        return value.to_jsonable()

    def to_python(self, value, **kw) -> str:
        value = self.clean_value(value)
        if not self.has_value(value):
            return repr(None)
        return value.to_python(**kw)

    def diff(self, res: Diff, first, second):
        first = self.clean_value(first)
        second = self.clean_value(second)
        has_first = self.has_value(first)
        has_second = self.has_value(second)
        if not has_first and not has_second:
            return
        elif has_first and not has_second:
            res.add_only_first(self, first)
        elif not has_first and has_second:
            res.add_only_second(self, first)
        else:
            with res.subfield(self.name) as subres:
                first.diff(subres, second)

    def from_etree(self, el):
        res = self.model()
        res.from_etree(el)
        return res


class ModelListField(Field):
    """
    Field containing a list of model instances
    """
    multivalue = True

    def __init__(self, model, min_num=0, **kw):
        super().__init__(**kw)
        self.model = model
        self.min_num = min_num

    def get_construct_default(self):
        res = []
        for i in range(self.min_num):
            res.append(self.model())
        return res

    def clean_value(self, value):
        value = super().clean_value(value)
        if value is None:
            return value
        res = [self.model.clean_value(val) for val in value]
        while len(res) > self.min_num and (res[-1] is None or not res[-1].has_value()):
            res.pop()
        return res

    def has_value(self, value):
        if value is None:
            return False

        for el in value:
            if el.has_value():
                return True

        return False

    def get_xmltag(self):
        if self.xmltag is not None:
            return self.xmltag
        return self.model.get_xmltag()

    def validate(self, validation, value):
        value = super().validate(validation, value)
        if not self.has_value(value):
            return value

        if len(value) < self.min_num:
            validation.add_error(
                    self,
                    "list must have at least {} elements, but has only {}".format(self.min_num, len(value)))

        for idx, val in enumerate(value):
            with validation.subfield(self.name + "." + str(idx)) as sub:
                val.validate_fields(sub)

            val.validate_model(validation)
        return value

    def to_xml(self, builder, value):
        value = self.clean_value(value)
        if not self.has_value(value):
            return
        for val in value:
            val.to_xml(builder)

    def to_jsonable(self, value):
        value = self.clean_value(value)
        if not self.has_value(value):
            return None
        return [val.to_jsonable() for val in value]

    def to_python(self, value, **kw) -> str:
        value = self.clean_value(value)
        if not self.has_value(value):
            return repr(None)
        return "[" + ", ".join(v.to_python(**kw) for v in value) + "]"

    def diff(self, res: Diff, first, second):
        first = self.clean_value(first)
        second = self.clean_value(second)
        has_first = self.has_value(first)
        has_second = self.has_value(second)
        if not has_first and not has_second:
            return
        if has_first and not has_second:
            res.add_only_first(self, first)
        elif not has_first and has_second:
            res.add_only_second(self, second)
        else:
            for idx, (el_first, el_second) in enumerate(zip(first, second)):
                with res.subfield(self.name + "." + str(idx)) as subres:
                    el_first.diff(subres, el_second)

            if len(first) != len(second):
                res.add_different_length(self, first, second)

    def from_etree(self, elements):
        values = []
        for el in elements:
            value = self.model()
            value.from_etree(el)
            values.append(value)
        return values
