from datetime import datetime

from pytest_mock_experiments import MockerFixture


dt = datetime(2021, 2, 2)
dt_additional_ref = dt


def _get_dt():
    return dt, dt_additional_ref


def test_patch_method__class_method(mocker: MockerFixture):
    class Foo:
        def bar(self):
            return 'bar'

    assert Foo().bar() == 'bar'

    mock = mocker.patch.method(Foo.bar, return_value=42)

    assert Foo().bar() == 42
    assert mock.call_count == 1


def test_patch_method__instance_method(mocker: MockerFixture):
    class Foo:
        def bar(self):
            return 'bar'

    foo1 = Foo()
    assert foo1.bar() == 'bar'
    foo2 = Foo()
    assert foo2.bar() == 'bar'

    mock = mocker.patch.method(foo1.bar, return_value=42)

    assert foo1.bar() == 42
    assert foo2.bar() == 'bar'
    foo3 = Foo()
    assert foo3.bar() == 'bar'
    assert mock.call_count == 1


def test_patch_refs(mocker: MockerFixture):
    class ClassWithSlots:
        __slots__ = ('dt',)

    instance_with_slots = ClassWithSlots()
    instance_with_slots.dt = dt

    mocker.patch.refs(dt, new=datetime(2021, 5, 6))
    assert dt == datetime(2021, 5, 6)
    assert _get_dt() == (datetime(2021, 5, 6), datetime(2021, 5, 6))
    assert instance_with_slots.dt == datetime(2021, 5, 6)


def test_patch_refs__undone():
    assert dt == datetime(2021, 2, 2)
