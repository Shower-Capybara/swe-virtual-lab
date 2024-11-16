APP_PORT ?= 8000

.PHONY: seed
seed:
	@poetry run python -m seeder


.PHONY: run
run:
	@poetry run uvicorn --port ${APP_PORT} --reload src.server.main:app
