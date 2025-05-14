import typing
from typing import Any, Dict, List, Set, Tuple, TypeAlias, Union

from pydantic import BaseModel, Field
from pydantic.main import create_model


class Ref(BaseModel):
    ref: str = Field(..., alias="$ref")


def get_sub_models(model: TypeAlias[BaseModel]) -> Set[TypeAlias[BaseModel]]:
    def recurse(m: TypeAlias[BaseModel], seen_models: Set[TypeAlias[BaseModel]]):
        for field in m.model_fields.values():
            field_type: type[Any] | None = field.annotation
            types_to_check = {field_type}
            origin = typing.get_origin(field_type)  # list[X] -> list
            if origin in (list, set, tuple, dict, Union):
                types_to_check.update(typing.get_args(field_type))

            for typ in types_to_check:
                if (
                    isinstance(typ, type)
                    and issubclass(typ, BaseModel)
                    and typ is not m
                    and typ not in seen
                ):
                    seen_models.add(typ)
                    recurse(typ, seen_models)

    seen: set[TypeAlias[BaseModel]] = set()
    recurse(model, seen)
    return {s for s in seen if s != Ref}


def create_config_type(model_type: TypeAlias[BaseModel]) -> TypeAlias[BaseModel]:
    wrapped_model_type: TypeAlias = Union[model_type, Ref]  # noqa: F821
    sub_models = get_sub_models(model_type) | {model_type}
    components = create_model(
        "Components",
        field_definitions={m.__name__: (dict[str, m], Field(default_factory=dict)) for m in sub_models},
    )

    # TODO: make this more generic
    # TODO: Add super class, that validates refs, or add that to Ref class with context ...
    config = create_model(
        f"{model_type.__name__}Config",
        components=(components, Field(default_factory=dict)),
        model=wrapped_model_type,
    )
    return config


def replace_submodels_with_ref_union(model: TypeAlias[BaseModel]) -> TypeAlias[BaseModel]:
    cache: Dict[TypeAlias[BaseModel], TypeAlias[BaseModel]] = {}

    def process_model(m: TypeAlias[BaseModel]) -> TypeAlias[BaseModel]:
        if m in cache:
            return cache[m]

        fields: Dict[str, Tuple[Any, Any]] = {}
        for name, field in m.model_fields.items():
            orig_type = field.annotation
            new_type = wrap_type(orig_type)
            fields[name] = (new_type, field.default if not field.is_required else ...)

        new_model = create_model(m.__name__, field_definitions=fields)
        cache[m] = new_model
        return new_model

    def wrap_type(tp: Any) -> Any:
        origin = typing.get_origin(tp)
        args = typing.get_args(tp)
        if isinstance(tp, type) and issubclass(tp, BaseModel):
            return Union[process_model(tp), Ref]
        elif origin is Union:
            # TODO: Add ref?
            return Union[tuple(wrap_type(arg) for arg in args)]
        # TODO: Make an extensive origin list
        elif origin in (list, List, tuple, Tuple, set, Set):
            return origin[tuple(wrap_type(arg) for arg in args)]
        elif origin is dict or origin is Dict:
            key_type, val_type = args
            return Dict[wrap_type(key_type), wrap_type(val_type)]
        else:
            return tp

    return process_model(model)


def create_config_model(model: TypeAlias[BaseModel]) -> TypeAlias[BaseModel]:
    model_with_refs = replace_submodels_with_ref_union(model)
    config_model = create_config_type(model_with_refs)
    return config_model


class ConfigModel:
    model: TypeAlias[BaseModel]

    def __init__(self, model: TypeAlias[BaseModel]):
        self.model = model
        self.config_model: TypeAlias[BaseModel] = create_config_model(self.model)
