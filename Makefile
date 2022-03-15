ci-workaround:
	sudo sed -i 's/azure\.//' /etc/apt/sources.list
	sudo apt-get -o Acquire::Retries=5 update

install-os:
	sudo apt-get -o Acquire::Retries=5 install \
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

lint:
	isort \
		--check \
		$(PWD)/a38 \
		$(PWD)/tests \
		setup.py
	flake8 \
		--ignore=E126,E203,E501,W503 \
		--max-line-length 120 \
		--indent-size 4 \
		--jobs=8 \
		$(PWD)/a38 \
		$(PWD)/tests \
		setup.py
	bandit \
		--recursive \
		--number=3 \
		-lll \
		-iii \
		$(PWD)/a38 \
		$(PWD)/tests \
		setup.py

lint-dev:
	isort \
		--atomic \
		$(PWD)/a38 \
		$(PWD)/tests \
		setup.py
	$(eval PIP_DEPS=$(shell awk '{printf("%s,",$$1)}' requirements-lib.txt | sed '$$s/,$$//'))
	autoflake \
		--imports=$(PIP_DEPS) \
		--recursive \
		--in-place \
		--remove-unused-variables \
		$(PWD)/a38 \
		$(PWD)/tests \
		setup.py
