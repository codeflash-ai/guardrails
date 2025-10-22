from string import Template
from typing import List
import re

_TEMPLATE_VAR_PATTERN = re.compile(r"\${([_a-zA-Z][_a-zA-Z0-9]*)}")


def get_template_variables(template: str) -> List[str]:
    # If Template provides identifiers, use that (backward-compatible)
    if hasattr(Template, "get_identifiers"):
        return Template(template).get_identifiers()  # type: ignore
    # Fast regex extraction for variable names in the template string
    return list({match.group(1) for match in _TEMPLATE_VAR_PATTERN.finditer(template)})
