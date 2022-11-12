import sys
from typing import Optional

__all__ = [
    "remove_affix",
    "register_excepthook",
]


def remove_affix(
    s: str, prefix: Optional[str] = None, suffix: Optional[str] = None
) -> str:
    if prefix is not None and s.startswith(prefix):
        s = s[len(prefix) :]
    if suffix is not None and s.endswith(suffix):
        s = s[: -len(suffix)]
    return s


def register_excepthook():
    def excepthook(type, value, traceback):
        if type is KeyboardInterrupt:
            # don't capture keyboard interrupts (Ctrl+C)
            sys.__excepthook__(type, value, traceback)
        else:
            ipython_hook(type, value, traceback)

    # enter IPython debugger on exception
    from IPython.core import ultratb

    ipython_hook = ultratb.FormattedTB(
        mode="Context", color_scheme="Linux", call_pdb=True
    )
    sys.excepthook = excepthook
