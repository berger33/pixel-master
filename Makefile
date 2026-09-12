.PHONY: install test lint run-api run-web clean

install:
	python3 -m venv backend/.venv
	backend/.venv/bin/pip install -r backend/requirements-dev.txt
	cd frontend && npm install

test:
	cd backend && .venv/bin/python -m pytest -q

lint:
	cd backend && .venv/bin/ruff check app tests
	cd frontend && npx tsc --noEmit

run-api:
	cd backend && .venv/bin/python -m uvicorn app.main:app --reload --port 8000

run-web:
	cd frontend && npm run dev

clean:
	rm -rf backend/.pytest_cache backend/.ruff_cache backend/var backend/*.db frontend/dist
