# Run the frontend
run:
	uv run streamlit run src/whats_this_id/frontend/app.py

# Run the backend
run-backend:
	uv run python src/whats_this_id/core/example.py

# Run the linter
lint:
	uv run ruff check --fix && uv run isort --check --profile black . && uv run ruff format
