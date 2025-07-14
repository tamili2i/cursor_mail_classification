import pytest
from week6.collaborative_docs_architecture.services.collaboration_service.ot import OTOperation, transform, apply_operation, OTState

def test_insert_apply():
    text = "hello"
    op = OTOperation("insert", 5, text=" world")
    result = apply_operation(text, op)
    assert result == "hello world"

def test_delete_apply():
    text = "hello world"
    op = OTOperation("delete", 5, length=6)
    result = apply_operation(text, op)
    assert result == "hello"

def test_transform_insert_insert():
    op1 = OTOperation("insert", 2, text="A")
    op2 = OTOperation("insert", 4, text="B")
    t1 = transform(op1, op2)
    t2 = transform(op2, op1)
    assert t1.pos == 2
    assert t2.pos == 5

def test_transform_insert_delete():
    op1 = OTOperation("insert", 5, text="A")
    op2 = OTOperation("delete", 2, length=2)
    t1 = transform(op1, op2)
    assert t1.pos == 3

def test_otstate_undo_redo():
    state = OTState("abc")
    op1 = OTOperation("insert", 3, text="d")
    state.apply(op1)
    assert state.text == "abcd"
    state.undo()
    assert state.text == "abc"
    state.redo()
    assert state.text == "abcd" 