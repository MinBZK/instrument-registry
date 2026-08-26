import sys

from instrument_registry.validate import validate_all


def main() -> int:
    errors = validate_all()
    for error in errors:
        print(f"{error.file}: {error.message}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
