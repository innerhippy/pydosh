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
                    'PyQt5.QtDesigner',
                    'PyQt5.QtDeclarative',
                    'PyQt5.QtHelp',
                    'PyQt5.QtMultimedia',
                    'PyQt5.QtSvg',
                    'PyQt5.QtXml',
                    'PyQt5.QtOpenGL',
                    'PyQt5.QtTest',
                    'PyQt5.QtWebKit',
                    'PyQt5.QtScriptTools',
                    'PyQt5.QtXmlPatterns',
                    'PyQt5.QtNetwork',
                    'PyQt5.QtScript',
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
    description='Bank statement transaction manager, written in PyQt5',
    long_description=readme(),
    url='http://github.com/innerhippy/pydosh',
    author='Will Hall',
    author_email='will@innerhippy.com',
    license='GPLv3',
    packages=['pydosh', 'pydosh.dialogs', 'pydosh.models', 'pydosh.delegates'],
    zip_safe=False,
    test_suite='tests',
    **extra_options)
