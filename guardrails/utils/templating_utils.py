import re
from string import Template
from typing import List


def get_template_variables(template: str) -> List[str]:
    if hasattr(Template, "get_identifiers"):
        return Template(template).get_identifiers()  # type: ignore
    else:
        pattern = r"\$\{([_a-zA-Z][_a-zA-Z0-9]*)\}|\$([_a-zA-Z][_a-zA-Z0-9]*)"
        matches = re.findall(pattern, template)
        variables = []
        seen = set()
        for a, b in matches:
            var = a or b
            if var and var not in seen:
                seen.add(var)
                variables.append(var)
        return variables
