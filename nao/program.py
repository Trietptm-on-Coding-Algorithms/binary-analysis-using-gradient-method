import subprocess
import functools
import time
import sys

from ptrace.debugger.process_event import ProcessExit
from ptrace.error import PtraceError

from .inspector import Inspector
from .exceptions import * # pylint: disable=W0614
from .ast import constraint as ir
from .encoder import Encode, encode_constraint_to_loss_function_ast
from .evaluate import evaluate_constraint_ast
from .y import yadapter


class X():
    def __init__(self, args=[], stdin='', files={}, env={}):
        assert isinstance(args, list)
        assert isinstance(stdin, str)
        self.args = args
        self.stdin = stdin
        self.files = files
        self.env = env

    def __repr__(self):
        return "{}(args={!r}, stdin={!r}, files={!r}, env={!r})".format(self.__class__.__name__, self.args, self.stdin, self.files, self.env)

class Program:
    # @param xadapter encodes vector to vales of x variables (program inputs)
    # @param yadapter encodes values of y variables to vector
    def __init__(self, program, xadapter, debug=False):
        assert isinstance(program, str), "'program` must be a path to program"
        assert callable(xadapter), "`adapter` must be a fucntion"
        self.program = program
        self.xadapter = xadapter
        # self.inspector = Inspector(program, debug=True)
        self.inspector = Inspector(program, debug=False)
        self.debug = debug

    def get_constraints(self, tactic, object_name=None, relative_addr=None, rebased_addr=None):
        if relative_addr:
            return self.inspector.get_condition_at(tactic, object_name=object_name, relative_addr=relative_addr)
        if rebased_addr:
            return self.inspector.get_condition_at(tactic, rebased_addr=rebased_addr)
        raise UnhandledCaseError("provide relative_addr or rebased_addr")

    def N(self, constraint):
        assert isinstance(constraint, ir.ConstraintIR)
        return functools.partial(self.call_with_adapter, constraint)
    
    def L(self, constraint):
        assert isinstance(constraint, ir.ConstraintIR)
        return Encode(constraint)

    def call(self, y_constraints, x):
        if self.debug: print("[*] call(y_constraints=..., x={})".format(x))
        assert isinstance(y_constraints, ir.ConstraintIR)
        assert isinstance(x, X), "x must be instance of X: x = {}".format(x)

        if not isinstance(y_constraints, ir.ConstraintList):
            y_constraints = ir.ConstraintList([y_constraints])

        while True:
            try:
                self.inspector.run(args=x.args, stdin=x.stdin, files=x.files, env=x.env)
                break
            except (ProcessExit, PtraceError) as e:
                if self.debug: print("[!] Exception at program.call(): {}".format(e))
                self.inspector.stop()
                time.sleep(1.0)
                if self.debug: print("[!] Retrying run()")
                sys.stdout.flush()
                continue
            except AssertionError as e:
                raise e
            except Exception as e:
                print("[!] Unhandled exception at program.call(): {} (type={})".format(e, type(e)))
                sys.stdout.flush()
                exit(1)

        res = self.inspector.collect(y_constraints)
        self.inspector.stop()

        # if self.debug: print("[*] Program.call() = {}".format(res))
        return res

    def call_with_adapter(self, constraint, x):
        ### FIXME: Dirty implementation. non-efficient implementaiton
        context = self.call(constraint, self.xadapter(x))
        context = evaluate_constraint_ast(constraint, context)
        loss_function_ast = encode_constraint_to_loss_function_ast(constraint)
        return yadapter(loss_function_ast, context)

    def run(self, x):
        assert(isinstance(x, X))
        if self.debug: print("run(x={})".format(x))
        args = [self.program] + x.args

        p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=x.env)

        return p.communicate(x.stdin)