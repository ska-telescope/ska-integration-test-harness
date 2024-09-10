
Core mechanisms API
--------------------------------


Here below are documented the core mechanisms
of the ska-integration-test-harness. Implementation of specific
actions and structures are currently left outside, see directly the code
for more details.

**IMPORTANT NOTE**: A very crucial aspect of the core mechanisms is that
they are unit tested code, while the specific actions and structures are
not unit tested (and in a certain sense, the integration tests that use
the test harness are the validation of the correctness of the implementation
of the specific actions and structures). **The coverage metrics of the
test harness are calculated only on the core mechanisms** (*at the time of
writing, the coverage on the core mechanisms is approximately 90%, while
the overall coverage is around 60%*).

Structure module
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: ska_integration_test_harness.structure
    :members:
    :undoc-members:


Actions module
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: ska_integration_test_harness.actions
    :members:
    :undoc-members:


Inputs module
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: ska_integration_test_harness.inputs
    :members:
    :undoc-members:

Inputs validation
~~~~~~~~~~~~~~~~~

.. automodule:: ska_integration_test_harness.inputs.validation
    :members:
    :undoc-members:


Config(uration) module
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: ska_integration_test_harness.config
    :members:
    :undoc-members:


Config reader
~~~~~~~~~~~~~~

.. automodule:: ska_integration_test_harness.config.reader
    :members:
    :undoc-members:


Config validation
~~~~~~~~~~~~~~~~~

.. automodule:: ska_integration_test_harness.config.validation
    :members:
    :undoc-members:

Init(ialization) module
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: ska_integration_test_harness.init
    :members:
    :undoc-members:



