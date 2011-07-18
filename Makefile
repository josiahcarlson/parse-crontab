SHELL=/bin/bash

clean:
	-rm -f *.pyc crontab/*.pyc README.html MANIFEST
	-rm -rf build dist

install:
	python setup.py install

test:
	python -m tests.test_crontab

upload:
	python setup.py sdist upload
