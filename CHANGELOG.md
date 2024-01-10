# New in version UNRELEASED

New in version 0.1.7

* Allow ranges of decimal digits in some fields, to match specifications more
  closely
* Added `allegati` subcommand to list and extract attachments. See #32
* Allow more than one DatiRitenuta tag in DatiGeneraliDocumento, thanks
  @tschager, see #38
* Bump minimum supported Python version to 3.11

# New in version 0.1.6

* Generate `dati_riepilogo` with properly set `natura` (#27)
* Ignore non-significant digits when computing differences between Decimal fields
* a38tool diff: return exit code 0 if there are no differences
* Change Prezzo Unitario decimals precision to 3 digits, thanks @matteorizzello
* Fixed a rounding issue (#35), thanks @tschager
* Updated signature in test certificate

# New in version 0.1.5

* Added to `a38.codec` has a basic implementation of interactive editing in a
  text editor

# New in version 0.1.4

* When a Model instance is required, allow to pass a dict matching the Model
  fields instead
* `natura_iva` is now from 2 to 4 characters long (#18)
* Added a38.consts module with constants for common enumerations (#18)
* Added `DettaglioLinee.autofill_prezzo_totale`
* Export `a38.fattura.$MODEL` models as `a38.$MODEL`
* Implemented `a38tool yaml` to export in YAML format
* Implemented loading from YAML and JSON as if they were XML
* Implemented `a38tool edit` to open a fattura in a text editor using YAML or
  Python formats (#22)
* Use UTF-8 encoding and include xml declaration when writing XML from a38tool
  (#19)
* New module `a38.codec`, with functions to load and save from/to all supported
  formats
* Use defusedxml for parsing if available (#24)
