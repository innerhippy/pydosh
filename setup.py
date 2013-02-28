from setuptools import setup
from pydosh import version

def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='pydosh',
	version=version.__VERSION__,
	description='Bank statement transaction manager, written in PyQt',
	long_description=readme(),
	url='http://github.com/innerhippy/pydosh',
	author='Will Hall',
	author_email='will@innerhippy.com',
	license='LICENSE.txt',
	packages=['pydosh'],
    data_files=[
        ('share/applications', ['pydosh.desktop']),
        ('share/pixmaps', ['ui/icons/pydosh.png', 'ui/icons/pydosh.xpm']),
    ],
    scripts = ['scripts/pydosh'],
	zip_safe=False)
