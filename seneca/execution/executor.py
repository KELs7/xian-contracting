import importlib
import multiprocessing
from typing import Dict

from . import runtime
from ..db.cr.transaction_bag import TransactionBag
from ..db.driver import CRDriver, ContractDriver
from ..execution.module import install_database_loader


class Executor:

    def __init__(self, metering=True, production=False):
        self.metering = metering

        # Colin -  Setup the tracer
        # Colin TODO: Find out why Tracer is not instantiating properly. Raghu also said he wants to pull this out.
        #cu_cost_fname = join(seneca.__path__[0], 'constants', 'cu_costs.const')
        #self.tracer = Tracer(cu_cost_fname)

        self.tracer = None

        if production:
            self.driver = CRDriver()
            self.sandbox = MultiProcessingSandbox()
        else:
            self.sandbox = Sandbox()
            self.driver = ContractDriver()

    def execute_bag(self, bag: TransactionBag) -> Dict[int, dict]:
        """
        The execute bag method sends a list of transactions to the sandbox to be executed

        :param bag: a list of deserialized transaction objects
        :return: a dict of results (result index == bag index), formatted as
                 [ (status_code, result), ... ] where status_code is 0 or 1
                 depending on success/failure and result is what is returned
                 from executing the underlying function
        """
        results = {}
        for idx, tx in bag:
            self.driver.setup(idx, bag.cr_context)
            results[idx] = self.execute(tx.sender, tx.contract_name, tx.function_name, tx.kwargs)

        return results

    def execute(self, sender, contract_name, function_name, kwargs, environment={}) -> dict:
        """
        Method that does a naive execute

        :param sender:
        :param contract_name:
        :param function_name:
        :param kwargs:
        :return: result of execute call
        """
        # A successful run is determined by if the sandbox execute command successfully runs.
        # Therefor we need to have a try catch to communicate success/fail back to the
        # client. Necessary in the case of batch run through bags where we still want to
        # continue execution in the case of failure of one of the transactions.
        try:
            result = self.sandbox.execute(sender, contract_name, function_name, kwargs, environment)
            status_code = 0
            runtime.rt.driver.commit()
        # TODO: catch SenecaExceptions distinctly, this is pending on Raghu looking into Exception override in compiler
        except Exception as e:
            result = e
            status_code = 1
            runtime.rt.driver.revert()
        runtime.rt.clean_up()

        return status_code, result


"""
The Sandbox class is used as a execution sandbox for a transaction.

I/O pattern:

    ------------                                  -----------
    | Executor |  ---> Transaction Bag (all) ---> | Sandbox |
    ------------                                  -----------
                                                       |
    ------------                                       v
    | Executor |  <---      Send Results     <---  Execute all tx
    ------------

    * The client sends the whole transaction bag to the Sandbox for
      processing. This is done to minimize back/forth I/O overhead
      and deadlocks
    * The sandbox executes all of the transactions one by one, resetting
      the syspath after each execution.
    * After all execution is complete, pass the full set of results
      back to the client again to minimize I/O overhead and deadlocks
    * Sandbox blocks on pipe again for new bag of transactions
"""


class Sandbox(object):
    def __init__(self):
        install_database_loader()

    def execute(self, sender, contract_name, function_name, kwargs, environment={}):

        # __main__ is replaced by the sender of the message in this case
        runtime.rt.ctx.clear()
        runtime.rt.ctx.append(sender)
        runtime.rt.env = environment

        module = importlib.import_module(contract_name)

        func = getattr(module, function_name)

        return func(**kwargs)

# TODO: Test environment variable passing in multiprocess sandboxing
class MultiProcessingSandbox(Sandbox):
    def __init__(self):
        super().__init__()
        self.pipe = multiprocessing.Pipe()
        self.p = None

    def terminate(self):
        if self.p is not None:
            self.p.terminate()

    def execute(self, sender, contract_name, function_name, kwargs, environment={}):
        if self.p is None:
            self.p = multiprocessing.Process(target=self.process_loop,
                                             args=(super().execute, ))
            self.p.start()

        _, child_pipe = self.pipe

        # Sends code to be executed in the process loop
        child_pipe.send((sender, contract_name, function_name, kwargs, environment))

        # Receive result object back from process loop, formatted as
        # (status_code, result), loaded in using dill due to python
        # base pickler not knowning how to pickle module object
        # returned from execute
        status_code, result = child_pipe.recv()

        # Check the status code for failure, if failure raise the result
        if status_code > 0:
            raise result
        return result

    def process_loop(self, execute_fn):
        parent_pipe, _ = self.pipe
        while True:
            sender, contract_name, function_name, kwargs, environment = parent_pipe.recv()
            try:
                result = execute_fn(sender, contract_name, function_name, kwargs, environment={})
                status_code = 0
            except Exception as e:
                result = e
                status_code = 1
            finally:
                # Pickle the result using dill so module object can be retained
                parent_pipe.send((status_code, result))
