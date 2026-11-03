"""Scene graph and input behaviour."""

from __future__ import annotations

import pytest

import py3dgame as p3d


# -- scene graph ------------------------------------------------------- #

def test_node_names_are_validated():
    with pytest.raises(p3d.SceneError):
        p3d.Node("")
    with pytest.raises(p3d.SceneError):
        p3d.Scene("  ")


def test_add_remove_and_parent_links():
    parent = p3d.Node("parent")
    child = p3d.Node("child")
    parent.add(child)
    assert child.parent is parent
    assert parent.children == [child]
    assert parent.remove(child) is True
    assert child.parent is None
    assert parent.remove(child) is False


def test_reparenting_moves_the_node():
    a, b, child = p3d.Node("a"), p3d.Node("b"), p3d.Node("child")
    a.add(child)
    b.add(child)
    assert child.parent is b
    assert child not in a.children


def test_cycles_are_refused():
    a, b = p3d.Node("a"), p3d.Node("b")
    a.add(b)
    with pytest.raises(p3d.SceneError):
        b.add(a)
    with pytest.raises(p3d.SceneError):
        a.add(a)


def test_find_and_walk_order():
    root = p3d.Node("root")
    first = root.add(p3d.Node("first"))
    second = root.add(p3d.Node("second"))
    first.add(p3d.Node("deep"))
    names = [node.name for node in root.walk()]
    assert names == ["root", "first", "deep", "second"]
    assert root.find("deep").name == "deep"
    assert root.find("missing") is None
    assert second.parent is root


def test_world_positions_compose_through_parents():
    parent = p3d.Node("parent", position=p3d.Vec3(10, 0, 0))
    child = p3d.Node("child", position=p3d.Vec3(0, 5, 0))
    parent.add(child)
    assert child.world_position() == p3d.Vec3(10, 5, 0)


def test_parent_rotation_affects_child_world_position():
    parent = p3d.Node("parent")
    parent.transform.rotation = p3d.Vec3(0, 0, 90)
    child = p3d.Node("child", position=p3d.Vec3(1, 0, 0))
    parent.add(child)
    world = child.world_position()
    assert world.x == pytest.approx(0, abs=1e-9)
    assert world.y == pytest.approx(1, abs=1e-9)


def test_update_visits_parent_before_children():
    order = []
    scene = p3d.Scene("main")
    parent = scene.add(p3d.Node("parent"))
    child = parent.add(p3d.Node("child"))
    parent.on_update = lambda dt: order.append(("parent", dt))
    child.on_update = lambda dt: order.append(("child", dt))
    scene.update(0.5)
    assert order == [("parent", 0.5), ("child", 0.5)]


def test_scene_counts_and_background():
    scene = p3d.Scene("main")
    scene.add(p3d.Node("a"))
    scene.add(p3d.Node("b"))
    assert scene.node_count() == 2
    assert [node.name for node in scene.nodes] == ["a", "b"]
    assert scene.background == (12, 12, 16, 255)
    assert scene.find("b") is not None


# -- input ------------------------------------------------------------- #

def test_key_state_lifecycle():
    state = p3d.InputState()
    state.handle_event(p3d.KeyDown(key="Space"))
    assert state.is_down("space")
    assert state.was_pressed("space")
    assert state.pressed_keys == frozenset({"space"})

    state.end_frame()
    assert state.is_down("space")
    assert not state.was_pressed("space")

    state.handle_event(p3d.KeyUp(key="space"))
    assert not state.is_down("space")
    assert state.was_released("space")


def test_actions_follow_bindings():
    state = p3d.InputState()
    state.bind_action("jump", "space", "w")
    assert state.action_keys("jump") == frozenset({"space", "w"})
    state.handle_event(p3d.KeyDown(key="w"))
    assert state.action_down("jump")
    assert state.action_pressed("jump")
    state.end_frame()
    assert state.action_down("jump")
    assert not state.action_pressed("jump")


def test_unknown_action_raises():
    state = p3d.InputState()
    with pytest.raises(p3d.ConfigurationError):
        state.action_keys("dash")
    with pytest.raises(p3d.ConfigurationError):
        state.bind_action("dash")


def test_key_and_action_callbacks_fire_on_press_only():
    state = p3d.InputState()
    state.bind_action("jump", "space")
    key_hits, action_hits = [], []
    state.on_key_press("space", lambda key: key_hits.append(key))
    state.on_action_press("jump", lambda action: action_hits.append(action))

    state.handle_event(p3d.KeyDown(key="space"))
    state.handle_event(p3d.KeyDown(key="space"))  # repeat does not re-fire
    assert key_hits == ["space"]
    assert action_hits == ["jump"]

    state.handle_event(p3d.KeyUp(key="space"))
    state.handle_event(p3d.KeyDown(key="space"))
    assert key_hits == ["space", "space"]


def test_mouse_and_wheel_state():
    state = p3d.InputState()
    state.handle_event(p3d.MouseMove(x=12, y=34))
    assert state.mouse_position() == p3d.Vec2(12, 34)

    state.handle_event(p3d.MouseButton(button=1, pressed=True, x=5, y=6))
    assert state.button_down(1)
    assert state.button_pressed(1)
    assert state.mouse_position() == p3d.Vec2(5, 6)

    state.handle_event(p3d.MouseWheel(dy=1.0))
    state.handle_event(p3d.MouseWheel(dy=0.5))
    assert state.wheel_dy == pytest.approx(1.5)

    state.end_frame()
    assert state.button_down(1)
    assert not state.button_pressed(1)
    assert state.wheel_dy == 0.0

    state.handle_event(p3d.MouseButton(button=1, pressed=False))
    assert not state.button_down(1)
