class UnsupportedModelError(ValueError):
    """Raised when a requested model is not supported by HydratEx"""


class UnsupportedRangeError(ValueError):
    """Raised when a requested simulation range is not supported by HydratEx"""


class ConvergenceError(RuntimeError):
    """Raised when HydratEx did not converge to a physical value"""
