from typing import Optional, Any, List
from .traversal import Annotation, Traversal
from . import fields


class Difference(Annotation):
    def __init__(self, prefix: Optional[str], field: "fields.Field", first: Any, second: Any):
        super().__init__(prefix, field)
        self.first = first
        self.second = second

    def __str__(self):
        return "{}: first: {}, second: {}".format(
                self.qualified_field,
                self.field.to_str(self.first),
                self.field.to_str(self.second))


class MissingOne(Difference):
    def __str__(self):
        if self.first is None:
            return "{}: first is not set".format(self.qualified_field)
        else:
            return "{}: second is not set".format(self.qualified_field)


class ExtraItems(Difference):
    def __str__(self):
        if len(self.first) > len(self.second):
            diff = len(self.first) - len(self.second)
            longer = "first"
        else:
            diff = len(self.second) - len(self.first)
            longer = "second"

        if diff == 1:
            return "{}: {} has 1 extra element".format(self.qualified_field, longer)
        else:
            return "{}: {} has {} extra elements".format(self.qualified_field, longer, diff)


class Diff(Traversal):
    def __init__(self, prefix: Optional[str] = None, differences: Optional[List[Difference]] = None):
        super().__init__(prefix)
        self.differences: List[Difference]
        if differences is None:
            self.differences = []
        else:
            self.differences = differences

    def with_prefix(self, prefix: str):
        return Diff(prefix, self.differences)

    def add_different(self, field: "fields.Field", first: Any, second: Any):
        self.differences.append(Difference(self.prefix, field, first, second))

    def add_only_first(self, field: "fields.Field", first: Any):
        self.differences.append(MissingOne(self.prefix, field, first, None))

    def add_only_second(self, field: "fields.Field", second: Any):
        self.differences.append(MissingOne(self.prefix, field, None, second))

    def add_different_length(self, field: "fields.Field", first: Any, second: Any):
        self.differences.append(ExtraItems(self.prefix, field, first, second))
