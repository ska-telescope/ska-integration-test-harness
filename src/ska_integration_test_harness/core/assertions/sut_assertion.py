"""A base class for an assertion on the SUT."""

import abc
from typing import SupportsFloat

# TODO: ma


class SUTAssertion(abc.ABC):
    """A base class for an assertion on the SUT.

    This class represents an assertion on the SUT. A generic assertion on the
    SUT:

    - is the verification of some kind of wide condition, probably made
      by many lower level assertions grouped together;
    - it may (optionally) need a setup phase;
    - has a semantic description that explains what the assertion is about.

    We think of this class because the SUT is a complex system made
    of multiple components, so it may be useful to have a way to
    group together many lower level assertions into something more
    abstract and meaningful (e.g., sometimes we want to write things as
    "the SUT is in a X state", but the "being in a X state" may be
    composed by many lower level assertions involving many Tango devices).
    Moreover, in this context many assertions are event based, so defining
    the existence of a setup phase is useful.

    **How to use an assertion as an end user**: An end user can use assertions
    calling in sequence the :py:meth:`setup` method to prepare the assertion
    for the verification (and ensure that the assertion is in a clean state)
    and then the :py:meth:`verify` method to verify the assertion. Example:

    .. code-block:: python
        assertion = MyAssertion()
        assertion.setup()
        logging.info(f"Verifying: {assertion.describe_assumption()}")
        assertion.verify()

    **How to extend this class**: This class is basically just an empty
    skeleton, so subclass it and implement compulsory
    :py:meth:`verify` and :py:meth:`describe_assumption` methods. Optionally,
    you can also override the :py:meth:`setup` method.
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
          are set up (and briefly recap also what is done by superclasses)
        - if you think the method may be extended by your own subclasses,
          put in the docstring a reference to this method docstring
          (e.g., TODO: add example)
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
          are verified (and briefly recap also what is done by superclasses)
        - if you think the method may be extended by your own subclasses,
          put in the docstring a reference to this method docstring
          (e.g., TODO: add example)

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

    def error_message(self, details: str = "") -> str:
        """Produce the error message that describes the failure.

        You can override this method if you want to customise the error
        message produced by the assertion further, but probably you should
        prefer to override just the :py:meth:`describe_assumption` method
        and use the ``details`` parameter to provide more context to the
        failure.

        :param details: the details of the error message
        """
        error_msg = f"{self.describe_assumption()} - FAILED"
        if details:
            error_msg += f": {details}"
        return error_msg

    def fail(
        self, details: str = "", exception: Exception | None = None
    ) -> None:
        """Fail the assertion with an error message.

        This method is used to fail the assertion with an error message. You
        can customise the error message by providing a
        string in the ``details`` and you can also provide an exception
        that caused the failure. Call it when you want to raise a failure
        in your verification procedure.

        You can override it if you want to raise something different.

        :param details: the details of the error message
        :raises AssertionError: always
        """
        if exception:
            raise AssertionError(self.error_message(details)) from exception

        raise AssertionError(self.error_message(details))


class SUTAssertionWTimeout(SUTAssertion, abc.ABC):
    """A base class for an assertion on the SUT with a timeout.

    This class represents an assertion on the SUT that can be verified
    within a timeout. It extends the :py:class:`SUTAssertion` class by
    adding the possibility to specify a timeout for the verification.

    The timeout can be initialised in the constructor or set later with
    :py:meth:`reset_timeout`. By default, the timeout is 0.0 seconds, but you
    can set any objects that supports the float interface.

    If you extend this class, please check the documentation of the
    base class :py:class:`SUTAssertion` to see how to extend it properly.
    """

    def __init__(self, timeout: SupportsFloat = 0.0):
        """Initialise the assertion with a timeout.

        :param timeout: the timeout in seconds (default is 0.0)
        """
        self.timeout = timeout

    def reset_timeout(self, timeout: SupportsFloat = 0.0):
        """Reset the timeout to a new value.

        :param timeout: the new timeout in seconds (default is 0.0)
        """
        self.timeout = timeout
