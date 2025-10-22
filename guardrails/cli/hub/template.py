import json
import os

from guardrails.cli.server.hub_client import get_guard_template


def get_template(template_name: str) -> tuple[dict, str]:
    # if template ends in .json load file from disk relative to the execution directory
    if template_name.endswith(".json"):
        template_file_name = template_name
        try:
            file_path = os.path.abspath(template_name)
            with open(file_path, "r", encoding="utf-8") as fin:
                return json.load(fin), template_file_name
        except FileNotFoundError:
            raise FileNotFoundError(f"Template file {template_name} not found.")

    name_split = template_name.split("/")
    template_file_base = name_split[-1]
    template_file_name = f"{template_file_base}.json"

    template = get_guard_template(template_name)

    # write template to file
    out_path = os.path.abspath(template_file_name)
    with open(out_path, "w", encoding="utf-8") as file_out:
        json.dump(template, file_out, indent=4)

    return template, template_file_name
