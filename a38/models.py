from typing import Union, Sequence, Dict
from .fields import Field, ModelField
from .validation import ValidationError, ValidationErrors
from collections import OrderedDict


class ModelBase:
    def __init__(self):
        pass

    @classmethod
    def get_xmltag(cls) -> str:
        xmltag = getattr(cls, "xmltag", None)
        if xmltag is not None:
            return xmltag

        xmlns = getattr(cls, "xmlns", None)
        if xmlns:
            return "{" + xmlns + "}" + cls.__name__
        else:
            return cls.__name__

    def get_xmlattrs(self) -> Dict[str, str]:
        return {}


class ModelMetaclass(type):
    @classmethod
    def __prepare__(self, name, bases):
        # See https://stackoverflow.com/questions/4459531/how-to-read-class-attributes-in-the-same-order-as-declared
        return OrderedDict()

    def __new__(cls, name, bases, dct):
        res = super().__new__(cls, name, bases, dct)

        _meta = OrderedDict()

        # Add fields from subclasses
        for b in bases:
            if not issubclass(b, ModelBase):
                continue
            b_meta = getattr(b, "_meta", None)
            if b_meta is None:
                continue
            _meta.update(b_meta)

        for name, val in list(dct.items()):
            if isinstance(val, Field):
                dct.pop(name)
                _meta[name] = val
                val.set_name(name)
            elif isinstance(val, type) and issubclass(val, ModelBase):
                dct.pop(name)
                val = ModelField(val)
                _meta[name] = val
                val.set_name(name)
        res._meta = _meta

        return res


class Model(ModelBase, metaclass=ModelMetaclass):
    """
    Declarative description of a data structure that can be validated and
    serialized to XML.
    """
    def __init__(self, *args, **kw):
        super().__init__()
        for name, value in zip(self._meta.keys(), args):
            kw[name] = value

        for name, field in self._meta.items():
            value = kw.pop(name, None)
            if value is None:
                value = field.get_construct_default()
            else:
                value = field.clean_value(value)
            setattr(self, name, value)

    def validate_fields(self):
        errors = []
        for name, field in self._meta.items():
            try:
                field.validate(getattr(self, name))
            except ValidationError as e:
                errors.append(e)
        if errors:
            raise ValidationErrors(errors)

    def validate_model(self):
        pass

    def validate(self):
        self.validate_fields()
        self.validate_model()

    def validation_error(self, fields: Union[str, Sequence[str]], msg: str):
        if isinstance(fields, str):
            raise ValidationError(fields, msg)
        else:
            raise ValidationErrors(tuple(
                ValidationError(f, msg) for f in fields))

    def to_dict(self):
        return {name: field.to_dict(getattr(self, name)) for name, field in self._meta.items()}

    def to_xml(self, builder):
        with builder.element(self.get_xmltag(), **self.get_xmlattrs()) as b:
            for name, field in self._meta.items():
                field.to_xml(b, getattr(self, name))

    def __setattr__(self, key, value):
        field = self._meta.get(key, None)
        if field is not None:
            value = field.clean_value(value)
        super().__setattr__(key, value)

    def _to_tuple(self):
        return tuple(getattr(self, name) for name in self._meta.keys())

    def __eq__(self, other):
        return self._to_tuple() == other._to_tuple()

    def __ne__(self, other):
        return self._to_tuple() != other._to_tuple()

    def __lt__(self, other):
        return self._to_tuple() < other._to_tuple()

    def __gt__(self, other):
        return self._to_tuple() > other._to_tuple()

    def __le__(self, other):
        return self._to_tuple() <= other._to_tuple()

    def __ge__(self, other):
        return self._to_tuple() >= other._to_tuple()
