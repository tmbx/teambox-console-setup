#
# Teambox console setup python library
#

all:
	:

clean:
	rm -f *.pyc

install:
	mkdir -p /usr/share/python-support/teambox-console-setup/
	cp -a kplatshell.py /usr/bin/kplatshell
	cp -a kasmodel.py /usr/share/python-support/teambox-console-setup/
	cp -a kasmodeltool.py /usr/share/python-support/teambox-console-setup/

	update-python-modules teambox-console-setup

setup_py:
	# Create a setup.py file using setup.py.tmpl file and set the version to the head HG rev.
	cat setup.py.tmpl | sed "s/__VERSION__/`hg head | head -1 | sed 's#changeset: *\([0-9]*\):.*#\1#g'`/g" > setup.py

egg: setup_py
	# Build the egg
	python setup.py bdist_egg

