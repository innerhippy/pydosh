UI_TARGETS = $(patsubst %.ui,pydosh/ui_%.py,$(notdir $(wildcard ui/*.ui)))
ALL_TARGETS = $(UI_TARGETS) pydosh/pydosh_rc.py
VERSION=$(shell python -c 'from pydosh import version; print version.__VERSION__')

all: $(ALL_TARGETS) 

pydosh/pydosh_rc.py: ui/pydosh.qrc
	pyrcc4 $? -o $@

clean:
	rm -rf $(ALL_TARGETS) pydosh/*.pyc pydosh/ui_*.py dist/ pydosh.egg-info/ deb_dist/ build/ pydosh*.dmg

$(UI_TARGETS): pydosh/ui_%.py: ui/%.ui
	pyuic4 $< -o $@

deb: clean all
	python setup.py --command-packages=stdeb.command sdist_dsc bdist_deb

dmg: clean all
	python setup.py -v py2app
	hdiutil create -srcfolder dist/pydosh.app pydosh-$(VERSION).dmg

