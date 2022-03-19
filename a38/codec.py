from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING, Any, BinaryIO, Dict, Optional, TextIO, Union

try:
    import ruamel.yaml
    yaml = None
except ModuleNotFoundError:
    ruamel = None
    try:
        import yaml
    except ModuleNotFoundError:
        yaml = None

from . import crypto
from .fattura import auto_from_dict, auto_from_etree
from .models import Model

if TYPE_CHECKING:
    from .fattura import Fattura
    from .fattura_semplificata import FatturaElettronicaSemplificata


if ruamel is not None:
    def _load_yaml(fd: TextIO):
        yaml_loader = ruamel.yaml.YAML(typ="safe", pure=True)
        return yaml_loader.load(fd)

    def _write_yaml(data: Dict[str, Any], file: TextIO):
        yaml = ruamel.yaml.YAML(typ="safe")
        yaml.default_flow_style = False
        yaml.allow_unicode = True
        yaml.explicit_start = True
        yaml.dump(data, file)
elif yaml is not None:
    def _load_yaml(fd: TextIO):
        return yaml.load(fd, Loader=yaml.CLoader)

    def _write_yaml(data: Dict[str, Any], file: TextIO):
        yaml.dump(
            data, stream=file, default_flow_style=False,
            allow_unicode=True, explicit_start=True, Dumper=yaml.CDumper)
else:
    def _load_yaml(fd: TextIO):
        raise NotImplementedError("loading YAML requires ruamel.yaml or PyYAML to be installed")

    def _write_yaml(data: Dict[str, Any], file: TextIO):
        raise NotImplementedError("writing YAML requires ruamel.yaml or PyYAML to be installed")


class Codec:
    """
    Base class for format-specific reading and writing of fatture
    """
    # If True, file objects are expected to be open in binary mode
    binary = False

    @classmethod
    def from_filename(cls, pathname: str) -> Codec:
        if pathname.endswith(".p7m"):
            return P7M
        elif pathname.endswith(".json"):
            return JSON
        elif pathname.endswith(".yaml"):
            return YAML
        elif pathname.endswith(".py"):
            return Python
        else:
            return XML

    def load(self, pathname: str) -> Union[Fattura, FatturaElettronicaSemplificata]:
        raise NotImplementedError(f"{self.__class__.__name__}.load is not implemented")

    def write_file(self, f: Model, file: Union[TextIO, BinaryIO]):
        raise NotImplementedError(f"{self.__class__.__name__}.write_file is not implemented")


class P7M(Codec):
    """
    P7M codec, that only supports loading
    """
    def load(self, pathname: str) -> Union[Fattura, FatturaElettronicaSemplificata]:
        p7m = crypto.P7M(pathname)
        return p7m.get_fattura()


class JSON(Codec):
    """
    JSON codec.

    `indent` represents the JSON structure indentation, and can be None to
    output everything in a single line.

    `end` is a string that gets appended to the JSON structure.
    """
    def __init__(self, indent: Optional[int] = 1, end="\n"):
        self.indent = indent
        self.end = end

    def load(self, pathname: str) -> Union[Fattura, FatturaElettronicaSemplificata]:
        with open(pathname, "rt") as fd:
            data = json.load(fd)
        return auto_from_dict(data)

    def write_file(self, f: Model, file: TextIO):
        json.dump(f.to_jsonable(), file, indent=self.indent)
        if self.end is not None:
            file.write(self.end)


class YAML(Codec):
    """
    YAML codec
    """
    def load(self, pathname: str) -> Union[Fattura, FatturaElettronicaSemplificata]:
        with open(pathname, "rt") as fd:
            data = _load_yaml(fd)
        return auto_from_dict(data)

    def write_file(self, f: Model, file: TextIO):
        _write_yaml(f.to_jsonable(), file)


class Python(Codec):
    """
    Python codec.

    `namespace` defines what namespace is used to refer to `a38` models. `None`
    means use a default, `False` means not to use a namespace, a string defines
    which namespace to use.

    `unformatted` can be set to True to skip code formatting.

    The code will be written with just the expression to build the fattura.

    The code assumes `import datetime` and `from decimal import Decimal`.

    Note that loading Python fatture executes arbitrary Python code!
    """
    def __init__(self, namespace: Union[None, bool, str] = "a38", unformatted: bool = False):
        self.namespace = namespace
        self.unformatted = unformatted

    def load(self, pathname: str) -> Union[Fattura, FatturaElettronicaSemplificata]:
        with open(pathname, "rt") as fd:
            code = compile(fd.read(), pathname, 'exec')

        loc = {}
        exec(code, {}, loc)
        return loc["fattura"]

    def write_file(self, f: Model, file: TextIO):
        code = f.to_python(namespace=self.namespace)

        if not self.unformatted:
            try:
                from yapf.yapflib import yapf_api
            except ModuleNotFoundError:
                return code
            code, changed = yapf_api.FormatCode(code)

        print(code, file=file)


class XML(Codec):
    """
    XML codec
    """
    binary = True

    def load(self, pathname: str) -> Union[Fattura, FatturaElettronicaSemplificata]:
        tree = ET.parse(pathname)
        return auto_from_etree(tree.getroot())

    def write_file(self, f: Model, file: BinaryIO):
        tree = f.build_etree()
        tree.write(file, encoding="utf-8", xml_declaration=True)
        file.write(b"\n")
