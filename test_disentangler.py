import pytest

import disentangler as mod


def test__invert_reverse_dependencies():
    dep_tree = mod.collections.OrderedDict()
    dep_tree['a'] = {'depends_on': ['b']}
    dep_tree['b'] = {'depends_on': ['c']}
    dep_tree['c'] = {'required_by': ['a']}
    dep_tree['d'] = {'depends_on': ['c'], 'required_by': ['a', 'b']}

    inst = mod.Disentangler(dep_tree)
    inst._invert_reverse_dependencies()

    expected = mod.collections.OrderedDict()
    expected['a'] = {'depends_on': ['b', 'c', 'd']}
    expected['b'] = {'depends_on': ['c', 'd']}
    expected['c'] = {}
    expected['d'] = {'depends_on': ['c']}
    assert inst._tree == expected


def test__order_nodes_simple():
    dep_tree = mod.collections.OrderedDict()
    dep_tree['a'] = {}
    dep_tree['b'] = {'depends_on': ['d', 'c']}
    dep_tree['c'] = {}
    dep_tree['d'] = {'depends_on': ['a']}

    inst = mod.Disentangler(dep_tree)
    inst._order_nodes()

    expected = mod.collections.OrderedDict()
    expected['a'] = {}
    expected['c'] = {}
    expected['d'] = {'depends_on': ['a']}
    expected['b'] = {'depends_on': ['d', 'c']}
    assert inst._tree == expected


def test__order_nodes_circular_dependency():
    dep_tree = mod.collections.OrderedDict()
    dep_tree['a'] = {}
    dep_tree['b'] = {'depends_on': ['d', 'c']}
    dep_tree['c'] = {'depends_on': ['b']}
    dep_tree['d'] = {'depends_on': ['b']}

    inst = mod.Disentangler(dep_tree)
    with pytest.raises(inst.CircularDependency):
        inst._order_nodes()


def test__order_nodes_overlapping_dependencies():
    dep_tree = mod.collections.OrderedDict()
    dep_tree['a'] = {'depends_on': ['c']}
    dep_tree['b'] = {'depends_on': ['a', 'c']}
    dep_tree['c'] = {}
    inst = mod.Disentangler(dep_tree)
    inst._order_nodes()
    assert list(inst._tree) == ['c', 'a', 'b']


def test__order_nodes_multiple_deps_when_one_is_met_already():
    dep_tree = mod.collections.OrderedDict()
    dep_tree['a'] = {'depends_on': ['b', 'c']}
    dep_tree['b'] = {'depends_on': ['c']}
    dep_tree['c'] = {}
    inst = mod.Disentangler(dep_tree)
    inst._order_nodes()
    assert list(inst._tree) == ['c', 'b', 'a']


def test__order_nodes_missing_dependency():
    dep_tree = mod.collections.OrderedDict()
    dep_tree['a'] = {'depends_on': ['b']}
    dep_tree['b'] = {'depends_on': ['invalid']}

    inst = mod.Disentangler(dep_tree)
    with pytest.raises(inst.UnresolvableDependency) as exc:
        inst._order_nodes()
        assert exc.deps == ['invalid']
        assert exc.node_id == 'b'


def test_pop_node():
    dep_tree = mod.collections.OrderedDict()
    dep_tree['a'] = {}
    dep_tree['b'] = {}
    dep_tree['c'] = {}
    inst = mod.Disentangler(dep_tree)
    inst._order_nodes()
    assert list(inst.solve()) == ['a', 'b', 'c']
    inst.pop('a')
    assert list(inst.solve()) == ['b', 'c']
    inst.pop('b')
    assert list(inst.solve()) == ['c']
    inst.pop('c')
    assert list(inst.solve()) == []


def test__required_by_all():
    dep_tree = mod.collections.OrderedDict()
    dep_tree['a'] = {}
    dep_tree['b'] = {}
    dep_tree['c'] = {'required_by': '*'}
    inst = mod.Disentangler(dep_tree)
    ret = inst.solve()
    assert list(ret) == ['c', 'a', 'b']


def test_required_by_all_multiple():
    dep_tree = mod.collections.OrderedDict()
    dep_tree['a'] = {}
    dep_tree['b'] = {'required_by': '*'}
    dep_tree['c'] = {'required_by': '*'}
    inst = mod.Disentangler(dep_tree)
    ret = inst.solve()
    assert list(ret) == ['c', 'b', 'a']


def test_depends_on_all():
    dep_tree = mod.collections.OrderedDict()
    dep_tree['a'] = {'depends_on': '*'}
    dep_tree['b'] = {}
    dep_tree['c'] = {}
    inst = mod.Disentangler(dep_tree)
    ret = inst.solve()
    assert list(ret) == ['b', 'c', 'a']


def test_depends_on_all_multiple():
    dep_tree = mod.collections.OrderedDict()
    dep_tree['a'] = {'depends_on': '*'}
    dep_tree['b'] = {'depends_on': '*'}
    dep_tree['c'] = {}
    inst = mod.Disentangler(dep_tree)
    ret = inst.solve()
    assert list(ret) == ['c', 'a', 'b']
