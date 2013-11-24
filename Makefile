clean:
	rm -f $$(find . | grep "~$$")
	rm -f $$(find . | grep "[.]pyc$$")
