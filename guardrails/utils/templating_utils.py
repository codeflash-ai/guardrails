from string import Template
from typing import List


def get_template_variables(template: str) -> List[str]:
    if hasattr(Template, "get_identifiers"):
        return Template(template).get_identifiers()  # type: ignore
    else:
        pattern = Template.pattern
        variables = []
        seen = set()
        for m in pattern.finditer(template):
            named = m.group("named") or m.group("braced")
            if named is not None and named not in seen:
                variables.append(named)
                seen.add(named)
        return variables
