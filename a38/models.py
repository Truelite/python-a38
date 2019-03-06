from typing import Dict, Any, Optional, Tuple
from .fields import Field, ModelField
from .validation import Validation
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

    def update(self, *args, **kw):
        """
        Set multiple values in the model.

        Arguments are treated in the same way as in the constructor. Any field
        not mentioned is left untouched.
        """
        for name, value in zip(self._meta.keys(), args):
            setattr(self, name, value)

        for name, value in kw.items():
            setattr(self, name, value)

    def has_value(self):
        for name, field in self._meta.items():
            if field.has_value(getattr(self, name)):
                return True
        return False

    @classmethod
    def clean_value(cls, value: Any) -> Optional["Model"]:
        """
        Create a model from the given value.

        Always make a copy even if value is already of the right class, to
        prevent mutability issues.
        """
        if value is None:
            return None
        if not isinstance(value, ModelBase):
            raise TypeError("{} is not a Model instance".format(value.__class__.__name__))
        kw = {}
        for name, field in cls._meta.items():
            kw[name] = getattr(value, name, None)
        return cls(**kw)

    def validate_fields(self, validation: Validation):
        for name, field in self._meta.items():
            field.validate(validation, getattr(self, name))

    def validate_model(self, validation: Validation):
        pass

    def validate(self, validation: Validation):
        self.validate_fields(validation)
        self.validate_model(validation)

    def to_jsonable(self):
        res = {}
        for name, field in self._meta.items():
            value = field.to_jsonable(getattr(self, name))
            if value is not None:
                res[name] = value
        return res

    def to_python(self, **kw) -> str:
        args = []
        for name, field in self._meta.items():
            value = getattr(self, name)
            if not field.has_value(value):
                continue
            args.append(name + "=" + field.to_python(value, **kw))
        namespace = kw.get("namespace")
        if namespace is None:
            constructor = self.__class__.__module__ + "." + self.__class__.__qualname__
        elif namespace is False:
            constructor = self.__class__.__qualname__
        else:
            constructor = namespace + "." + self.__class__.__qualname__
        return "{}({})".format(constructor, ", ".join(args))

    def to_xml(self, builder):
        with builder.element(self.get_xmltag(), **self.get_xmlattrs()) as b:
            for name, field in self._meta.items():
                field.to_xml(b, getattr(self, name))

    def __setattr__(self, key: str, value: any):
        field = self._meta.get(key, None)
        if field is not None:
            value = field.clean_value(value)
        super().__setattr__(key, value)

    def _to_tuple(self) -> Tuple[Any]:
        return tuple(getattr(self, name) for name in self._meta.keys())

    def __eq__(self, other):
        other = self.clean_value(other)
        has_self = self.has_value()
        has_other = other is not None and other.has_value()
        if not has_self and not has_other:
            return True
        if has_self != has_other:
            return False
        return self._to_tuple() == other._to_tuple()

    def __ne__(self, other):
        other = self.clean_value(other)
        has_self = self.has_value()
        has_other = other is not None and other.has_value()
        if not has_self and not has_other:
            return False
        if has_self != has_other:
            return True
        return self._to_tuple() != other._to_tuple()

    def __lt__(self, other):
        other = self.clean_value(other)
        has_self = self.has_value()
        has_other = other is not None and other.has_value()
        if not has_self and not has_other:
            return False
        if has_self and not has_other:
            return False
        if not has_self and has_other:
            return True
        return self._to_tuple() < other._to_tuple()

    def __gt__(self, other):
        other = self.clean_value(other)
        has_self = self.has_value()
        has_other = other is not None and other.has_value()
        if not has_self and not has_other:
            return False
        if has_self and not has_other:
            return True
        if not has_self and has_other:
            return False
        return self._to_tuple() > other._to_tuple()

    def __le__(self, other):
        other = self.clean_value(other)
        has_self = self.has_value()
        has_other = other is not None and other.has_value()
        if not has_self and not has_other:
            return True
        if has_self and not has_other:
            return False
        if not has_self and has_other:
            return True
        return self._to_tuple() <= other._to_tuple()

    def __ge__(self, other):
        other = self.clean_value(other)
        has_self = self.has_value()
        has_other = other is not None and other.has_value()
        if not has_self and not has_other:
            return True
        if has_self and not has_other:
            return True
        if not has_self and has_other:
            return False
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

        # Group values by tag
        by_name = defaultdict(list)
        for child in el:
            try:
                name, field = tag_map[child.tag]
            except KeyError:
                raise RuntimeError("found unexpected element {} in {}".format(child.tag, el.tag))

            by_name[name].append(child)

        for name, elements in by_name.items():
            field = self._meta[name]
            if field.multivalue:
                setattr(self, name, field.from_etree(elements))
            elif len(elements) != 1:
                raise RuntimeError(
                        "found {} {} elements in {} instead of just 1".format(
                            len(elements), child.tag, el.tag))
            else:
                setattr(self, name, field.from_etree(elements[0]))

    def diff(self, diff, other):
        has_self = self.has_value()
        has_other = other.has_value()
        if not has_self and not has_other:
            return
        if has_self != has_other:
            diff.add(None, self, other)
            return
        for name, field in self._meta.items():
            first = getattr(self, name)
            second = getattr(other, name)
            field.diff(diff, first, second)
