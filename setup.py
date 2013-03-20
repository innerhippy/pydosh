import sys
from setuptools import setup
from pydosh import version

def readme():
    with open('README.rst') as f:
        return f.read()

if sys.platform == 'darwin':
	extra_options = dict(
		setup_requires=['py2app'],
		app=['pydosh/pydosh.py'],
		data_files=['pydosh'],
		options = dict(
			py2app = dict(
				argv_emulation=True, 
#				includes=['sip', 'PyQt4.QtCore'], # These are imported automatically
				excludes=[
					'PyQt4.QtDesigner', 
					'PyQt4.QtDeclarative', 
					'PyQt4.QtHelp', 
					'PyQt4.QtMultimedia',
					'PyQt4.QtSvg',
					'PyQt4.QtXml',
					'PyQt4.QtOpenGL',
					'PyQt4.QtTest',
					'PyQt4.QtWebKit',
					'PyQt4.QtScriptTools',
					'PyQt4.QtXmlPatterns',
					'PyQt4.QtNetwork',
					'PyQt4.QtScript',
				],
				iconfile='icons/pydosh.icns',
				qt_plugins=['sqldrivers'],
			)
		)
	)
elif sys.platform == 'win32':
	raise Exception('Sorry, Windows is not supported. Please upgrade to Unix')
else: # Unix
	extra_options = dict(
		scripts=['scripts/pydosh'],
        	data_files=[
			('share/applications', ['pydosh.desktop']),
			('share/pixmaps', ['icons/pydosh.png', 'icons/pydosh.xpm']),
		],
	)

setup(name='pydosh',
	version=version.__VERSION__,
	description='Bank statement transaction manager, written in PyQt',
	long_description=readme(),
	url='http://github.com/innerhippy/pydosh',
	author='Will Hall',
	author_email='will@innerhippy.com',
	license='GPLv3',
	packages=['pydosh'],
	zip_safe=False,
	**extra_options)
