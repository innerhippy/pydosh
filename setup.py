from setuptools import setup

def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='pydosh',
	version='0.1',
	description='Bank statement transaction manager, written in PyQt',
	long_description=readme(),
	url='http://github.com/innerhippy/pydosh',
	author='Will Hall',
	author_email='will@innerhippy.com',
	license='GPL3',
	packages=['pydosh'],
#	install_requires=[
#		'python-qt',
#		'libqt4-sql',
#		'libqt4-sql-psql',
#	],
#    data_files=[
#       ('share/applications', ['pydosh.desktop']),
#      ('share/pixmaps', ['ui/icons/pydosh.png', 'ui/icons/pydosh.xpm']),
#   ],
    scripts = ['scripts/pydosh'],
    requires=['PyQt4'],
	zip_safe=False)
