# Python Rules (enforced)

- Python 3.11+ syntax only
- Type hints on all public functions (`def fn(x: int) -> str:`)
- `pathlib.Path` for all file paths — never `os.path.join`
- `dataclasses.dataclass` for data schemas — never plain dicts as function args
- `logging.getLogger(__name__)` — never `print()` in production code
- No bare `except:` — always `except SpecificError as e:`
- `pytest` for tests — file naming: `tests/unit/test_<module>.py`
- `TEST_<ClassName>_<describes_behaviour>` naming for test functions
- FastAPI: return `dict` from handlers, not custom objects
- All environment variables via `python-dotenv` — never hardcode keys
