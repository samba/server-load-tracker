.PHONY: test


test:
	python -m unittest discover -v -f -s test/ -p 'test_*.py'
