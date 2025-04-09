
FILES=`ls docker-compose.*.yaml`
# A little nasty here, but we can do it!
# The grep finds the 'rom-test-<service version>' in the .yaml
# The sed removes extra spaces and colons
# Which we pass into our rebuild
GET_TARGET=grep crontab-test $${target} | sed 's/[ :]//g'
GET_TARGET2=grep crontab-test-$${target} docker-compose.yaml | sed 's/[ :]//g'

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

default: perms
	find . -type f | sudo xargs chmod -x

perms:
	-sudo chown ${USER}:${USER} -R .

clean: default
	-rm -f *.pyc crontab/*.pyc README.html MANIFEST
	-rm -rf build crontab.egg-info

compose-build-all:
	docker-compose build

compose-build-%:
	for target in $(patsubst compose-build-%,%,$@) ; do \
		docker-compose build `${GET_TARGET2}`; \
	done

testall:
	make -j1 test-3.13 test-3.12 test-3.11 test-3.10 test-3.9 test-3.8 test-3.7 test-3.6 test-3.5 test-3.4 test-2.7

test-%:
	# the test container runs the tests on up, then does an exit 0 when done
	for target in $(patsubst test-%,%,$@) ; do \
		docker-compose run --rm `${GET_TARGET2}` ; \
	done

upload:
	docker-compose run --rm -w /source crontab-test-uploader python3.13 -m build --sdist
	docker-compose run --rm -w /source crontab-test-uploader python3.13 -m twine upload --skip-existing dist/*.tar.gz
	make perms
