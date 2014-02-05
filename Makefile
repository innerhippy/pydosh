UI_TARGETS=$(patsubst %.ui,pydosh/ui_%.py,$(notdir $(wildcard ui/*.ui)))
ALL_TARGETS=$(UI_TARGETS) pydosh/pydosh_rc.py
VERSION=$(shell python -c 'from pydosh import __version__; print __version__')

all: $(ALL_TARGETS)

pydosh/pydosh_rc.py: ui/pydosh.qrc ui/*.qss sql/*.sql
	pyside-rcc $< -o $@

clean:
	@find pydosh \( -name "*.pyc" -o -name "ui_*.py" -o -name "*_rc.py" \) -delete
	@rm -rf \
		dist/ \
		pydosh.egg-info/ \
		deb_dist/ \
		build/ \
		pydosh*.dmg

$(UI_TARGETS): pydosh/ui_%.py: ui/%.ui
	pyside-uic $< -o $@

deb: clean all
	python setup.py --command-packages=stdeb.command sdist_dsc bdist_deb

dmg: clean all
	python setup.py py2app
	hdiutil create -srcfolder dist/pydosh.app pydosh-$(VERSION).dmg

