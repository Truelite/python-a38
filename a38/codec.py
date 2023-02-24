from __future__ import annotations

import io
import json
import logging
import os
import subprocess
import tempfile

try:
    from defusedxml import ElementTree as ET
except ModuleNotFoundError:
    import xml.etree.ElementTree as ET

from typing import (Any, BinaryIO, Dict, List, Optional, Sequence, TextIO,
                    Type, Union)

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

log = logging.getLogger("codec")

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
            data, stream=file, default_flow_style=False, sort_keys=False,
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

    def load(
            self,
            pathname: str,
            model: Optional[Type[Model]]) -> Model:
        """
        Load a fattura from a file.

        If model is provided it will be used for loading, otherwise the Model
        type will be autodetected
        """
        raise NotImplementedError(f"{self.__class__.__name__}.load is not implemented")

    def write_file(self, f: Model, file: Union[TextIO, BinaryIO]):
        """
        Write a fattura to the given file deescriptor.
        """
        raise NotImplementedError(f"{self.__class__.__name__}.write_file is not implemented")

    def save(self, f: Model, pathname: str):
        """
        Write a fattura to the given file
        """
        with open(pathname, "wb" if self.binary else "wt") as fd:
            self.write_file(f, fd)

    def interactive_edit(self, f: Model) -> Optional[Model]:
        """
        Edit the given model in an interactive editor, using the format of this
        codec
        """
        with io.StringIO() as orig:
            self.write_file(f, orig)
            return self.edit_buffer(orig.getvalue(), model=f.__class__)

    def edit_buffer(self, buf: str, model: Optional[Type[Model]] = None) -> Optional[Model]:
        """
        Open an editor on buf and return the edited fattura.

        Return None if editing did not change the contents.
        """
        editor = os.environ.get("EDITOR", "sensible-editor")

        current = buf
        error = None

        while True:
            with tempfile.NamedTemporaryFile(
                    mode="wt",
                    suffix=f".{self.EXTENSIONS[0]}") as tf:
                # Write out the current buffer
                tf.write(current)
                if error is not None:
                    tf.write(f"# ERROR: {error}")
                    error = None
                tf.flush()

                # Run the editor on it
                subprocess.run([editor, tf.name], check=True)

                # Reopen by name in case the editor did not write on the same
                # inode
                with open(tf.name, "rt") as fd:
                    lines = []
                    for line in fd:
                        if line.startswith("# ERROR: "):
                            continue
                        lines.append(line)
                    edited = "".join(lines)

                if edited == current:
                    return None

                try:
                    return self.load(tf.name, model=model)
                except Exception as e:
                    log.error("%s: cannot load edited file: %s", tf.name, e)
                    error = str(e)


class P7M(Codec):
    """
    P7M codec, that only supports loading
    """
    EXTENSIONS = ("p7m",)

    def load(
            self,
            pathname: str,
            model: Optional[Type[Model]] = None) -> Model:
        p7m = crypto.P7M(pathname)
        return p7m.get_fattura()


class JSON(Codec):
    """
    JSON codec.

    `indent` represents the JSON structure indentation, and can be None to
    output everything in a single line.

    `end` is a string that gets appended to the JSON structure.
    """
    EXTENSIONS = ("json",)

    def __init__(self, indent: Optional[int] = 1, end="\n"):
        self.indent = indent
        self.end = end

    def load(
            self,
            pathname: str,
            model: Optional[Type[Model]] = None) -> Model:
        with open(pathname, "rt") as fd:
            data = json.load(fd)
        if model:
            return model(**data)
        else:
            return auto_from_dict(data)

    def write_file(self, f: Model, file: TextIO):
        json.dump(f.to_jsonable(), file, indent=self.indent)
        if self.end is not None:
            file.write(self.end)


class YAML(Codec):
    """
    YAML codec
    """
    EXTENSIONS = ("yaml", "yml")

    def load(
            self,
            pathname: str,
            model: Optional[Type[Model]] = None) -> Model:
        with open(pathname, "rt") as fd:
            data = _load_yaml(fd)
        if model:
            return model(**data)
        else:
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

    If loadable is True, the file is written as a Python source that
    creates a `fattura` variable with the fattura, with all the imports that
    are needed. This generates a python file that can be loaded with load().

    Note that loading Python fatture executes arbitrary Python code!
    """
    EXTENSIONS = ("py",)

    def __init__(
            self, namespace: Union[None, bool, str] = "a38",
            unformatted: bool = False,
            loadable: bool = False):
        self.namespace = namespace
        self.unformatted = unformatted
        self.loadable = loadable

    def load(
            self,
            pathname: str,
            model: Optional[Type[Model]] = None) -> Model:
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
                pass
            else:
                code, changed = yapf_api.FormatCode(code)

        if self.loadable:
            print("import datetime", file=file)
            print("from decimal import Decimal", file=file)
            if self.namespace:
                print("import", self.namespace, file=file)
            elif self.namespace is False:
                print("from a38.fattura import *", file=file)
            else:
                print("import a38", file=file)
            print(file=file)
            print("fattura = ", file=file, end="")
        print(code, file=file)


class XML(Codec):
    """
    XML codec
    """
    EXTENSIONS = ("xml",)

    binary = True

    def load(
            self,
            pathname: str,
            model: Optional[Type[Model]] = None) -> Model:
        tree = ET.parse(pathname)
        return auto_from_etree(tree.getroot())

    def write_file(self, f: Model, file: BinaryIO):
        tree = f.build_etree()
        tree.write(file, encoding="utf-8", xml_declaration=True)
        file.write(b"\n")


class Codecs:
    """
    A collection of codecs
    """
    ALL_CODECS = (XML, P7M, JSON, YAML, Python)

    def __init__(
            self,
            include: Optional[Sequence[Type[Codec]]] = None,
            exclude: Optional[Sequence[Type[Codec]]] = (Python,)):
        """
        if `include` is not None, only codecs in that list are used.

        If `exclude` is not None, all codecs are used except the given one.

        If neither `include` nor `exclude` are None, all codecs are used.

        By default, `exclude` is not None but it is set to exclude Python.
        """
        self.codecs: List[Type[Codec]]

        if include is not None and exclude is not None:
            raise ValueError("include and exclude cannot both be set")
        elif include is not None:
            self.codecs = list(include)
        elif exclude is not None:
            self.codecs = [c for c in self.ALL_CODECS if c not in exclude]
        else:
            self.codecs = list(self.ALL_CODECS)

    def codec_from_filename(self, pathname: str) -> Type[Codec]:
        """
        Infer a Codec class from the extension of the file at `pathname`.
        """
        ext = pathname.rsplit(".", 1)[1].lower()

        for c in self.codecs:
            if ext in c.EXTENSIONS:
                return c
