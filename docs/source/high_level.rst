High-level interfaces
================================

PyMavryk client
++++++++++++++++
.. autoclass:: pymavryk.client.PyMavrykClient
   :members:
   :inherited-members:

Contract interface
++++++++++++++++++++
.. autoclass:: pymavryk.contract.interface.ContractInterface
   :members:
   :inherited-members:

Contract entrypoint proxy
+++++++++++++++++++++++++++
.. autoclass:: pymavryk.contract.entrypoint.ContractEntrypoint
   :members:
   :special-members: __call__
   :inherited-members:

Contract call proxy
+++++++++++++++++++++
.. autoclass:: pymavryk.contract.call.ContractCall
   :members:
   :inherited-members:

Contract call result
++++++++++++++++++++++
.. autoclass:: pymavryk.contract.result.ContractCallResult
   :members:

Contract storage proxy
++++++++++++++++++++++
.. autoclass:: pymavryk.contract.data.ContractData
   :members:
   :special-members: __call__
   :inherited-members:

Contract view proxy
+++++++++++++++++++
.. autoclass:: pymavryk.contract.view.ContractView
   :members:
   :inherited-members:
