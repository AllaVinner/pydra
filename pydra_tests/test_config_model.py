import pytest
from pydantic import BaseModel, ValidationError

from pydra.config_model import create_config_model, expand_refs


def test_basic_config_model():
    class A(BaseModel):
        x: int

    config_model = create_config_model(model=A)

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

    config_model = create_config_model(model=A)

    dct = {}
    with pytest.raises(ValidationError):
        config_model.model_validate(dct)
    dct = {"model": {}}
    with pytest.raises(ValidationError):
        config_model.model_validate(dct)
    dct = {"model": {"x": "asd"}}
    with pytest.raises(ValidationError):
        config_model.model_validate(dct)
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

    config_model = create_config_model(model=A)

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


def test_expand_refs():
    d = {"a": {"b": 1}, "b": {"$ref": "#/a/b"}}
    expected_unpacked = {"a": {"b": 1}, "b": 1}
    actual_unpacked = expand_refs(d)
    assert actual_unpacked == expected_unpacked

    d = {"aa": {"a": {"b": 1}}, "bb": {"b": {"$ref": "#/aa/a/b"}}}
    expected_unpacked = {"aa": {"a": {"b": 1}}, "bb": {"b": 1}}
    actual_unpacked = expand_refs(d)
    assert actual_unpacked == expected_unpacked

    d = {
        "a": {"b": {"c": {"d": {"$ref": "#/q/w"}}}},
        "x": {"y": {"$ref": "#/a/b"}},
        "q": {"w": {"s": {"p": 999}}},
    }
    expected_unpacked = {
        "a": {"b": {"c": {"d": {"s": {"p": 999}}}}},
        "x": {"y": {"c": {"d": {"s": {"p": 999}}}}},
        "q": {"w": {"s": {"p": 999}}},
    }
    actual_unpacked = expand_refs(d)
    assert actual_unpacked == expected_unpacked
