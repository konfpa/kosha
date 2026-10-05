# kosha

A Django web app for personal finance.

## Requirements

- Python 3.14+
- [uv](https://docs.astral.sh/uv/)

## Setup

```sh
uv sync
uv run prek install
cp .env.example .env  # then set SECRET_KEY; see comments in the file
uv run manage.py migrate
uv run manage.py runserver
```

## Linting

```sh
uv run ruff check
uv run ruff format
```

## License

[MIT](LICENSE)
