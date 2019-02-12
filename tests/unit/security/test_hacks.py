from unittest import TestCase
from seneca.engine.interface import SenecaInterface
from seneca.engine.interpreter import SenecaInterpreter, ReadOnlyException, CompilationException
from os.path import join
from tests.utils import captured_output, TestInterface
import redis, unittest, seneca

test_contracts_path = seneca.__path__[0] + '/test_contracts/'

class TestHacks(TestInterface):

    def test_forbidden_import(self):
        with self.assertRaises(ImportError) as context:
            self.si.execute_code_str("""
import sys
            """)


    def test_modify_imports(self):
        with self.assertRaises(ReadOnlyException) as context:
            self.si.execute_code_str("""
from test_contracts.sample import good_call
def bad_call():
    return 'hacked'
good_call = bad_call
            """)

    def test_del_variables(self):
        with self.assertRaises(AssertionError) as context:
            self.si.execute_code_str("""
from test_contracts.sample import good_call
del good_call
            """)

    def test_access_underscore_attributes(self):
        with self.assertRaises(CompilationException) as context:
            self.si.execute_code_str("""
v = abs.__self__.__dict__
            """)

    def test_callable_exec(self):
        with self.assertRaises(CompilationException) as context:
            self.si.execute_code_str("""
callable.__self__.__dict__['exec']('''
import sys
''')
            """)

    def test_globals(self):
        with self.assertRaises(CompilationException) as context:
            self.si.execute_code_str("""
v = __builtins__['__import__']('sys')
            """)

    def test_tracer(self):
        from seneca.libs.metering.tracer import Tracer
        with self.assertRaises(CompilationException) as context:
            self.si.execute_code_str("""
__tracer__.set_stamp(1000)
            """, added_scope={'__tracer__': Tracer()})

    def test_import(self):
        with self.assertRaises(CompilationException) as context:
            self.si.execute_code_str("""
__import__('sys')
            """)

# No memory limit for now
#     def test_overflow(self):
#         with self.assertRaises(ValueError) as context:
#             self.si.execute_code_str("""
# obj = {}
# for i in range(int(1000000)):
#     obj[i*int(10000000)] = i*int(10000000)
#             """)
#             print('passed through')
#         with self.assertRaises(ValueError) as context:
#             self.si.execute_code_str("""
# obj = {}
# for i in range(int(1000000)):
#     obj[i*int(10000000)] = i*int(10000000)
#             """)

    def test_recursion(self):
        with self.assertRaises(RecursionError) as context:
            self.si.execute_code_str("""
def recurse():
    return recurse()
recurse()
            """)


if __name__ == '__main__':
    # print('#' * 128)
    # print('Listing attributes assesible in each built-in values:')
    # print('#' * 128)
    # from seneca.constants.whitelists import _SAFE_NAMES
    # for name in _SAFE_NAMES:
    #     v = eval(name)
    #     print('{}:\n\t{}'.format(
    #         v,
    #         [k for k in dir(v) if not k.startswith('__')],
    #     ))
    unittest.main()
