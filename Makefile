.PHONY: setup run test lint clean

setup:
	pip install -r requirements.txt
	python -c "from database.connection import init_db; init_db()"

run:
	python -m streamlit run frontend/app.py

test:
	python -m pytest tests/test_validator.py tests/test_pipeline.py::TestExecutor tests/test_pipeline.py::TestSchemaContext -v

test-all:
	python -m pytest tests/ -v --ignore=tests/test_pipeline.py

lint:
	ruff check .

clean:
	python -c "import shutil, Path; shutil.rmtree(Path('__pycache__'), ignore_errors=True); shutil.rmtree('.pytest_cache', ignore_errors=True)"