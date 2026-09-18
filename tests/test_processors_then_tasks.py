# SPDX-License-Identifier: MIT
"""Processors run then tasks once. Only the pre_set *hook* return is stored.

There is no ``add_pre_set`` / ``_processors["pre_set"]`` bag. Hang before-store
work on ``add_pre_validator`` (inside ``pre_set``). ``add_post_set`` runs after
store and its return is ignored.
"""

from dataclasses import dataclass

from ux_valio import Validator
from ux_valio.validators.hooks import HookHost


def _bind_phase(validator, namespace, log, add_name, task_add_name, label):
    def proc(instance, value):
        log.append((f"{label}_proc", value))
        if isinstance(value, str):
            return f"{value}-{label[0]}"
        return value

    def task(instance, value):
        log.append((f"{label}_task", value))

    getattr(validator, add_name)(proc, namespace=namespace)
    getattr(validator, task_add_name)(task, namespace=namespace)


def test_validator_runs_processing_then_task_once():
    log = []
    v = Validator(debug=True)

    @dataclass
    class Host:
        x: str = v

    _bind_phase(v, HookHost._bag_key(Host), log, "add_pre_validator", "add_pre_validator_task", "pre")

    host = Host(x="raw")
    assert host.x == "raw-p"
    assert log == [("pre_proc", "raw"), ("pre_task", "raw-p")]


def test_validator_all_phases_run_task_once_after_processing():
    log = []
    v = Validator(debug=True)

    @dataclass
    class Host:
        x: str = v

    ns = HookHost._bag_key(Host)
    phases = (
        ("add_pre_validator", "add_pre_validator_task", "pre"),
        ("add_post_validator", "add_post_validator_task", "post"),
        ("add_post_set", "add_post_set_task", "set"),
        ("add_pre_get", "add_pre_get_task", "pget"),
        ("add_post_get", "add_post_get_task", "gget"),
        ("add_pre_delete", "add_pre_delete_task", "pdel"),
        ("add_post_delete", "add_post_delete_task", "gdel"),
    )
    for add_name, task_add_name, label in phases:
        _bind_phase(v, ns, log, add_name, task_add_name, label)

    host = Host(x="raw")
    _ = host.x
    del host.x

    assert log == [
        ("pre_proc", "raw"),
        ("pre_task", "raw-p"),
        ("post_proc", "raw-p"),
        ("post_task", "raw-p-p"),
        ("set_proc", "raw-p-p"),
        ("set_task", "raw-p-p-s"),
        ("pget_proc", "x"),
        ("pget_task", "x-p"),
        ("gget_proc", "x"),
        ("gget_task", "x-g"),
        ("pdel_proc", "x"),
        ("pdel_task", "x-p"),
        ("gdel_proc", "x"),
        ("gdel_task", "x-g"),
    ]


def test_plain_validator_processing_without_tasks():
    log = []
    v = Validator(debug=True)

    def proc(instance, value):
        log.append(("proc", value))
        return value.upper()

    @dataclass
    class Plain:
        x: str = v

    v.add_pre_validator(proc, namespace=HookHost._bag_key(Plain))

    assert Plain(x="raw").x == "RAW"
    assert log == [("proc", "raw")]


def test_only_pre_set_processor_return_is_stored():
    v = Validator(debug=True)

    def post_set_proc(instance, value):
        return "SHOULD_NOT_STORE"

    @dataclass
    class Host:
        x: str = v

    v.add_post_set(post_set_proc, namespace=HookHost._bag_key(Host))

    assert Host(x="kept").x == "kept"


def test_get_processors_see_attribute_name_not_stored_value():
    log = []
    v = Validator(debug=True)

    def pget(instance, value):
        log.append(("pget", value))
        return value

    @dataclass
    class Host:
        x: str = v

    v.add_pre_get(pget, namespace=HookHost._bag_key(Host))

    host = Host(x="stored")
    assert host.x == "stored"
    assert log == [("pget", "x")]
