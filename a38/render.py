from typing import Optional
import tempfile
import subprocess
try:
    import lxml.etree
    HAVE_LXML = True
except ModuleNotFoundError:
    HAVE_LXML = False


if HAVE_LXML:
    class XSLTTransform:
        def __init__(self, xslt):
            parsed_xslt = lxml.etree.parse(xslt)
            self.xslt = lxml.etree.XSLT(parsed_xslt)

        def __call__(self, f):
            """
            Return the xml.etree ElementTree for f rendered as HTML
            """
            tree = f.build_etree(lxml=True)
            return self.xslt(tree)

        def to_pdf(self, wkhtmltopdf: str, f, output_file: Optional[str] = None):
            """
            Render a fattura to PDF using the given wkhtmltopdf command.

            Returns None if output_file is given, or the binary PDF data if not
            """
            if output_file is None:
                output_file = "-"
            html = self(f)
            with tempfile.NamedTemporaryFile("wb", suffix=".html") as fd:
                html.write(fd)
                fd.flush()
                res = subprocess.run([wkhtmltopdf, fd.name, output_file], stdin=subprocess.DEVNULL, capture_output=True)
                if res.returncode != 0:
                    raise RuntimeError("%s exited with error %d: stderr: %s", self.wkhtmltopdf, res.returncode, res.stderr)
            if output_file == "-":
                return res.stdout
