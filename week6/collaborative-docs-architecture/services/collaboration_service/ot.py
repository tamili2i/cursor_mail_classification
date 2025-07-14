from typing import List, Dict, Any, Optional

class OTOperation:
    def __init__(self, op_type: str, pos: int, text: str = "", length: int = 0, user_id: Optional[str] = None):
        self.op_type = op_type  # 'insert' or 'delete'
        self.pos = pos
        self.text = text
        self.length = length
        self.user_id = user_id

    def to_dict(self):
        return {
            "op_type": self.op_type,
            "pos": self.pos,
            "text": self.text,
            "length": self.length,
            "user_id": self.user_id
        }

    @staticmethod
    def from_dict(d):
        return OTOperation(d["op_type"], d["pos"], d.get("text", ""), d.get("length", 0), d.get("user_id"))

# Transform two operations against each other
# (simplified for insert/delete, no formatting)
def transform(op1: OTOperation, op2: OTOperation) -> OTOperation:
    if op1.op_type == "insert":
        if op2.op_type == "insert":
            if op1.pos <= op2.pos:
                return op1
            else:
                op1.pos += len(op2.text)
                return op1
        elif op2.op_type == "delete":
            if op1.pos <= op2.pos:
                return op1
            elif op1.pos > op2.pos + op2.length:
                op1.pos -= op2.length
                return op1
            else:
                op1.pos = op2.pos
                return op1
    elif op1.op_type == "delete":
        if op2.op_type == "insert":
            if op1.pos >= op2.pos:
                op1.pos += len(op2.text)
                return op1
            else:
                return op1
        elif op2.op_type == "delete":
            if op1.pos >= op2.pos + op2.length:
                op1.pos -= op2.length
                return op1
            elif op1.pos + op1.length <= op2.pos:
                return op1
            else:
                # Overlapping deletes: shrink
                overlap_start = max(op1.pos, op2.pos)
                overlap_end = min(op1.pos + op1.length, op2.pos + op2.length)
                overlap = max(0, overlap_end - overlap_start)
                op1.length -= overlap
                if op1.length < 0:
                    op1.length = 0
                return op1
    return op1

def apply_operation(text: str, op: OTOperation) -> str:
    if op.op_type == "insert":
        return text[:op.pos] + op.text + text[op.pos:]
    elif op.op_type == "delete":
        return text[:op.pos] + text[op.pos + op.length:]
    return text

class OTState:
    def __init__(self, initial_text: str = ""):
        self.text = initial_text
        self.version = 0
        self.history: List[OTOperation] = []
        self.undo_stack: List[OTOperation] = []
        self.redo_stack: List[OTOperation] = []

    def apply(self, op: OTOperation):
        self.text = apply_operation(self.text, op)
        self.history.append(op)
        self.version += 1
        self.undo_stack.append(op)
        self.redo_stack.clear()

    def undo(self):
        if not self.undo_stack:
            return
        op = self.undo_stack.pop()
        if op.op_type == "insert":
            rev = OTOperation("delete", op.pos, length=len(op.text))
        else:
            rev = OTOperation("insert", op.pos, text=self.text[op.pos:op.pos+op.length])
        self.text = apply_operation(self.text, rev)
        self.redo_stack.append(op)
        self.version += 1

    def redo(self):
        if not self.redo_stack:
            return
        op = self.redo_stack.pop()
        self.apply(op) 