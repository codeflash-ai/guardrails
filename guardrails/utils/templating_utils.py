import re
from string import Template
from typing import List

_TEMPLATE_IDENTIFIER_RE = re.compile(r"\$\{([\w]+)\}|\$([a-zA-Z_][\w]*)")


def get_template_variables(template: str) -> List[str]:
    if hasattr(Template, "get_identifiers"):
        return Template(template).get_identifiers()  # type: ignore
    # Direct regex extraction for all $identifier and ${identifier} (per string.Template spec)
    # This avoids creating a Template and substituting, improving performance.
    # Each match may have either group 1 or group 2 set
    matches = _TEMPLATE_IDENTIFIER_RE.findall(template)
    return list({m[0] or m[1] for m in matches})
