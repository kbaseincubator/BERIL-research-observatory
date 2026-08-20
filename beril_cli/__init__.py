from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("beril-cli")
except PackageNotFoundError:
    # Running from source without an installed distribution (e.g. editable
    # checkout that was never `pip install`-ed) — no version metadata exists.
    __version__ = "0+unknown"
