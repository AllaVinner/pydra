"""
# super union model


"""

from typing import Any, ClassVar, Literal, Union, get_args, get_origin

from pydantic import BaseModel, GetCoreSchemaHandler
from pydantic.json_schema import model_json_schema
from pydantic_core import CoreSchema, core_schema


def _is_pydantic_model(typ: Any) -> bool:
    try:
        return issubclass(typ, BaseModel)
    except TypeError:
        return False


def _modify_field_type(typ: Any) -> Any:
    # origin[*args] - E.g. dict[str, str]
    origin = get_origin(typ)
    args = get_args(typ)

    if _is_pydantic_model(typ):
        return Union[typ, str]
    elif origin is list and args:
        modified = _modify_field_type(args[0])
        return list[Union[modified, str]]
    elif origin is dict and args:
        key_type, value_type = args
        modified_value = _modify_field_type(value_type)
        return dict[key_type, Union[modified_value, str]]
    elif origin in {Union, tuple}:
        return Union[tuple(_modify_field_type(arg) for arg in args)]
    return typ

def create_config_json_schema(cls) -> dict[str, Any]:
        modified_annotations = {}

        for name, field in cls.__annotations__.items():
            modified_annotations[name] = _modify_field_type(field)

        dynamic_cls = type(
            f"{cls.__name__}WithStrUnion",
            (BaseModel,),
            {"__annotations__": modified_annotations},
        )

        return model_json_schema(dynamic_cls)


class SuperUnionModel(BaseModel):
    _super_union_base_name: ClassVar[Literal["SuperUnionModel"]] = "SuperUnionModel"
    _super_union_discriminator: ClassVar[Literal["class_name"]] = "class_name"
    class_name: str

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: type[BaseModel], handler: GetCoreSchemaHandler, /
    ) -> CoreSchema:
        mros = cls.mro()
        if len(mros) < 2:
            return handler(source)
        next_super = mros[1]  # Next Super Class - 0 is it self
        if next_super.__name__ != cls._super_union_base_name:
            return handler(source)
        # TODO: Add cls if not abstract class
        subclasses = cls.__subclasses__()
        schemas = {
            sub.model_fields[cls._super_union_discriminator].default: handler.generate_schema(sub)
            for sub in subclasses
        }
        return core_schema.tagged_union_schema(schemas, discriminator=cls._super_union_discriminator)

