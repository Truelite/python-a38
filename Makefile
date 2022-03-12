install-os:
	sudo apt-get install \
		openssl \
		wkhtmltopdf \
		eatmydata \
		python3-nose2

install-py:
	pip install -r requirements-lib.txt
	pip install -r requirements-devops.txt

test:
	sh test-coverage

install-package:
	pip install .

clean:
	rm --recursive --force \
		$(PWD)/build \
		$(PWD)/dist \
		$(PWD)/htmlcov \
		$(PWD)/a38.egg-info \
		$(PWD)/.coverage

