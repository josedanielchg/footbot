"""Small numeric helpers shared by simulation packages."""


def clamp(value, minimum, maximum):
    """Clamp a numeric value into an inclusive range."""
    return max(minimum, min(maximum, value))
