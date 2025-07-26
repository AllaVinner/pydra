from copy import deepcopy
from typing import (
    Any,
    TypeAlias,
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
