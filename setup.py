import sys
from setuptools import setup
from pydosh import version

def readme():
    with open('README.rst') as f:
        return f.read()

if sys.platform == 'darwin':
	extra_options = {
		setup_requires=['py2app'],
		app=['pydosh/pydosh.py'],
		options={
			py2app: {
				'argv_emulation': True,
				'includes': ['sip', 'PyQt4']
			},
		},
	}
elif sys.platform == 'win32':
	raise Exception('Sorry, Windows is not supported. Please upgrade to Unix')
else: # Unix
	extra_options = {
		scripts=['scripts/pydosh'],
	}

setup(name='pydosh',
	version=version.__VERSION__,
	description='Bank statement transaction manager, written in PyQt',
	long_description=readme(),
	url='http://github.com/innerhippy/pydosh',
	author='Will Hall',
	author_email='will@innerhippy.com',
	license='GPL3',
	packages=['pydosh'],
    data_files=[
        ('share/applications', ['pydosh.desktop']),
        ('share/pixmaps', ['ui/icons/pydosh.png', 'ui/icons/pydosh.xpm']),
    ],
    scripts = ['scripts/pydosh'],
	zip_safe=False,
	**extra_options)
