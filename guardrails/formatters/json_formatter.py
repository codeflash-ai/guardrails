import json
from typing import Dict, List, Optional, Union

from guardrails.formatters.base_formatter import BaseFormatter
from guardrails.llm_providers import (
    ArbitraryCallable,
    HuggingFacePipelineCallable,
    HuggingFaceModelCallable,
)


def _deref_schema_path(schema: dict, path: Union[list, str]):
    """Given a path like #/$defs/foo/bar/bez, nagivates into a JSONSchema dict
    and pulls the respective sub-object."""
    if isinstance(path, str):
        path = path.split("/")
    idx = 0
    plen = len(path)
    # Unroll the recursion into a loop for performance
    while idx < plen:
        key = path[idx]
        if key == "#":
            # The '#' indicates the root of the chain, so this is a first call.
            # If we're at the root we want to make sure we have our '$defs'.
            assert "$defs" in schema
            idx += 1
            continue
        schema = schema[key]
        idx += 1
    return schema


def _jsonschema_to_jsonformer(
    schema: dict, path: Optional[list] = None, objdefs: Optional[dict] = None
) -> dict:
    """Converts the large-ish JSONSchema standard into the JSONFormer schema
    format.

    These are mostly identical, but the jsonschema supports '$defs' and
    '$ref'. There's an additional inconsistency in the use 'integer'
    versus 'number'.
    """
    # TODO: Can we use jsonref to replace references, since it's a dependency anyway?
    if path is None:
        path = []
    if objdefs is None:
        objdefs = {"$defs": dict()}

    # We may get something we don't expect...
    if not isinstance(schema, dict):
        raise Exception(
            f"Error: could not convert/parse base schema. Encountered `{schema}`"
        )

    if "$defs" in schema:
        # We have some sub-schemas defined here.  We need to convert them.
        # We may also need to handle sub-schema defs.
        # For now, build a quick tree in the defs.
        current = objdefs["$defs"]
        # Use for loop with early binding for step for efficiency
        for step in path:
            current = current.setdefault(step, {})
        current.update(schema["$defs"])

    result = {}
    # Avoid .items() when possible - but we need keys and values here.
    # Prebind locals for small performance benefit
    schema_items = schema.items()
    result_type = None
    for k, v in schema_items:
        if k == "type" and v == "integer":
            result["type"] = "number"
        elif k == "type" and v == "object":
            result["type"] = "object"
            # Use local reference to properties dict
            props = schema["properties"]
            result_props = result["properties"] = {}
            for subkey, subvalue in props.items():  # Must be present.
                path.append(subkey)
                result_props[subkey] = _jsonschema_to_jsonformer(
                    subvalue,
                    path,
                    objdefs,
                )
                assert path.pop() == subkey
        elif k == "type" and v == "array":
            result["type"] = "array"
            result["items"] = _jsonschema_to_jsonformer(schema["items"], path, objdefs)
        elif k == "$ref":
            result = _jsonschema_to_jsonformer(
                _deref_schema_path(objdefs, v), path, objdefs
            )
            # Short-circuit after reference resolution
            break
        else:
            result[k] = v
    return result


class JsonFormatter(BaseFormatter):
    """A formatter that uses Jsonformer to ensure the shape of structured data
    for Hugging Face models."""

    def __init__(self, schema: dict):
        self.output_schema = _jsonschema_to_jsonformer(schema)

    def wrap_callable(self, llm_callable) -> ArbitraryCallable:
        # JSON Schema enforcement experiment.
        from jsonformer import Jsonformer

        if isinstance(llm_callable, HuggingFacePipelineCallable):
            model = llm_callable.init_kwargs["pipeline"]

            def fn(
                *args,
                messages: Optional[List[Dict[str, str]]] = None,
                **kwargs,
            ) -> str:
                prompt = ""
                for msg in messages:  # type: ignore
                    prompt += msg["content"]

                return json.dumps(
                    Jsonformer(
                        model=model.model,
                        tokenizer=model.tokenizer,
                        json_schema=self.output_schema,
                        prompt=prompt,
                    )()
                )

            return ArbitraryCallable(fn)
        elif isinstance(llm_callable, HuggingFaceModelCallable):
            # This will not work because 'model_generate' is the .gen method.
            # model = self.api.init_kwargs["model_generate"]
            # Use the __self__ to grab the base mode for passing into JF.
            model = llm_callable.init_kwargs["model_generate"].__self__
            tokenizer = llm_callable.init_kwargs["tokenizer"]

            def fn(
                *args,
                messages: Optional[List[Dict[str, str]]] = None,
                **kwargs,
            ) -> str:
                prompt = ""
                for msg in messages:  # type: ignore
                    prompt += msg["content"]

                return json.dumps(
                    Jsonformer(
                        model=model,
                        tokenizer=tokenizer,
                        json_schema=self.output_schema,
                        prompt=prompt,
                    )()
                )

            return ArbitraryCallable(fn)
        else:
            raise ValueError(
                "JsonFormatter can only be used with HuggingFace*Callable."
            )
