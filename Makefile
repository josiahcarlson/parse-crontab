
FILES=`ls docker-compose.*.yaml`
# A little nasty here, but we can do it!
# The grep finds the 'rom-test-<service version>' in the .yaml
# The sed removes extra spaces and colons
# Which we pass into our rebuild
GET_TARGET=grep crontab-test $${target} | sed 's/[ :]//g'
GET_TARGET2=grep crontab-test docker-compose.$${target}.yaml | sed 's/[ :]//g'
DASH_TO_DOTS=sed 's/[-]/\./g'
COMPOSE_PREFIX=docker-compose -f docker-compose.

SHELL=/bin/bash
# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
PAPER         =
BUILDDIR      = _build
# Internal variables.
PAPEROPT_a4     = -D latex_paper_size=a4
PAPEROPT_letter = -D latex_paper_size=letter
ALLSPHINXOPTS   = -d $(BUILDDIR)/doctrees $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) source
# the i18n builder cannot share the environment and doctrees with the others
I18NSPHINXOPTS  = $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) source

.PHONY: clean docs test

default:
	find . -type f | xargs chmod -x

clean:
	-rm -f *.pyc crontab/*.pyc README.html MANIFEST
	-rm -rf build dist

install:
	python setup.py install


compose-build-all:
	for target in ${FILES} ; do \
		docker-compose -f $${target} build `${GET_TARGET}`; \
	done

compose-build-%:
	for target in $(patsubst compose-build-%,%,$@) ; do \
		${COMPOSE_PREFIX}$${target}.yaml build `${GET_TARGET2}`; \
	done

compose-up-%:
	for target in $(patsubst compose-up-%,%,$@) ; do \
		${COMPOSE_PREFIX}$${target}.yaml up --remove-orphans `${GET_TARGET2}`; \
	done

compose-down-%:
	for target in $(patsubst compose-down-%,%,$@) ; do \
		${COMPOSE_PREFIX}$${target}.yaml down `${GET_TARGET2}`; \
	done

testall:
	make -j1 test-3.11 test-3.10 test-3.9 test-3.8 test-3.7 test-3.6 test-3.5 test-3.4 test-2.7

test-%:
	# the test container runs the tests on up, then does an exit 0 when done
	for target in $(patsubst test-%,%,$@) ; do \
		make compose-build-$${target} && make compose-up-$${target}; \
	done

upload:
	python3.6 setup.py sdist upload

