ITH as a Platform: Introduction
================================

The Integration Test Harness (ITH) is evolving from a monolithic structure
to a versatile platform. This transformation aims to provide generic tools
for integration testing any Tango-based system within the SKA project.

In this document you can find an overview of the general ideas behind the
ITH as a Platform, the structure of the platform and the development process.

.. contents:: Table of Contents
   :local:
   :depth: 2

For a more technical detailed explanation of the building blocks and how to
use them, refer to the section: :doc:`platform-concepts/index`.

From a Monolith to a Platform
--------------------------------

Before the ``0.4.0`` release, the ITH was a **Monolithic Test Harness**
specifically designed for testing TMC in both Mid and Low environments.
As you can still see in other sections of the documentation,
the *TMC Monolith* is a set of facades, wrappers and actions to test TMC,
integrated with CSP, SDP, the Dishes and MCCS in both Mid and Low
environments. While this have been a solid starting point, the ITH
is evolving further.

In the long term, the ITH should be seen as a **platform** that provides a set
of **generic tools to integration test potentially any SKA Tango-based system**,
covering a wide range of use cases within the SKA project. To achieve this,
we plan to gradually re-write the ITH to follow the *"as a Platform"* approach,
as described in the book `Team Topologies <https://teamtopologies.com/>`_.

Essentially, *"as a Platform"* means the ITH should be considered a
set of shared tools, services and capabilities that all teams can use
to work more effectively and efficiently. In this specific context, the
**ITH as a Platform** should be considered an **Object-Oriented Framework**
that all teams can use, compose and extend to create their own integration
test harnesses for their specific System Under Test (SUT). What sets the
*as a Platform* approach apart from the monolith is that:

1. **teams will be able to self-service** and set up an instance
   of the ITH for their SUT without requiring extensive support;
2. the ITH will provide an **abstraction of complexity**, both in terms of
   building blocks that enable complex operations with minimal code, and by
   offering a general structure that can be extended and customised;
3. through a **continuous feedback loop**, the ITH will evolve according
   to the needs of the teams (by satisfying common needs with new built-in
   blocks, while also ensuring the ITH is elastic enough where required);
4. the ITH will focus on **Developer Experience (DX)**, prioritising ease
   of use, writing new code, creating new tests, and debugging.

The 2+1 Layers Structure
--------------------------------

The ITH as a Platform will be structured in **2+1 layers**:

1. At the centre, there is the **Core** layer, which is the heart of the
   ITH as a Platform. The Core layer provides the basic building blocks
   to create wrappers, configurations, actions, etc. By itself,
   the Core will be *highly generic*, and it is being designed so that it
   does not assume the SUT is a telescope or an SKA subsystem. Instead, it
   will be *versatile enough to integration test any Tango-based system*.
   The Core layer will be the most stable and thoroughly unit-tested part
   of the ITH as a Platform. It will reside in the
   `ska-integration-test-harness <https://gitlab.com/ska-telescope/ska-integration-test-harness/>`_
   repository and will be distributed as a Python package of the same name.
   In the short to medium term, *development and maintenance are handled by
   Emanuele Lena, Giorgio Brajnik, and Verity Allan*. In the long term,
   the maintenance and development strategy may involve a wider group of
   contributors.

2. Surrounding the Core is the **Customisation** layer, where building blocks
   are composed to create specific actions, assertions, configurations,
   etc., tailored to integration testing one or more specific subsystems.
   Unlike the Core, the Customisations will: 1) be *developed and maintained
   by individual teams* as needed, 2) be *decentralised* (each team will
   store their extensions in appropriate locations, *likely alongside
   their tests*), and 3) be *dynamic, flexible and easily adaptable* to
   changes in the SUT.

Additionally, there is the **Common Extensions** layer, which comprises
extensions that may be *useful for multiple teams across SKAO
and are not tied to a specific SUT*. Common Extensions are intended as building blocks generic
enough for almost any SKA project. However, as they assume the SUT is part
of a telescope within the SKA context, they cannot be included in the
Core layer. An example might be a command call action capable of handling
Long Running Commands (LRC) in line with SKA conventions; another
(more complex) example could be a framework for managing the lifecycle
of one or more Tango Subarray devices in a test environment
(see the next section for more details). Currently, the
Common Extensions layer will be distributed alongside the Core in
the `ska-integration-test-harness <https://gitlab.com/ska-telescope/ska-integration-test-harness/>`_.
Contributions to this layer are welcome, provided they meet the
Core layer’s quality and unit-testing standards.

The **Tests** can potentially use all the layers according
to the needs. If the needs are simple and generic enough the test can just
directly use the Core and Common Extensions layers. If the needs are more
specific, a Customisation Layer can be created to encapsulate the specific
logic for the SUT and for the testing context.


ITH Components and Building Blocks
------------------------------------

The ITH as a Platform consists of a set of building blocks designed to
address common needs across teams. The ITH as a Platform is still in
development, so its building blocks are not yet fully defined. However,
based on our experience with TMC and our collaboration with the CREAM
team, we have identified the following key building blocks:

- **Actions and Assertions**: Basic building blocks to define structured
  interactions with the SUT and the necessary synchronisation logic
- **Wrappers**: A means to group sets of Tango devices representing a
  subsystem and encapsulate the logic for interacting with them
- **Configurations**: A method for dynamically setting up a correct
  Test Harness instance according to the specific SUT being tested

Potential additional concepts may include:

- **Wrappers for Emulators**: Structured methods for interacting with emulators
- **Inputs**: Defining input data for actions
- **Command Factories**: Systematic generation of actions for interacting
  with the SUT
- **Setup and Reset Procedures**: Systematic methods for setting up and
  resetting the entire SUT or its parts

An additional element, not strictly a building block but worth mentioning,
is the **Tango Event Tracer** and its assertions. This is a fundamental
mechanism provided by
`SKA Tango Testing <https://developer.skao.int/projects/ska-tango-testing/en/latest/>`_,
which serves as the basis for the ITH as a Platform.


.. _development_process:

Development Process
-------------------

The development of this new structure will be **incremental** and **driven by 
the needs of the teams**. This means that:

- The **ITH as a Platform** will not be released as a whole but rather 
  incrementally, as new building blocks are developed, unit tested, 
  documented, tested by teams, reviewed, and merged.
- The development process will be **guided by the needs of the teams** that 
  choose to collaborate with us and adopt (some of) the building blocks we 
  develop.  

  If you are interested in using the **ITH as a Platform**, please **get in 
  touch with us** (*Giorgio Brajnik*, *Emanuele Lena*, *Verity Allan*).  
  Let us know your needs, and we will do our best to accommodate them.  
  The sooner you reach out, the greater your influence on the development 
  process.

Below is a diary of the development process.


1. **March 2025**: Test Harness as a Platform Foundation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This first increment introduces:
   
- **For the Core Layer**: A framework for representing interactions with the  
  SUT as **Actions** and **Assertions**.
- **For the Common Extensions Layer**: An action to send **Tango Long Running  
  Commands**, synchronise on their completion, and fail if any errors are  
  reported in the events.

This increment was developed in collaboration with the **CREAM Team** to  
provide suitable (but still generic) building blocks for  
`CSP.LMC testing <https://jira.skatelescope.org/browse/CT-1519>`_.
   
Documentation and References:
   
- **Examples and user documentation**: :doc:`./platform-concepts/actions`
- **API documentation**:

  - :py:mod:`ska_integration_test_harness.core.actions`  
  - :py:mod:`ska_integration_test_harness.extensions.lrc`  
- **ITH Merge Request**:

  - `MR 13 <https://gitlab.com/ska-telescope/ska-integration-test-harness/-/merge_requests/13>`_  
- **Jira tickets**:

  - `SST-1018 (generic ticket for the first increment of the ITH) <https://jira.skatelescope.org/browse/SST-1018>`_  
  - `SST-1019 (CREAM/CSP.LMC collaboration) <https://jira.skatelescope.org/browse/SST-1019>`_  
  - **CREAM Team tickets**:

    - `SP-4457 <https://jira.skatelescope.org/browse/SP-4457>`_  
    - `CT-1519 <https://jira.skatelescope.org/browse/CT-1519>`_  


2. **To Be Released**: Subarray Management and Reset Framework
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This upcoming increment (not yet released) introduces:
   
- **For the Common Extensions Layer**: Actions and tools for interacting  
  with a **Subarray-based system** (i.e., a system with one or more Tango  
  subarray devices that implement the SKA Observation State Machine).  

  The interaction will likely include an action to reset the **Subarray** to  
  a given **Observation State**, starting from any other state.

At present, this increment exists only as a draft.  

**If you are interested in this, please get in touch with us.**
