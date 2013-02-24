UI_TARGETS = $(patsubst %.ui,pydosh/ui_%.py,$(notdir $(wildcard ui/*.ui)))
ALL_TARGETS = $(UI_TARGETS) pydosh/pydosh_rc.py

all: $(ALL_TARGETS) 

pydosh/pydosh_rc.py: ui/pydosh.qrc
	pyrcc4 $? -o $@

clean:
	rm -rf $(ALL_TARGETS) pydosh/*.pyc dist/ pydosh.egg-info/ deb_dist/

$(UI_TARGETS): pydosh/ui_%.py: ui/%.ui
	pyuic4 $< -o $@

deb: clean all
	python setup.py sdist -v
	 py2dsc dist/pydosh*.gz
#	(cd deb_dist/pydosh-* && debuild)
	(cd deb_dist/pydosh-* && debuild --no-lintian)
