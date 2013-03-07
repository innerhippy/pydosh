UI_TARGETS = $(patsubst %.ui,pydosh/ui_%.py,$(notdir $(wildcard ui/*.ui)))
ALL_TARGETS = $(UI_TARGETS) pydosh/pydosh_rc.py

all: $(ALL_TARGETS) 

pydosh/pydosh_rc.py: ui/pydosh.qrc
	pyrcc4 $? -o $@

clean:
	rm -rf $(ALL_TARGETS) pydosh/*.pyc dist/ pydosh.egg-info/ deb_dist/ build/ pydosh*.dmg

$(UI_TARGETS): pydosh/ui_%.py: ui/%.ui
	pyuic4 $< -o $@

deb: clean all
#	python setup.py sdist
#	py2dsc dist/pydosh*.gz
#	(cd deb_dist/pydosh-* && debuild)
#	(cd deb_dist/pydosh-* && debuild --no-lintian)
#	python setup.py --command-packages=stdeb.command sdist_dsc
#	(cd deb_dist/pydosh-* && debuild -uc -us -i -b)
#	python setup.py --command-packages=stdeb.command -x deb.cfg bdist_deb 
#	python setup.py --command-packages=stdeb.command sdist_dsc --mime-desktop-files=pydosh.desktop
#	python setup.py --command-packages=stdeb.command sdist_dsc --mime-desktop-files=pydosh.desktop bdist_deb
#	python setup.py --command-packages=stdeb.command sdist_dsc --extra-cfg-file=deb.cfg  bdist_deb
	python setup.py --command-packages=stdeb.command sdist_dsc bdist_deb
#	--mime-desktop-files=pydosh.desktop
#	(cd deb_dist/pydosh* && dpkg-buildpackage -rfakeroot -uc -us)
#	(cd deb_dist/pydosh-* && debuild)

dmg: clean all
	python setup.py -v py2app
#	cp qt.conf dist/pydosh.app/Contents/Resources/
#	mkdir -p dist/pydosh.app/Contents/qt_plugins/sqldrivers/
#	cp /usr/local//Cellar/qt/4.8.4/plugins/sqldrivers/libqsqlpsql.dylib dist/pydosh.app/Contents/qt_plugins/sqldrivers/
#	cp /usr/local//Cellar/qt/4.8.4/plugins/sqldrivers/libqsqlpsql.dylib dist/pydosh.app/Contents/qt_plugins
#	hdiutil create -srcfolder dist/pydosh.app pydosh.dmg

