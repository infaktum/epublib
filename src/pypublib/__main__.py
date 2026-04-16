def main() -> None:
    """
    Entry point for pypublib when run as a module.

    Prints the current version of pypublib to stdout.

    Example:
        Run with: python -m pypublib
    """
    from . import __version__
    print(f"pypublib {__version__}")