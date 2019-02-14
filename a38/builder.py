from contextlib import contextmanager
import xml.etree.ElementTree as ET


class Builder:
    def __init__(self, etreebuilder=None):
        if etreebuilder is None:
            etreebuilder = ET.TreeBuilder()
        self.etreebuilder = etreebuilder
        self.default_namespace = None

    def _decorate_tag_name(self, tag: str):
        if self.default_namespace is not None and not tag.startswith("{"):
            return "{" + self.default_namespace + "}" + tag
        return tag

    def add(self, tag: str, value: str, **attrs):
        tag = self._decorate_tag_name(tag)
        self.etreebuilder.start(tag, attrs)
        if value is not None:
            self.etreebuilder.data(value)
        self.etreebuilder.end(tag)

    @contextmanager
    def element(self, tag: str, **attrs):
        tag = self._decorate_tag_name(tag)
        self.etreebuilder.start(tag, attrs)
        yield self
        self.etreebuilder.end(tag)

    @contextmanager
    def override_default_namespace(self, ns):
        b = Builder(self.etreebuilder)
        b.default_namespace = ns
        yield b

    def get_tree(self):
        root = self.etreebuilder.close()
        return ET.ElementTree(root)
