from typing import Any


def get_value_at_path(source: dict, path: str) -> Any:
    """Get the value in a source dict at the given path.

    :param source: The dict from which to extract the value
    :param path: The path to look into
    :return: The value found at the path
    :raises: KeyError when no value exists at the path
    """
    current_location = source
    for part in path.split("."):
        current_location = current_location[part]

    return current_location
