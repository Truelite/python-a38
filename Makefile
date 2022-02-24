install-os:
	sudo apt-get install \
		openssl \
		wkhtmltopdf \
		eatmydata \
		python3-nose2

install-py:
	pip install -r requirements-lib.txt

test:
	sh test-coverage

install-package:
	pip install .
