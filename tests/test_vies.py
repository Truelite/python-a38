from unittest import TestCase

from a38.vies import get_vat_details, inspect_vat

# curl -X POST https://ec.europa.eu/taxation_customs/vies/vatResponse.html \
# 		--silent --show-error \
# 		--header "Content-Type: application/x-www-form-urlencoded" \
# 		--data "memberStateCode=IT&number=00934460049&traderName=&traderStreet=&traderPostalCode=&traderCity=&requesterMemberStateCode=&requesterNumber=&check=Verify&action=check" | \
# 	grep -A2 --color 'static-field'


class TestVIESRetrieval(TestCase):

    sample_country_code_it = "IT"
    sample_vat_num_ferrero = "00934460049"

    # PYTHONPATH=. nose2-3 -s tests test_vies
    def test_api_call(self):
        res_html, status = inspect_vat(
            self.sample_country_code_it, self.sample_vat_num_ferrero
        )
        assert status == 200
        assert len(res_html) > 0

    # PYTHONPATH=. nose2-3 -s tests test_vies
    def test_get_vat_details(self):
        vat_details = get_vat_details(
            self.sample_country_code_it, self.sample_vat_num_ferrero
        )
        # print(vat_details)
        assert len(vat_details) == 6

        # from a38.vies import render_vat_details
        # render_vat_details(vat_details)
