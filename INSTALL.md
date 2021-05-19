Installation notes
==================

Ubuntu
------

To build a debian package type:

```bash
make deb
```

or:

```bash
python setup.py --command-packages=stdeb.command sdist_dsc bdist_deb
```

Upload changes to PyPi:

```bash
python setup.py sdist bdist upload
```

OSX
---

* Install python3 (eg `brew install python3`)
* Update pip `python3 -m pip install --upgrade pip --user`
* Install PyQt5 `python3 -m pip install PyQt5 --user`
* Add PyQt5 binaries to PATH `echo 'export PATH=$HOME/Library/Python/3.8/bin:$PATH' >> ~/.zshrc`
* Generate UI files `make`
* Install Postgres libraries `brew install libpq`
* Enable libpq libraries to be visible in path `brew link libpq --force`

Generate app:

```bash
python setup.py -v py2app
```

Create dmg file

```bash
hdiutil create -srcfolder dist/pydosh.app pydosh.dmg
```

Shortcut

```bash
make dmg
```
