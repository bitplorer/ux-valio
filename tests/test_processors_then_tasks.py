# SPDX-License-Identifier: MIT
"""Processors run then tasks once. Only the pre_set *hook* return is stored.

There is no ``add_pre_set`` / ``_processors["pre_set"]`` bag. Hang before-store
work on ``add_process_pre_validate`` (inside ``pre_set``). ``add_process_post_set`` runs after
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

    _bind_phase(v, HookHost._owner_key(Host), log, "add_process_pre_validate", "add_task_pre_validate", "pre")

    host = Host(x="raw")
    assert host.x == "raw-p"
    HookHost.wait_tasks(timeout=2)
    assert log == [("pre_proc", "raw"), ("pre_task", "raw-p")]


def test_validator_all_phases_run_task_once_after_processing():
    log = []
    v = Validator(debug=True)

    @dataclass
    class Host:
        x: str = v

    ns = HookHost._owner_key(Host)
    phases = (
        ("add_process_pre_validate", "add_task_pre_validate", "pre"),
        ("add_process_post_validate", "add_task_post_validate", "post"),
        ("add_process_post_set", "add_task_post_set", "set"),
        ("add_process_pre_get", "add_task_pre_get", "pget"),
        ("add_process_post_get", "add_task_post_get", "gget"),
        ("add_process_pre_delete", "add_task_pre_delete", "pdel"),
        ("add_process_post_delete", "add_task_post_delete", "gdel"),
    )
    for add_name, task_add_name, label in phases:
        _bind_phase(v, ns, log, add_name, task_add_name, label)

    host = Host(x="raw")
    _ = host.x
    del host.x
    HookHost.wait_tasks(timeout=2)

    procs = [event for event in log if event[0].endswith("_proc")]
    tasks = [event for event in log if event[0].endswith("_task")]
    assert procs == [
        ("pre_proc", "raw"),
        ("post_proc", "raw-p"),
        ("set_proc", "raw-p-p"),
        ("pget_proc", "x"),
        ("gget_proc", "x"),
        ("pdel_proc", "x"),
        ("gdel_proc", "x"),
    ]
    assert set(tasks) == {
        ("pre_task", "raw-p"),
        ("post_task", "raw-p-p"),
        ("set_task", "raw-p-p-s"),
        ("pget_task", "x-p"),
        ("gget_task", "x-g"),
        ("pdel_task", "x-p"),
        ("gdel_task", "x-g"),
    }


def test_plain_validator_processing_without_tasks():
    log = []
    v = Validator(debug=True)

    def proc(instance, value):
        log.append(("proc", value))
        return value.upper()

    @dataclass
    class Plain:
        x: str = v

    v.add_process_pre_validate(proc, namespace=Plain)

    assert Plain(x="raw").x == "RAW"
    assert log == [("proc", "raw")]


def test_only_pre_set_processor_return_is_stored():
    v = Validator(debug=True)

    def post_set_proc(instance, value):
        return "SHOULD_NOT_STORE"

    @dataclass
    class Host:
        x: str = v

    v.add_process_post_set(post_set_proc, namespace=Host)

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

    v.add_process_pre_get(pget, namespace=Host)

    host = Host(x="stored")
    assert host.x == "stored"
    assert log == [("pget", "x")]


def test_task_does_not_block_the_setter():
    import threading

    started = threading.Event()
    release = threading.Event()
    seen: list[str] = []
    v = Validator(debug=True)

    def email(instance, value):
        started.set()
        release.wait(timeout=2)
        seen.append(value)

    @dataclass
    class Host:
        x: str = v

    v.add_task_post_set(email, namespace=Host)

    host = Host(x="ada")
    assert host.x == "ada"
    assert started.wait(timeout=2)
    assert seen == []
    release.set()
    HookHost.wait_tasks(timeout=2)
    assert seen == ["ada"]


def test_task_error_does_not_fail_the_set():
    v = Validator(debug=True)

    def boom(instance, value):
        raise RuntimeError("smtp down")

    @dataclass
    class Host:
        x: str = v

    v.add_task_post_set(boom, namespace=Host)

    host = Host(x="ada")
    assert host.x == "ada"
    HookHost.wait_tasks(timeout=2)
    assert any(isinstance(err, RuntimeError) for err in v.errors)
