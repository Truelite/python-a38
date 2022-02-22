install-os:
	sudo apt-get install \
		openssl \
		wkhtmltopdf \
		eatmydata

install-py:
	pip install -r requirements-lib.txt
	pip install -r requirements-devops.txt

test:
	sh test-coverage

install-package:
	pip install .
