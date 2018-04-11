PYTHON=./env/bin/python3
SRC=./aa


.PHONY: lint

lint:
	${PYTHON} -m pylint --output-format=colorized --reports=n ${SRC}
	${PYTHON} -m pycodestyle ${SRC}
	${PYTHON} -m pydocstyle ${SRC}

test:
	${PYTHON} -m unittest discover -v
