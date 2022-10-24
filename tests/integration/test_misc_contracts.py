import importlib
from unittest import TestCase
from contracting.stdlib.bridge.time import Datetime
from contracting.client import ContractingClient


def too_many_writes():
    v = Variable()

    @export
    def single():
        v.set('a' * (32 * 1024 + 1))

    @export
    def multiple():
        for i in range(32 * 1024 + 1):
            v.set('a')

    @export
    def not_enough():
        v.set('a' * (30 * 1024))

    @export
    def run():
        a = ""
        for i in range(1000000):
            a += "NAME" * 10

        return a

    @export
    def run2():
        a = 0
        b = ""
        for i in range(1000000):
            b = b + "wow" + "baseName" * a
            a += 1
        return b


def exploit():
    @construct
    def seed():
        a = 0
        b = ""
        for i in range(10000000):
            b = b + "wow" + "baseName" * a
            a += 1
        return b

    @export
    def b():
        pass


class TestMiscContracts(TestCase):
    def setUp(self):
        self.c = ContractingClient(signer='stu')
        self.c.raw_driver.flush()

        with open('../../contracting/contracts/submission.s.py') as f:
            contract = f.read()

        self.c.raw_driver.set_contract(name='submission', code=contract,)

        self.c.raw_driver.commit()

        submission = self.c.get_contract('submission')

        self.c.submit(too_many_writes)

        # submit erc20 clone
        with open('./test_contracts/thing.s.py') as f:
            code = f.read()
            self.c.submit(code, name='thing')

        with open('./test_contracts/foreign_thing.s.py') as f:
            code = f.read()
            self.c.submit(code, name='foreign_thing')

        self.thing = self.c.get_contract('thing')
        self.foreign_thing = self.c.get_contract('foreign_thing')

    def tearDown(self):
        self.c.flush()

    def test_H_values_return(self):
        output = self.foreign_thing.read_H_hello()
        self.assertEqual(output, 'there')

        output = self.foreign_thing.read_H_something()
        self.assertEqual(output, 'else')

    def test_cant_modify_H(self):
        with self.assertRaises(ReferenceError):
            self.foreign_thing.set_H(k='hello', v='not_there')

    def test_cant_add_H(self):
        with self.assertRaises(ReferenceError):
            self.foreign_thing.set_H(k='asdf', v='123')

    def test_cant_set_V(self):
        with self.assertRaises(ReferenceError):
            self.foreign_thing.set_V(v=123)

    def test_V_returns(self):
        output = self.foreign_thing.read_V()
        self.assertEqual(output, 'hi')

    def test_single_too_many_writes_fails(self):
        tmwc = self.c.get_contract('too_many_writes')
        self.c.executor.metering = True
        self.c.set_var(contract='currency', variable='balances', arguments=['stu'], value=1000000)
        with self.assertRaises(AssertionError):
            tmwc.single()
        self.c.executor.metering = False

    def test_multiple_too_many_writes_fails(self):
        tmwc = self.c.get_contract('too_many_writes')
        self.c.executor.metering = True
        self.c.set_var(contract='currency', variable='balances', arguments=['stu'], value=1000000)
        with self.assertRaises(AssertionError):
            tmwc.multiple()
        self.c.executor.metering = False

    def test_failed_once_doesnt_affect_others(self):
        tmwc = self.c.get_contract('too_many_writes')
        self.c.executor.metering = True
        self.c.set_var(contract='currency', variable='balances', arguments=['stu'], value=1000000)
        with self.assertRaises(AssertionError):
            tmwc.multiple()
        tmwc.not_enough()
        self.c.executor.metering = False

    def test_memory_overload(self):
        tmwc = self.c.get_contract('too_many_writes')
        self.c.executor.metering = True
        self.c.set_var(contract='currency', variable='balances', arguments=['stu'], value=1000000)
        with self.assertRaises(AssertionError):
            tmwc.run()
        self.c.executor.metering = False

    def test_memory_overload2(self):
        tmwc = self.c.get_contract('too_many_writes')
        self.c.executor.metering = True
        self.c.set_var(contract='currency', variable='balances', arguments=['stu'], value=1000000)
        with self.assertRaises(AssertionError):
            tmwc.run2()
        self.c.executor.metering = False

    def test_memory_exploit(self):
        self.c.executor.metering = True
        self.c.set_var(contract='currency', variable='balances', arguments=['stu'], value=1000000)
        with self.assertRaises(AssertionError):
            self.c.submit(exploit)
        self.c.executor.metering = False

class TestPassHash(TestCase):
    def setUp(self):
        self.c = ContractingClient(signer='stu')
        self.c.raw_driver.flush()

        with open('../../contracting/contracts/submission.s.py') as f:
            contract = f.read()

        self.c.raw_driver.set_contract(name='submission', code=contract,)

        self.c.raw_driver.commit()

        submission = self.c.get_contract('submission')

        # submit erc20 clone
        with open('./test_contracts/pass_hash.s.py') as f:
            code = f.read()
            self.c.submit(code, name='pass_hash')

        with open('./test_contracts/test_pass_hash.s.py') as f:
            code = f.read()
            self.c.submit(code, name='test_pass_hash')

        self.pass_hash = self.c.get_contract('pass_hash')
        self.test_pass_hash = self.c.get_contract('test_pass_hash')

    def test_store_value(self):
        self.test_pass_hash.store(k='thing', v='value')
        output = self.test_pass_hash.get(k='thing')

        self.assertEqual(output, 'value')


def test():
    @export
    def return_something():
        return 1


def import_submission():
    import submission

    @export
    def haha():
        code = '''
@export
def something():
    pass
'''
        submission.submit_contract(name='something123', code=code)


class TestDeveloperSubmission(TestCase):
    def setUp(self):
        self.c = ContractingClient(signer='stu')
        self.c.raw_driver.flush()

        with open('../../contracting/contracts/submission.s.py') as f:
            contract = f.read()

        self.c.raw_driver.set_contract(name='submission', code=contract,)

        self.c.raw_driver.commit()

    def test_submit_sets_developer(self):
        self.c.submit(test)

        dev = self.c.get_var('test', '__developer__')

        self.assertEqual(dev, 'stu')

    def test_change_developer_if_developer_works(self):
        self.c.submit(test)

        submission = self.c.get_contract('submission')

        submission.change_developer(contract='test', new_developer='not_stu')

        dev = self.c.get_var('test', '__developer__')

        self.assertEqual(dev, 'not_stu')

    def test_change_developer_prevents_new_change(self):
        self.c.submit(test)

        submission = self.c.get_contract('submission')

        submission.change_developer(contract='test', new_developer='not_stu')

        with self.assertRaises(AssertionError):
            submission.change_developer(contract='test', new_developer='woohoo')

    def test_cannot_import_submission(self):
        self.c.submit(import_submission)

        imp_con = self.c.get_contract('import_submission')

        with self.assertRaises(AssertionError):
            imp_con.haha()


def float_thing():
    @export
    def test(currency_reserve: float, token_reserve: float, currency_amount: float):
        k = currency_reserve * token_reserve

        new_currency_reserve = currency_reserve + currency_amount
        new_token_reserve = k / new_currency_reserve

        tokens_purchased = token_reserve - new_token_reserve
        return tokens_purchased


class TestFloatThing(TestCase):
    def setUp(self):
        self.c = ContractingClient(signer='stu')
        self.c.raw_driver.flush()

        with open('../../contracting/contracts/submission.s.py') as f:
            contract = f.read()

        self.c.raw_driver.set_contract(name='submission', code=contract,)

        self.c.raw_driver.commit()

    def test_can_add(self):
        self.c.submit(float_thing)

        ft_con = self.c.get_contract('float_thing')

        ft_con.test(currency_reserve=50000.125, token_reserve=52.45, currency_amount=100.25)

def a():
    @export
    def x():
        return 1

def module_hack():
    v = Variable()

    @export
    def hack():
        hack.__module__
        return 1


def class_var():
    @export
    def hack():
        v = Variable
        x = v(contract="currency", name="balances")


def class_hash():
    @export
    def hack():
        v = Hash
        x = v(contract="currency", name="balances")


def exec_contract():
    @export
    def fn():
        def builtins__():
            pass

    wExec = builtins__["exec"]
    wExec("print('hello world')")

def type_exploit():
    @export
    def attack(to: str):
        # before
        # assert amount > 0, 'Cannot send negative balances!'
        def gt(a, b):
            print("gt", a, b)
            return True

        # assert balances[sender] >= amount, 'Not enough coins to send!'
        def le(a, b):
            print("lt", a, b)
            return True

        # balances[sender] -= amount
        def rsub(a, b):
            print("rsub", a, b)
            return b

        # balances[to] += amount
        def radd(a, b):
            print("radd", a, b)
            return 100

        wAmount = type("wAmount", (), {"__gt__": gt, "__le__": le, "__radd__": radd, "__rsub__": rsub})
        fake_amount_object = wAmount()

def test_one():
    h = Hash()

    @construct
    def seed():
        h['a'] = 100
        h['b'] = 999

    @export
    def output():
        return h['a'], h['b']

def test_two():
    f = ForeignHash(foreign_contract='test_one', foreign_name='h')

    @export
    def clear():
        f.clear()

def test_closure():
    def export(contract):
        def decorator(func):
            def enter(*args, **kwargs):
                result = func(*args, **kwargs)
                return result
            return enter
        return decorator

    @export
    def test():
        return 1

class TestHackThing(TestCase):
    def setUp(self):
        self.c = ContractingClient(signer='stu')
        self.c.raw_driver.flush()

        with open('../../contracting/contracts/submission.s.py') as f:
            contract = f.read()

        self.c.raw_driver.set_contract(name='submission', code=contract,)

        self.c.raw_driver.commit()

    def test_can_add(self):
        self.c.submit(a)
        with self.assertRaises(Exception):
            self.c.submit(module_hack)

            ft_con = self.c.get_contract('module_hack')

            ft_con.hack()

    def test_cant_submit_class_var(self):
        with self.assertRaises(Exception):
            self.c.submit(class_var)

    def test_cant_submit_class_hash(self):
        with self.assertRaises(Exception):
            self.c.submit(class_hash)

    def test_cant_submit_exec(self):
        with self.assertRaises(Exception):
            self.c.submit(exec_contract)

    def test_cant_submit_type(self):
        with self.assertRaises(Exception):
            self.c.submit(type_exploit)

    def test_cant_clear_foreign_hash(self):
        self.c.submit(test_one)
        self.c.submit(test_two)

        t2 = self.c.get_contract('test_two')

        with self.assertRaises(Exception):
            t2.clear()

    def test_no_closures(self):
        with self.assertRaises(Exception):
            self.c.submit(test_closure)