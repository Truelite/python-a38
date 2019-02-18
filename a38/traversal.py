from typing import Optional
from contextlib import contextmanager
from . import fields


class Annotation:
    def __init__(self, prefix: Optional[str], field: "fields.Field"):
        self.prefix = prefix
        self.field = field

    @property
    def qualified_field(self) -> str:
        if self.prefix is None:
            return self.field.name
        elif self.field.name is None:
            return self.prefix
        else:
            return self.prefix + "." + self.field.name


class Traversal:
    def __init__(self, prefix: Optional[str] = None):
        self.prefix = prefix

    def with_prefix(self, prefix: str) -> "Traversal":
        raise NotImplementedError("Traversal subclasses must implement with_prefix")

    @contextmanager
    def subfield(self, name: str):
        if self.prefix is None:
            prefix = name
        else:
            prefix = self.prefix + "." + name
        yield self.with_prefix(prefix)
