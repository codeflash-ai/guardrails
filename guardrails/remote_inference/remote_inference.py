from typing import Optional
from guardrails.classes.rc import RC


# TODO: Consolidate with telemetry switches
def get_use_remote_inference(rc: RC) -> Optional[bool]:
    """Load the use_remote_inferencing setting from the rc file.

    Args:
        rc (RC): The rc settings.

    Returns:
        Optional[bool]: The use_remote_inferencing setting, or None if not found.
    """
    use_remote_inferencing = getattr(rc, "use_remote_inferencing", None)
    if isinstance(use_remote_inferencing, bool):
        return use_remote_inferencing
    elif isinstance(use_remote_inferencing, str):
        return use_remote_inferencing.lower() == "true"
    else:
        return None
