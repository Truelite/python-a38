from typing import Sequence


class ValidationError(Exception):
    def __init__(self, field_name: str, msg: str):
        self.field_name = field_name
        self.msg = msg

    def __str__(self):
        return "{}: {}".format(self.field_name, self.msg)

    def add_container_name(self, name):
        self.field_name = name + "." + self.field_name


class ValidationErrors(Exception):
    def __init__(self, errors: Sequence[ValidationError]):
        self.errors = errors

    def __str__(self):
        return "\n".join(str(x) for x in self.errors)

    def add_container_name(self, name):
        for e in self.errors:
            e.add_container_name(name)
