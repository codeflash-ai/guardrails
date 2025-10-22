import inspect
import json
import sys
from dataclasses import InitVar, asdict, dataclass, field, is_dataclass
from json import JSONEncoder
from typing import Any, Dict

from pydash.strings import snake_case


def get_annotations(obj):
    if sys.version_info.minor >= 10 and hasattr(inspect, "get_annotations"):
        return inspect.get_annotations(obj)  # type: ignore
    else:
        return obj.__annotations__


class SerializeableJSONEncoder(JSONEncoder):
    def default(self, o):
        if is_dataclass(o):
            return asdict(o)
        return super().default(o)


encoder_kwargs = {}
if sys.version_info.minor >= 10:
    encoder_kwargs["kw_only"] = True
    encoder_kwargs["default"] = SerializeableJSONEncoder


@dataclass
class Serializeable:
    encoder: InitVar[JSONEncoder] = field(**encoder_kwargs)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        annotations = get_annotations(cls)
        # Convert the keys of annotations dict to a set for faster lookup
        attributes = set(annotations)
        # Precompute snake_case for each input key, avoid repeated computation in the comprehension
        sc_data = {snake_case(k): v for k, v in data.items()}
        # Only keep those that are present in attributes
        snake_case_kwargs = {k: v for k, v in sc_data.items() if k in attributes}
        # Use setdefault to avoid recomputing key and ensure compatible default
        snake_case_kwargs.setdefault("encoder", SerializeableJSONEncoder)
        return cls(**snake_case_kwargs)  # type: ignore

    @property
    def __dict__(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self):
        return json.dumps(self, cls=self.encoder)  # type: ignore
