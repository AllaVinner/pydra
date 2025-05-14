import pytest
from pydantic import BaseModel, ValidationError

from pydra.config_model import ConfigModel


def test_basic_config_model():
    class A(BaseModel):
        x: int

    config = ConfigModel(model=A)
    config_model = config.config_model

    dct = {"model": {"x": 12}}
    assert config_model.model_validate(dct)
    dct["components"] = {}
    assert config_model.model_validate(dct)
    dct["components"]["A"] = {}
    assert config_model.model_validate(dct)
    dct["components"]["A"]["simple"] = {"x": 11}
    assert config_model.model_validate(dct)
    dct["model"] = {"$ref": "#/components/A/simple"}
    m = config_model.model_validate(dct)
    assert m.model.ref == "#/components/A/simple"


def test_basic_config_model_exceptions():
    class A(BaseModel):
        x: int

    config = ConfigModel(model=A)
    config_model = config.config_model

    dct = {}
    with pytest.raises(ValidationError):
        config_model.model_validate(dct)
    dct = {"model": {}}
    with pytest.raises(ValidationError):
        config_model.model_validate(dct)
    dct = {"model": {"x": "asd"}}
    with pytest.raises(ValidationError):
        config_model.model_validate(dct)
    # TODO: Fix why this isn't complaining ...
    dct = {"model": {"x": 123}, "components": {"A": {"a": "asdf"}}}
    with pytest.raises(ValidationError):
        config_model.model_validate(dct)


def test_nested_config_model():
    class C(BaseModel):
        x: int

    class B(BaseModel):
        c: C

    class A(BaseModel):
        b: B

    config = ConfigModel(model=A)
    config_model = config.config_model

    dct = {
        "components": {
            "A": {
                "full": {"b": {"c": {"x": 1}}},
                "with-ref": {"b": {"$ref": "#/components/B/full"}},
            },
            "B": {"full": {"c": {"x": 2}}},
        },
        "model": {"$ref": "#/components/A/full"},
    }
    assert config_model.model_validate(dct)
    dct["components"]["A"]["full"]["b"]["c"]["x"] = "a"
    with pytest.raises(ValidationError):
        config_model.model_validate(dct)
    dct["components"]["A"]["full"]["b"]["c"]["x"] = 1
    del dct["components"]["A"]["with-ref"]["b"]["$ref"]
    with pytest.raises(ValidationError):
        config_model.model_validate(dct)
