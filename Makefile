.PHONY: test


test:
	python -m unittest discover -f -s test/ -p 'test_*.py'
