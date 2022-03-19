import os
import subprocess
import tempfile
from typing import Optional

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
            Return the ElementTree for f rendered as HTML
            """
            tree = f.build_etree(lxml=True)
            return self.xslt(tree)

        def _requires_enable_local_file_access(self, wkhtmltopdf: str):
            """
            Check if we need to pass --enable-local-file-access to wkhtmltopdf.

            See https://github.com/Truelite/python-a38/issues/6 for details
            """
            # We need to specifically use --extended-help, because --help does
            # not always document --enable-local-file-access
            verifyLocalAccessToFileOption = subprocess.run(
                    [wkhtmltopdf, "--extended-help"], stdin=subprocess.DEVNULL, text=True, capture_output=True)
            return "--enable-local-file-access" in verifyLocalAccessToFileOption.stdout

        def to_pdf(self, wkhtmltopdf: str, f, output_file: Optional[str] = None):
            """
            Render a fattura to PDF using the given wkhtmltopdf command.

            Returns None if output_file is given, or the binary PDF data if not
            """
            if output_file is None:
                output_file = "-"
            html = self(f)

            # TODO: pass html data as stdin, using '-' as input for
            #       wkhtmltopdf: that currently removes the requirement for
            #       --enable-local-file-access
            with tempfile.NamedTemporaryFile("wb", suffix=".html", delete=False) as fd:
                html.write(fd)
                tempFilename = fd.name

            try:
                cmdLine = [wkhtmltopdf, tempFilename, output_file]
                if self._requires_enable_local_file_access(wkhtmltopdf):
                    cmdLine.insert(1, "--enable-local-file-access")

                res = subprocess.run(cmdLine, stdin=subprocess.DEVNULL, capture_output=True)

                if res.returncode != 0:
                    raise RuntimeError(
                            "{0} exited with error {1}: stderr: {2!r}".format(
                                wkhtmltopdf, res.returncode, res.stderr))

                if output_file == "-":
                    return res.stdout
                else:
                    return None
            finally:
                os.remove(tempFilename)
