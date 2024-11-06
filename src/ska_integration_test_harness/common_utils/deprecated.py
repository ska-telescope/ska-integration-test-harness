"""A meta-class to mark deprecated classes."""

import warnings


class DeprecatedMeta(type):
    """A meta-class to mark deprecated classes."""

    def __call__(cls, *args, **kwargs):
        warnings.warn(
            f"{cls.__name__} is deprecated and will be "
            "removed in a future version.",
            DeprecationWarning,
            stacklevel=2,
        )
        return super().__call__(*args, **kwargs)
