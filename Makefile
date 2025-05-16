install:
	pip install -e .

format:
	black rosbeat

lint:
	flake8 rosbeat
	
run:
	python -m rosbeat --config config.yml
