install:
	python setup.py install
develop:
	python setup.py develop
build:
	python setup.py build
clean:
	rm -f $$(find . | grep "[.]pyc")
	rm -f $$(find . | grep "~$$")
purge: clean
	rm -rf build
	rm -rf src/*.egg-info
