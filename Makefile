# Include Python support
include .make/python.mk

# include core make support
include .make/base.mk

# include release support
# -include .make/release.mk

PYTHON_TEST_MARK ?= "not experiments"## The mark to use when running tests
# (by default, we don't run the experiments tests)

PYTHON_TEST_NAME ?= "" ## The name of the test to run
# (by default, we run all tests, but you can use it for filtering)

PYTHON_VARS_AFTER_PYTEST += -m $(PYTHON_TEST_MARK)
PYTHON_VARS_AFTER_PYTEST += $(if $(PYTHON_TEST_NAME),-k $(PYTHON_TEST_NAME),)
