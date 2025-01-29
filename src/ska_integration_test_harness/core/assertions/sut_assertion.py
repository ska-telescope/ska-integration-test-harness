"""A base class for an assertion on the SUT."""

import abc


class SUTAssertion(abc.ABC):
    """A base class for an assertion on the SUT.

    This class is the base class for the
    :py:mod:`ska_integration_test_harness.core.assertions` framework
    and it provides an empty shell for defining a generic assertion on the SUT.

    An assertion is a verification of some kind of wide condition, probably
    made by many lower level assertions grouped together, eventually
    event-based. An assertion:

    - may need a setup phase to prepare the assertion for the verification
      (method :py:meth:`setup`, optional extension point)
    - must have a verification phase to verify the assertion
      (method :py:meth:`verify`, required implementation)
    - should have a description of the assumption that the assertion verifies
      (method :py:meth:`describe_assumption`, required implementation)

    **How to use an assertion as an end user**: An end user can use assertions
    calling in sequence the :py:meth:`setup` method to prepare the assertion
    for the verification (and ensure that the assertion is in a clean state)
    and then the :py:meth:`verify` method to verify the assertion.

    **How to extend this class**: This class is basically just an empty
    skeleton, so subclass it and implement compulsory
    :py:meth:`verify` and :py:meth:`describe_assumption` methods. Optionally,
    you can also override the :py:meth:`setup` method.

    .. code-block:: python

        import logging
        from ska_integration_test_harness.core.assertions import SUTAssertion

        class MyAssertion(SUTAssertion):

            def setup(self):
                super().setup()

                # your setup code here (e.g., subscribe to events)

            def verify(self):
                # your verification code here

            def describe_assumption(self):
                return "My assertion description"

        assertion = MyAssertion()
        assertion.setup()

        logging.info(f"Verifying: {assertion.describe_assumption()}")
        assertion.verify()

        # an assertion can be reused multiple times, given that you call
        # the setup method before each verification
        assertion.setup()
        assertion.verify()
    """

    def setup(self):
        """Set up the assertion (**optional extension point**).

        This method should be called before the verification procedure.
        It should be used to prepare the instance to a new, clear verification
        procedure (e.g., subscribe to events, reset some state, etc.).
        By default, no setup is done.

        **HOW TO EXTEND**: override this method in your subclass to implement
        the setup phase. Always call the superclass method when overriding
        this method. Some good practices if you want to override are:

        - make it be idempotent
        - inside this method, clear and setup all the subscriptions you
          need for the verification procedure
        - in the docstring of the method, specify the resources that
          are set up (and briefly recap also what is done by superclasses,
          potentially referencing their method docstring)
        """

    @abc.abstractmethod
    def verify(self) -> None:
        """Verify the assertion..

        This method should be called to verify the assertion.
        It should be implemented to verify the assertion and raise
        an ``AssertionError`` if the assertion fails.

        **HOW TO EXTEND**: override this method in your subclass to implement
        the verification procedure. Always call the superclass method when
        overriding this method. Some good practices when you implement are:

        - make it be idempotent
        - inside this method, make all your assertions and fail if
          something is wrong
        - the verification can be a blocking operation that waits for
          some event to happen.
          If it is consider :py:class:`SUTAssertionWTimeout`
        - if you fail, produce a meaningful error message
        - in the docstring of the method, specify the resources that
          are verified (and briefly recap also what is done by superclasses,
          potentially referencing their method docstring)

        :raises AssertionError: if the assertion fails
        """  # noqa: DAR402

    @abc.abstractmethod
    def describe_assumption(self) -> str:
        """Describe assertion's assumption (**required implementation**).

        This method should return a string that describes briefly
        what the assertion verifies. This is useful to understand
        the context of the assertion and to give a semantic meaning to it.

        **HOW TO EXTEND**: override this method in your subclass to implement
        the description of the assumption. Return a string that describes
        briefly what you are verifying. The string may be single line, or
        multiline if needed. If you are extending from a subclass, consider
        to call the superclass method and append your description to it
        (if you think it is useful).

        :return: the description of the assumption
        """

    def __str__(self):
        return self.describe_assumption()
