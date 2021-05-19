PYTHON := python3
UI_TARGETS=$(patsubst %.ui,pydosh/ui_%.py,$(notdir $(wildcard ui/*.ui)))
ALL_TARGETS=$(UI_TARGETS) pydosh/pydosh_rc.py
VERSION=$(shell $(PYTHON) -c 'from pydosh import __version__; print (__version__)')

all: $(ALL_TARGETS)

pydosh/pydosh_rc.py: ui/pydosh.qrc ui/*.qss sql/*.sql
	pyrcc5 $< -o $@

clean:
	@find tests pydosh \( -name "*.pyc" -o -name "ui_*.py" -o -name "*_rc.py" \) -delete
	@rm -rf \
		.eggs/ \
		dist/ \
		pydosh.egg-info/ \
		deb_dist/ \
		build/ \
		pydosh*.dmg

$(UI_TARGETS): pydosh/ui_%.py: ui/%.ui
	pyuic5 --from-imports $< -o $@

deb: clean all
	env PYTHONPATH=$(shell pwd) $(PYTHON) setup.py --command-packages=stdeb.command sdist_dsc bdist_deb

dmg: clean all
	$(PYTHON) setup.py py2app
	hdiutil create -srcfolder dist/pydosh.app pydosh-$(VERSION).dmg

test:
	python3 -m pytest tests/

