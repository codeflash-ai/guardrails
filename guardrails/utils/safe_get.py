from typing import Any, Dict, List, Optional, Tuple, Union
from guardrails.logger import logger


def safe_get_with_brackets(
    container: Union[str, List[Any], Any], key: Any, default: Optional[Any] = None
) -> Any:
    try:
        value = container[key]
        if not value:
            return default
        return value
    except Exception as e:
        logger.debug(
            f"""
            Failed to get value for key: {key} out of container: {container}.
            Reason: {e}
            Fallbacking to default value...
            """
        )
        return default


def safe_get(
    container: Union[str, List[Any], Dict[Any, Any], Tuple],
    key: Any,
    default: Optional[Any] = None,
) -> Any:
    # Fast path for dict
    if isinstance(container, dict):
        return container.get(key, default)
    # Fast path for list and tuple (avoid function call; catch IndexError/TypeError directly)
    elif isinstance(container, (list, tuple, str)):
        try:
            value = container[key]
            if not value:
                return default
            return value
        except Exception:
            return default
    else:
        # Fallback to original, potentially custom handling
        from guardrails.utils.safe_get import safe_get_with_brackets

        return safe_get_with_brackets(container, key, default)
