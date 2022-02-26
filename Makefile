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
	rm \
		--recursive --force \
		$(PWD)/build \
		$(PWD)/dist \
		$(PWD)/htmlcov \
		$(PWD)/a38.egg-info \
		$(PWD)/.coverage

lint:
# The command `isort` sometimes applies a slightly unreadable import style, whereas `black` doesnt.
# However `isort` sorts out much more issues with imports.
# This way we apply `black` twice and make sure the `make lint` command is idempotent.
	black \
		--check \
		$(PWD)/a38 \
		$(PWD)/tests
	isort \
		--atomic \
		$(PWD)/a38 \
		$(PWD)/tests
	black \
		$(PWD)/a38 \
		$(PWD)/tests
# E203 usually happens in `:` ranges inside the `[...]` operator. In this scenario
# the rules applied by `black` are preferred.
# E501 is about lines longer than 79 characters, but we want `black` to drive this rule
# based on the context around that line in the source code.
# TODO introduce "cyclomatic complexity" with `flake8` (C901) via `--max-complexity=4`
	flake8 \
		--ignore=E203,E501,W503 \
		--jobs=8 \
		$(PWD)/a38 \
		$(PWD)/tests
# The `pylint` is very aggressive and widespread - it might be worth removing some codes from the disabled rules
# and see what is going on with those areas of the code.
# In some cases we want to disable some checks e.g. C0301 in favor of other tools e.g. `black`.
# TODO enable E1101,E1133,R0912 and many more and make sense of it.
# TODO sort out types and circular dependencies due to `a38/fields.py`
# pylint \
# 	--disable=C0103,C0114,C0115,C0116,C0301,E1101,E1133,R0201,R0903,R0912,R0914,W0231,W0511,W1510 \
# 	--jobs=4 \
# 	--extension-pkg-allow-list=lxml \
# 	$(PWD)/a38 \
# 	$(PWD)/tests
# TODO sort out types in `a38/fields.py`
# PYTHONPATH=. pytype \
# 	--keep-going \
# 	--jobs=8 \
# 	$(PWD)/a38
	bandit \
		--recursive \
		--number=3 \
		-lll \
		-iii \
		$(PWD)/a38 \
		$(PWD)/tests
