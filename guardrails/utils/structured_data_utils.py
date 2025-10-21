from typing import List, Optional
from guardrails.logger import logger
from guardrails.classes.schema.processed_schema import ProcessedSchema
from guardrails.types.pydantic import ModelOrListOfModels


# takes processed schema and converts it to a openai tool object
def schema_to_tool(schema) -> dict:
    tool = {
        "type": "function",
        "function": {
            "name": "gd_response_tool",
            "description": "A tool for generating responses to guardrails."
            " It must be called last in every response.",
            "parameters": schema,
            "required": schema["required"] or [],
        },
    }
    return tool


def set_additional_properties_false_iteratively(schema):
    # To minimize repeated type checks and dict lookups,
    # compress logic and use local variables.
    stack = [schema]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            keys = current.keys()
            # Use a local ref for quick lookup
            if "properties" in keys:
                current["required"] = list(current["properties"].keys())
            # Gather which props to drop in one go for small dicts
            # Avoid multiple separate passes for the same keys.
            drop_props = []
            if "maximum" in keys:
                logger.warn("Property maximum is not supported. Dropping")
                drop_props.append("maximum")
            if "minimum" in keys:
                logger.warn("Property maximum is not supported. Dropping")
                drop_props.append("minimum")
            if "default" in keys:
                logger.warn("Property default is not supported. Marking field Required")
                drop_props.append("default")
            for prop in drop_props:
                current.pop(prop)
            # Avoid recomputing .values() inside the loop; use list() to prevent mutation during iteration.
            values = list(current.values())
            stack.extend(values)
            # The following conditional does not need deeper nesting.
            if (
                "additionalProperties" not in keys
                and "type" in keys
                and current["type"] == "object"
            ):
                current["additionalProperties"] = False  # the api needs these set
        elif isinstance(current, list):
            # Use extend instead of repeated append for better perf.
            stack.extend(current)


def json_function_calling_tool(
    schema: ProcessedSchema,
    tools: Optional[List] = None,
) -> List:
    tools = tools or []
    tools.append(schema_to_tool(schema))  # type: ignore
    return tools


def output_format_json_schema(schema: ModelOrListOfModels) -> dict:
    parsed_schema = schema.model_json_schema()  # type: ignore

    set_additional_properties_false_iteratively(parsed_schema)

    return {
        "type": "json_schema",
        "json_schema": {
            "name": parsed_schema["title"],
            "schema": parsed_schema,
            "strict": True,
        },  # type: ignore
    }
