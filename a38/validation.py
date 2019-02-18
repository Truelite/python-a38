from typing import Optional, List, Sequence, Union
from .traversal import Annotation, Traversal
from . import fields


class ValidationError(Annotation):
    def __init__(self, prefix: Optional[str], field: "fields.Field", msg: str):
        self.prefix = prefix
        self.field = field
        self.msg = msg

    def __str__(self):
        return "{}: {}".format(self.qualified_field, self.msg)


Fields = Union["fields.Field", Sequence["fields.Field"]]


class Validation(Traversal):
    def __init__(self,
                 prefix: Optional[str] = None,
                 warnings: Optional[List[ValidationError]] = None,
                 errors: Optional[List[ValidationError]] = None):
        super().__init__(prefix)
        self.warnings: List[ValidationError]
        self.errors: List[ValidationError]
        if warnings is None:
            self.warnings = []
        else:
            self.warnings = warnings
        if errors is None:
            self.errors = []
        else:
            self.errors = errors

    def with_prefix(self, prefix: str):
        return Validation(prefix, self.warnings, self.errors)

    def add_warning(self, field: Fields, msg: str):
        if isinstance(field, fields.Field):
            self.warnings.append(ValidationError(self.prefix, field, msg))
        else:
            for f in field:
                self.warnings.append(ValidationError(self.prefix, f, msg))

    def add_error(self, field: Fields, msg: str):
        if isinstance(field, fields.Field):
            self.errors.append(ValidationError(self.prefix, field, msg))
        else:
            for f in field:
                self.errors.append(ValidationError(self.prefix, f, msg))
