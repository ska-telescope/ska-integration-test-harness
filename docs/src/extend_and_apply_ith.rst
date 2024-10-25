How to Use and Extend
========================


At the moment (October 2024) this harness has no well-defined
extension points yet and it is pretty specific to the TMC-CSP
integration tests in Mid. Based on feedback and on the evolution of the
project, the harness will be extended to be more flexible and to support
more use cases.

How to use this test harness right now as is
--------------------------------------------

To use this test harness *as is*, you can follow the instructions in :doc:`./getting_started`.

How to extend this test harness (within the current limitations)
----------------------------------------------------------------

Right now the test harness is designed for integration
tests of the TMC with CSP in Mid. Probably, it is still capable of
supporting TMC-X in Mid integrations tests.

Even if it is not yet generic, it still supports some level of
customisation. Within the current limitations, your main ways to extend
and/or customise this test harness are:

-  **Add new actions**: you can add new actions by sub-classing the
   ``TelescopeAction`` class and implementing the abstract methods. You
   can also create a sequence of actions by sub-classing the
   ``TelescopeActionSequence`` class and implementing the abstract
   methods. The actions can then be called from your tests, or also from
   new facades you may create.

      **Example**: you want to send a particular command to some SUT
      device and wait for some device to reach a particular state
      :math:`\to` *you create a new action that sends the command and
      specifies the expected state as a termination condition.*

   ..

      **Example**: you want to encode a complex procedure that requires
      multiple steps and synchronisation points :math:`\to` *you use the
      composite action mechanism to create a sequence of actions that
      perform the procedure. If there is the need of using if-then-else
      constructs or similar you can create a new action that acts as an
      orchestrator of other actions.*

-  **Add new facades**: you can create new facades that access the
   telescope wrappers and the actions. If you need to change just some
   behaviours or you want to extend an existing facade, you can do that
   by sub-classing it and using it instead of the original one.

      **Example**: you want to expose your new action from a facade that
      is already used in your tests :math:`\to` *you sub-class the
      facade and add the new method that calls the new action. Now you
      will use your new extended version instead of the base one.*

-  **Add new input classes**: you can create new input classes that
   generate the JSON input for the actions in your own ways.

      **Example**: you have a collection of JSON files in a your test
      data folder and you want to use them as input :math:`\to` *you
      sub-class the file-based input class and you allow access to your own
      input files through keywords which refer to the command you
      are calling (e.g., ``MyFileJsonInput('scan')``).*

-  **Customise the init procedure (and the wrappers)**: the
   initialisation procedure explained in :doc:`./getting_started` file can be
   customised:

   -  sub-classing various configuration, validation, reader and factory
      classes and injecting them in the builder, so they will be used
      instead of the original one;
   -  creating an overall new initialisation procedure (maybe
      sub-classing the existing one, maybe creating a new one from
      scratch).

   Customising the initialisation procedure may be a necessary step if
   you want to replace, modify and/or extend what makes the test harness
   ``structure`` (the ``TelescopeWrapper``, the subsystem wrappers,
   etc.).

      **Example**: you want to implement a your own wrapper, which
      should be activated only if a new configuration flag is used
      :math:`\to` *you add the needed parameters in the YAML file and
      you extend the configuration classes and the reader to support it,
      (optionally) you subclass the input validator and you inject it
      into the initialisation builder, you subclass the wrapper of the
      subsystem you want to replace and to use it in your test harness
      you subclass the factory that produces the wrappers and override
      the method that creates the wrapper for that subsystem.*

How you will be able to extend this test harness in the future
--------------------------------------------------------------

In the future, the test harness will be more flexible and will not be
centered strictly on the TMC-X integration tests in Mid.

Probably, there will be a generic *core*, made by an elastic
infrastructure, the action mechanism, some generic and parametric
actions, the input classes and a generic and flexible configuration and
initialisation mechanism. Then, partially through extension, partially
through configuration, you will be able to adapt the test harness to
your needs.

Please contact *Emanuele Lena*, *Giorgio Brajnik* and/or *Verity Allan*
if you think this test harness can be useful for your tests, if you have
any questions, proposals or feedback. Of course, you are more than
welcome also if you want to contribute to the development of this test
harness.

Test Harness applications examples
----------------------------------

Here there follows some (not necessarily exhaustive) examples of how this
test harness has been used.

In September 2024, this test harness was used for the new set of
this test harness is used for the new set of
`TMC-CSP Mid integration
tests <https://gitlab.com/ska-telescope/ska-tmc/ska-tmc-mid-integration/-/merge_requests/234>`__,
to test the subarray-related operations on
the TMC (with a production CSP and emulated SDP and Dishes).

In October 2024, this test harness was used for 
`this new set of TMC system tests <https://gitlab.com/ska-telescope/ska-sw-integration-testing/-/merge_requests/7/>`__,
which run in an environment where TMC, CSP, SDP and Dishes are production
subsystems.


