import sys
from setuptools import setup
from pydosh import __version__

def readme():
    with open('README.rst') as f:
        return f.read()

if sys.platform == 'darwin':
    extra_options = dict(
        setup_requires=['py2app'],
        app=['pydosh/main.py'],
        data_files=['pydosh'],
        options = dict(
            py2app = dict(
                argv_emulation=True,
                excludes=[
                    'PySide.QtDesigner',
                    'PySide.QtDeclarative',
                    'PySide.QtHelp',
                    'PySide.QtMultimedia',
                    'PySide.QtSvg',
                    'PySide.QtXml',
                    'PySide.QtOpenGL',
                    'PySide.QtTest',
                    'PySide.QtWebKit',
                    'PySide.QtScriptTools',
                    'PySide.QtXmlPatterns',
                    'PySide.QtNetwork',
                    'PySide.QtScript',
                ],
                iconfile='icons/pydosh.icns',
                qt_plugins=['sqldrivers/libqsqlpsql.dylib'],
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
    version=__version__,
    description='Bank statement transaction manager, written in PySide',
    long_description=readme(),
    url='http://github.com/innerhippy/pydosh',
    author='Will Hall',
    author_email='will@innerhippy.com',
    license='GPLv3',
    packages=['pydosh', 'pydosh.dialogs', 'pydosh.models', 'pydosh.delegates'],
    zip_safe=False,
	test_suite='tests',
    **extra_options)
