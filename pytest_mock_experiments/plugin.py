import gc
import types
import unittest.mock
from typing import Any
from typing import Callable
from typing import Generator
from typing import Optional
from typing import TYPE_CHECKING

import pytest
import pytest_mock


def _class_holding(fn: Callable) -> Optional[type]:  # see https://stackoverflow.com/a/65756960
    for possible_dict in gc.get_referrers(fn):
        if not isinstance(possible_dict, dict):
            continue
        for possible_class in gc.get_referrers(possible_dict):
            if isinstance(possible_class, type) and getattr(possible_class, fn.__name__, None) is fn:
                return possible_class
    return None


class _slot_attr_patcher:
    def __init__(self, target: object, attr_name: str, old_value: Any, new_value: Any) -> None:
        self.target = target
        self.attr_name = attr_name
        self.old_value = old_value
        self.new_value = new_value

    def start(self) -> None:
        setattr(self.target, self.attr_name, self.new_value)

    def stop(self) -> None:
        setattr(self.target, self.attr_name, self.old_value)


class MockerFixture(pytest_mock.MockerFixture):
    patch: 'MockerFixture._Patcher'

    class _Patcher(pytest_mock.MockerFixture._Patcher):
        if TYPE_CHECKING:

            def method(
                self,
                method: Callable,
                new: object = ...,
                spec: Optional[object] = ...,
                create: bool = ...,
                spec_set: Optional[object] = ...,
                autospec: Optional[object] = ...,
                new_callable: object = ...,
                **kwargs: Any,
            ) -> unittest.mock.MagicMock:
                ...

        else:

            def method(
                self,
                method: Callable,
                *args: Any,
                **kwargs: Any,
            ) -> unittest.mock.MagicMock:
                """
                Enables patching bound methods:

                  -patch.object(my_instance, 'my_method')
                  +patch.method(my_instance.my_method)

                and unbound methods:

                  -patch.object(MyClass, 'my_method')
                  +patch.method(MyClass.my_method)

                by passing a reference (not stringy paths!), allowing for easier IDE navigation and refactoring.
                """
                if isinstance(method, types.MethodType):  # handle bound methods
                    return self.object(method.__self__, method.__name__, *args, **kwargs)
                elif isinstance(method, types.FunctionType):  # handle unbound methods
                    cls = _class_holding(method)
                    if cls is None:
                        raise ValueError(
                            f"Could not determine class for {method}: if it's not an unbound method "
                            f'but a function, consider patch.refs or patch.object.'
                        )
                    return self.object(cls, method.__name__, *args, **kwargs)
                else:
                    raise ValueError(f"{method} doesn't look like a method")

        if TYPE_CHECKING:

            def refs(
                    self,
                    obj: object,
                    new: object = ...,
                    spec: Optional[object] = ...,
                    create: bool = ...,
                    spec_set: Optional[object] = ...,
                    autospec: Optional[object] = ...,
                    new_callable: object = ...,
                    **kwargs: Any,
            ) -> unittest.mock.MagicMock:
                ...

        else:

            def refs(self, obj: object, *args: Any, **kwargs: Any) -> unittest.mock.MagicMock:
                if isinstance(obj, types.MethodType):
                    # bound methods are somehow special since they're not turned up by gc.get_referrers :O
                    mock = self.object(obj.__self__, obj.__name__, *args, **kwargs)
                else:
                    # we want to use unittest.mock._patch w/o patching anything just yet
                    class DummyType: dummy_attr = obj

                    mock = self.object(DummyType, 'dummy_attr', *args, **kwargs)

                for ref in gc.get_referrers(obj):
                    if ref is locals():
                        continue  # don't patch our own locals!
                    if type(ref) is dict:
                        self.dict(ref, {k: mock for k, v in ref.items() if v is obj})
                    else:
                        for attr_name in getattr(type(ref), '__slots__', []):
                            attr_value = getattr(ref, attr_name)
                            if attr_value is obj:
                                self._start_patch(_slot_attr_patcher, False, ref, attr_name, attr_value, mock)

                    # we don't handle references in lists or other data types yet

                return mock


@pytest.fixture
def mocker(pytestconfig: Any) -> Generator[MockerFixture, None, None]:
    """
    Extends the pytest_mock 'mocker' fixture with additional methods:

    def test_foo(mocker):
       mocker.patch.method(...)
       mocker.patch.refs(...)
    """
    result = MockerFixture(pytestconfig)
    yield result
    result.stopall()
