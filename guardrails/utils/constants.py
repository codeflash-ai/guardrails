import re
from guardrails.classes.templating.constants_container import ConstantsContainer
from guardrails.classes.templating.namespace_template import NamespaceTemplate

_GR_REGEX = re.compile(r"\${gr\.(\w+)}")

# TODO: Move this to guardrails/constants/__init__.py
# Singleton instance created on import/init
constants = ConstantsContainer()


# TODO: Consolidate this and guardrails/utils/prompt_utils.py
#       into guardrails/utils/templating_utils.py
def substitute_constants(text):
    """Substitute constants in the prompt."""
    # Substitute constants by reading the constants file.
    # Regex to extract all occurrences of ${gr.<constant_name>}
    matches = _GR_REGEX.findall(text)

    if not matches:
        return text

    # Only rebuild the template if necessary, and substitute all in one pass
    # If duplicate names, set semantics are fine (safe_substitute will handle redundancy)
    mapping = {f"gr.{key}": constants[key] for key in set(matches)}
    template = NamespaceTemplate(text)
    return template.safe_substitute(**mapping)
