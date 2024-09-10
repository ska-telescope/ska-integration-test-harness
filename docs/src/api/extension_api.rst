Extensions and specific logic API
-------------------------------------


This section is a sort of enumeration of the main concrete *non-core*
classes and components that are part of the 
ska-integration-test-harness for testing
TMC-CSP in MID (at the time of writing).

**IMPORTANT NOTE**: A very crucial difference from the core mechanisms
section is that the classes and components described here are not unit
tested code, since they are considered more related to the specific SUT
logic than to the test harness itself. In a certain sense, the integration
tests that use the test harness are the validation of the correctness of
the implementation of the classes and components described in this section.
**The coverage metrics of the
test harness are calculated only on the first section** (*at the time of
writing, the coverage on the first section is approximately 90%, while
the overall coverage is around 60%*).

An example of tests that use what is described in the second section
are the ones introduced in `ska-tmc-mid-integration` by this
`merge request <https://gitlab.com/ska-telescope/ska-tmc-mid-integration/-/merge_requests/1>`_.



Facades module
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: ska_integration_test_harness.facades
    :members:
    :undoc-members:

Central Node actions
^^^^^^^^^^^^^^^^^^^^^^^^^^^


.. automodule:: ska_integration_test_harness.actions.central_node
    :members:
    :undoc-members:


Subarray actions
^^^^^^^^^^^^^^^^^^^^^^^^^^^


.. automodule:: ska_integration_test_harness.actions.subarray
    :members:
    :undoc-members: