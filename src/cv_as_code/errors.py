"""Domain errors. The CLI prints the message and exits 1; nothing else is caught broadly."""


class CvacError(Exception):
    """A user-facing failure: wrong input, a broken reference, a gate that did not pass."""


class ValidationError(CvacError):
    """A document fails its schema, its references or the approval gate."""


class RenderError(CvacError):
    """The deterministic tail (resolve/render) cannot produce its output."""
