from typing import Any


class Filter:
    pass


def apply_filters(value: Any) -> Any:
    """Recursively filter out any values that are instances of Filter."""
    if isinstance(value, Filter):
        pass
    elif isinstance(value, list):
        filtered_list = []
        for item in value:
            filtered_item = apply_filters(item)
            if filtered_item is not None:
                filtered_list.append(filtered_item)
        return filtered_list
    elif isinstance(value, dict):
        filtered_dict = {}
        for k, v in value.items():
            filtered_value = apply_filters(v)
            if filtered_value is not None:
                filtered_dict[k] = filtered_value
        return filtered_dict
    else:
        return value
