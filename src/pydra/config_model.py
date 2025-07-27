from copy import deepcopy
from typing import (
    Any,
    cast,
    get_args,
    get_origin,
)

from pydantic import BaseModel, Field
from pydantic.main import create_model


class Ref(BaseModel):
    ref: str = Field(..., alias="$ref")


def create_ref_type(model: type) -> type:
    return cast(type, model | Ref)


def create_ref_config_model(model: type, cache: dict | None = None) -> type:
    if cache is None:
        cache = dict()
    if not issubclass(model, BaseModel):
        origin = get_origin(model)
        if origin is None:
            return model
        args = [create_ref_config_model(a, cache=cache) for a in get_args(model)]
        return origin[*args]
    fields: dict[str, Any] = dict()
    for name, info in model.model_fields.items():
        assert info.annotation is not None
        config_type = create_ref_config_model(info.annotation, cache=cache)
        fields[name] = (config_type, deepcopy(info))
    config_model = create_model(model.__name__, **fields)
    cache[model] = config_model
    return create_ref_type(config_model)


def create_components_model(classes: dict[type[BaseModel], type[BaseModel]]):
    fields: dict[str, Any] = {}
    for m, m_config in classes.items():
        field_type = dict[str, m_config]  #  type: ignore
        fields[m.__name__] = (field_type, Field(default_factory=lambda: dict()))
    components = create_model("Components", **fields)
    return components


def create_config_model(model: type[BaseModel]) -> type[BaseModel]:
    config_models: dict[type[BaseModel], type[BaseModel]] = dict()
    config_model = create_ref_config_model(model, cache=config_models)
    components = create_components_model(config_models)
    return create_model(
        "Model",
        components=(components, Field(default_factory=components)),
        model=config_model,
    )


def join_dict_lists(d1, d2):
    for k, v in d2.items():
        if k not in d1.keys():
            d1[k] = []
        d1[k].extend(v)
    return d1


def gather_refs(d: dict[str, Any], current_path: list[str]) -> dict[str, list[str]]:
    refs: dict[str, list[str]] = dict()
    if isinstance(d, dict):
        for k, v in d.items():
            if k == "$ref":
                if v not in refs.keys():
                    refs[v] = []
                refs[v].append("/".join(current_path))
            else:
                refs = join_dict_lists(
                    refs, gather_refs(v, current_path=current_path + [k])
                )
    if isinstance(d, list):
        for i, v in enumerate(d):
            refs = join_dict_lists(
                refs, gather_refs(v, current_path=current_path + [str(i)])
            )
    return refs


def expand_ref(source: str, target: str, config: dict):
    source_segments = source.split("/")
    if source_segments[0] == "#":
        source_segments = source_segments[1:]
    if len(source_segments) == 1:
        source_parent = config
    else:
        source_parent = config[source_segments[0]]
        for s in source_segments[1:-1]:
            source_parent = source_parent[s]

    target_segments = target.split("/")
    if target_segments[0] == "#":
        target_segments = target_segments[1:]
    if len(target_segments) == 1:
        target_parent = config
    else:
        target_parent = config[target_segments[0]]
        for s in target_segments[1:-1]:
            target_parent = target_parent[s]
    source_parent[source_segments[-1]] = target_parent[target_segments[-1]]
    return config


def expand_refs(config: dict[str, Any]):
    rev_refs = gather_refs(config, ["#"])
    ref_targets = list(rev_refs.keys())
    ref_targets.sort(reverse=True)
    for ref_target in ref_targets:
        ref_sources = rev_refs[ref_target]
        for ref_source in ref_sources:
            print(ref_source)
            config = expand_ref(ref_source, ref_target, config)
    return config
