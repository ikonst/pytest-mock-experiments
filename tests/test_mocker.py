from datetime import datetime

from pytest_mock_experiments import MockerFixture


dt = datetime(2000, 1, 1)
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


def test_patch_refs__datetime(mocker: MockerFixture):
    class ClassWithSlots:
        __slots__ = ('dt',)

        dt: datetime

    instance_with_slots = ClassWithSlots()
    instance_with_slots.dt = dt

    new_dt = datetime(2021, 11, 12)
    mocker.patch.refs(dt, new=new_dt)
    assert dt == new_dt
    assert _get_dt() == (new_dt, new_dt)
    assert instance_with_slots.dt == new_dt


def test_patch_refs__datetime__undone():
    assert dt == datetime(2000, 1, 1)


def test_patch_refs__module_function(mocker: MockerFixture):
    from . import module1
    from . import module2

    assert module1.module_func() == 42
    assert module2.rose_by_any_other_name() == 42
    assert module2.calls_module_func() == 42

    mocker.patch.refs(module1.module_func, return_value='foo')

    assert module1.module_func() == 'foo'
    assert module2.rose_by_any_other_name() == 'foo'
    assert module2.calls_module_func() == 'foo'
