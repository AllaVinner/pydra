from abc import ABC, abstractmethod
from typing import Literal

from pydantic import BaseModel

from pydra.super_union_model import SuperUnionModel


def test_super_union():
    class SuperModel(SuperUnionModel, ABC):
        base_var: int

        @abstractmethod
        def fun(self) -> int: ...

    class ModelA(SuperModel):
        a_var: int
        class_name: Literal["ModelA"] = "ModelA"

        def fun(self) -> int:
            return 1

    class ModelB(SuperModel):
        b_var: str
        class_name: Literal["ModelB"] = "ModelB"

        def fun(self) -> int:
            return 2

    class Root(BaseModel):
        model: SuperModel

    exptected_root = Root(model=ModelA(base_var=0, a_var=2))
    expected_dict = {"model": {"class_name": "ModelA", "a_var": 2, "base_var": 0}}
    assert Root.model_validate(expected_dict) == exptected_root
    assert exptected_root.model_dump() == expected_dict

    exptected_root = Root(model=ModelB(base_var=0, b_var="b"))
    expected_dict = {"model": {"class_name": "ModelB", "b_var": "b", "base_var": 0}}
    assert Root.model_validate(expected_dict) == exptected_root
    assert exptected_root.model_dump() == expected_dict

    schema = Root.model_json_schema()
    assert "ModelA" in schema["$defs"]
    assert "ModelB" in schema["$defs"]
    assert "SuperModel" not in schema["$defs"]
