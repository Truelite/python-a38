#!/usr/bin/python3
import argparse
import logging
import contextlib
import sys
import os.path
import shutil
from pathlib import Path
import a38.fattura as a38
import xml.etree.ElementTree as ET

log = logging.getLogger("a38tool")


class Fail(Exception):
    pass


class App:
    NAME = None

    def __init__(self, args):
        pass

    def load_fattura(self, pathname):
        if pathname.endswith(".p7m"):
            from a38.crypto import P7M
            p7m = P7M(pathname)
            return p7m.get_fattura()
        else:
            tree = ET.parse(pathname)
            return a38.auto_from_etree(tree.getroot())

    @classmethod
    def add_subparser(cls, subparsers):
        parser = subparsers.add_parser(cls.NAME, help=cls.__doc__.strip())
        parser.set_defaults(app=cls)
        return parser


class Diff(App):
    """
    show the difference between two fatture
    """
    NAME = "diff"

    def __init__(self, args):
        super().__init__(args)
        self.first = args.first
        self.second = args.second

    @classmethod
    def add_subparser(cls, subparsers):
        parser = super().add_subparser(subparsers)
        parser.add_argument("first", help="first input file (.xml or .xml.p7m)")
        parser.add_argument("second", help="second input file (.xml or .xml.p7m)")
        return parser

    def run(self):
        first = self.load_fattura(self.first)
        second = self.load_fattura(self.second)
        from a38.diff import Diff
        res = Diff()
        first.diff(res, second)
        if res:
            for d in res.differences:
                print(d)
            return 1


class Validate(App):
    """
    validate the contents of a fattura
    """
    NAME = "validate"

    def __init__(self, args):
        super().__init__(args)
        self.pathname = args.file

    @classmethod
    def add_subparser(cls, subparsers):
        parser = super().add_subparser(subparsers)
        parser.add_argument("file", help="input file (.xml or .xml.p7m)")
        return parser

    def run(self):
        f = self.load_fattura(self.pathname)
        from a38.validation import Validation
        res = Validation()
        f.validate(res)
        if res.warnings:
            for w in res.warnings:
                print(str(w), file=sys.stderr)
        if res.errors:
            for e in res.errors:
                print(str(e), file=sys.stderr)
            return 1


class Exporter(App):
    WRITE_MODE = None

    def __init__(self, args):
        super().__init__(args)
        self.files = args.files
        self.output = args.output

    @contextlib.contextmanager
    def open_output(self):
        if self.output is None:
            if "b" in self.WRITE_MODE:
                yield sys.stdout.buffer
            else:
                yield sys.stdout
        else:
            with open(self.output, self.WRITE_MODE) as out:
                yield out

    def run(self):
        with self.open_output() as out:
            for pathname in self.files:
                f = self.load_fattura(pathname)
                self.write(f, out)

    @classmethod
    def add_subparser(cls, subparsers):
        parser = super().add_subparser(subparsers)
        parser.add_argument("-o", "--output", help="output file (default: standard output)")
        parser.add_argument("files", nargs="+", help="input files (.xml or .xml.p7m)")
        return parser


class ExportJSON(Exporter):
    """
    output a fattura in JSON
    """
    NAME = "json"
    WRITE_MODE = "wt"

    def __init__(self, args):
        super().__init__(args)
        if args.indent == "no":
            self.indent = None
        else:
            try:
                self.indent = int(args.indent)
            except ValueError:
                raise Fail("--indent argument must be an integer on 'no'")

    def write(self, f, out):
        import json
        json.dump(f.to_jsonable(), out, indent=self.indent)
        out.write("\n")

    @classmethod
    def add_subparser(cls, subparsers):
        parser = super().add_subparser(subparsers)
        parser.add_argument("--indent", default="1",
                            help="indentation space (default: 1, use 'no' for all in one line)")
        return parser


class ExportXML(Exporter):
    """
    output a fattura in XML
    """
    NAME = "xml"
    WRITE_MODE = "wb"

    def write(self, f, out):
        tree = f.build_etree()
        tree.write(out)
        out.write(b"\n")

    @classmethod
    def add_subparser(cls, subparsers):
        parser = super().add_subparser(subparsers)
        return parser


class ExportPython(Exporter):
    """
    output a fattura as Python code
    """
    NAME = "python"
    WRITE_MODE = "wt"

    def __init__(self, args):
        super().__init__(args)
        self.namespace = args.namespace
        if self.namespace == "":
            self.namespace = False
        self.unformatted = args.unformatted

    def get_code(self, f):
        code = f.to_python(namespace=self.namespace)
        if self.unformatted:
            return code

        try:
            from yapf.yapflib import yapf_api
        except ModuleNotFoundError:
            return code
        code, changed = yapf_api.FormatCode(code)
        return code

    def write(self, f, out):
        print(self.get_code(f), file=out)

    @classmethod
    def add_subparser(cls, subparsers):
        parser = super().add_subparser(subparsers)
        parser.add_argument("--namespace", default=None,
                            help="namespace to use for the model classes (default: the module fully qualified name)")
        parser.add_argument("--unformatted", action="store_true",
                            help="disable code formatting, outputting a single-line statement")
        return parser


class Renderer(App):
    def __init__(self, args):
        from a38.render import HAVE_LXML
        if not HAVE_LXML:
            raise Fail("python3-lxml is needed for XSLT based rendering")

        super().__init__(args)
        self.stylesheet = args.stylesheet
        self.files = args.files
        self.output = args.output
        self.force = args.force

        from a38.render import XSLTTransform
        self.transform = XSLTTransform(self.stylesheet)

    def run(self):
        for pathname in self.files:
            dirname = os.path.normpath(os.path.dirname(pathname))
            basename = os.path.basename(pathname)
            basename, ext = os.path.splitext(basename)
            output = self.output.format(dirname=dirname, basename=basename, ext=ext)
            if not self.force and os.path.exists(output):
                log.warning("%s: output file %s already exists: skipped", pathname, output)
            else:
                log.info("%s: writing %s", pathname, output)
            f = self.load_fattura(pathname)
            self.render(f, output)

    @classmethod
    def add_subparser(cls, subparsers):
        parser = super().add_subparser(subparsers)
        parser.add_argument("-f", "--force", action="store_true", help="overwrite existing output files")
        default_output = "{dirname}/{basename}{ext}." + cls.NAME
        parser.add_argument("-o", "--output",
                            default=default_output,
                            help="output file; use {dirname} for the source file path,"
                                 " {basename} for the source file name"
                                 " (default: '" + default_output + "'")
        parser.add_argument("stylesheet", help=".xsl/.xslt stylesheet file to use for rendering")
        parser.add_argument("files", nargs="+", help="input files (.xml or .xml.p7m)")
        return parser


class RenderHTML(Renderer):
    """
    render a Fattura as HTML using a .xslt stylesheet
    """
    NAME = "html"

    def render(self, f, output):
        html = self.transform(f)
        html.write(output)


class RenderPDF(Renderer):
    """
    render a Fattura as PDF using a .xslt stylesheet
    """
    NAME = "pdf"

    def __init__(self, args):
        super().__init__(args)
        self.wkhtmltopdf = shutil.which("wkhtmltopdf")
        if self.wkhtmltopdf is None:
            raise Fail("wkhtmltopdf is needed for PDF rendering")

    def render(self, f, output):
        self.transform.to_pdf(self.wkhtmltopdf, f, output)


class UpdateCAPath(App):
    """
    create/update an openssl CApath with CA certificates that can be used to
    validate digital signatures
    """
    NAME = "update_capath"

    def __init__(self, args):
        super().__init__(args)
        self.destdir = Path(args.destdir)
        self.remove_old = args.remove_old

    @classmethod
    def add_subparser(cls, subparsers):
        parser = super().add_subparser(subparsers)
        parser.add_argument("destdir", help="CA certificate directory to update")
        parser.add_argument("--remove-old", action="store_true", help="remove old certificates")
        return parser

    def run(self):
        from a38 import trustedlist as tl
        tl.update_capath(self.destdir, remove_old=self.remove_old)


def main():
    parser = argparse.ArgumentParser(description="Handle fattura elettronica files")
    parser.add_argument("--verbose", "-v", action="store_true", help="verbose output")
    parser.add_argument("--debug", action="store_true", help="debug output")

    subparsers = parser.add_subparsers(help="actions", required=True)
    subparsers.dest = "command"

    ExportJSON.add_subparser(subparsers)
    ExportXML.add_subparser(subparsers)
    ExportPython.add_subparser(subparsers)
    Diff.add_subparser(subparsers)
    Validate.add_subparser(subparsers)
    RenderHTML.add_subparser(subparsers)
    RenderPDF.add_subparser(subparsers)
    UpdateCAPath.add_subparser(subparsers)

    args = parser.parse_args()

    log_format = "%(levelname)s %(message)s"
    level = logging.WARN
    if args.debug:
        level = logging.DEBUG
    elif args.verbose:
        level = logging.INFO
    logging.basicConfig(level=level, stream=sys.stderr, format=log_format)

    app = args.app(args)
    res = app.run()
    if isinstance(res, int):
        sys.exit(res)


if __name__ == "__main__":
    try:
        main()
    except Fail as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    except Exception:
        log.exception("uncaught exception")
