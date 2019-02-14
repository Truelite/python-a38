from typing import Union, Sequence, Dict
from .fields import Field, ModelField
from .validation import ValidationError, ValidationErrors
from collections import OrderedDict, defaultdict


class ModelBase:
    def __init__(self):
        pass

    @classmethod
    def get_xmltag(cls) -> str:
        xmltag = getattr(cls, "__xmltag__", None)
        if xmltag is None:
            xmltag = cls.__name__

        xmlns = getattr(cls, "__xmlns__", None)
        if xmlns:
            return "{" + xmlns + "}" + xmltag
        else:
            return xmltag

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

    @classmethod
    def clean_value(cls, value):
        if value is None:
            return None
        if isinstance(value, cls):
            return value
        if not isinstance(value, ModelBase):
            raise ValidationError(None, "{} is not a Model instance".format(repr(value)))
        kw = {}
        for name, field in cls._meta.items():
            kw[name] = getattr(value, name, None)
        return cls(**kw)

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
            fields = (fields,)

        if len(fields) == 1:
            raise ValidationError(fields[0], msg)
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

    def __str__(self):
        vals = []
        for name, field in self._meta.items():
            vals.append(name + "=" + field.to_str(getattr(self, name)))
        return "{}({})".format(self.__class__.__name__, ", ".join(vals))

    def __repr__(self):
        vals = []
        for name, field in self._meta.items():
            vals.append(name + "=" + field.to_str(getattr(self, name)))
        return "{}({})".format(self.__class__.__name__, ", ".join(vals))

    def from_etree(self, el):
        if el.tag != self.get_xmltag():
            raise RuntimeError("element is {} instead of {}".format(el.tag, self.get_xmltag()))

        tag_map = {field.get_xmltag(): (name, field) for name, field in self._meta.items()}
        multivalues = None
        for child in el:
            try:
                name, field = tag_map[child.tag]
            except KeyError:
                raise RuntimeError("found unexpected element {} in {}".format(child.tag, el.tag))

            if field.multivalue:
                # Gather multivalue fields and process them later
                if multivalues is None:
                    multivalues = defaultdict(list)
                multivalues[name].append(child)
            else:
                setattr(self, name, field.from_etree(child))

        if multivalues:
            for name, elements in multivalues.items():
                field = self._meta[name]
                setattr(self, name, field.from_etree(elements))
