SKA Integration Test Harness
=============================

As of **March 2025**, this repository contains two separate components:

1. The Monolith TMC Test Harness
--------------------------------

This is a test harness for **testing TMC** in both **Mid** and **Low**.

It serves as an interface for using TMC together with controlled subsystems:  
**CSP, SDP, Dishes, and MCCS**. It is referred to as a *Monolith* because it is  
a single Python library, specifically designed for TMC, containing all the  
necessary logic for handling various testing scenarios:

- It can interface with **TMC-Mid** as well as **TMC-Low**.
- In **Mid**, it can connect to both **production** and **emulated** CSP, SDP,  
  and Dishes.
- In **Low**, it interfaces with **emulated** CSP, SDP, and MCCS.

In all cases, interactions are piloted by **TMC**.

If you need to use this test harness, you can attach to version ``0.3.0`` of  
the ``ska-tmc-integration-test-harness`` package. Version ``0.4.0`` also  
supports it but includes additional components for **Test Harness as a  
Platform**.

In the long term, this monolithic test harness will be relocated elsewhere.

For documentation on the **Monolithic TMC Test Harness**, refer to the  
:doc:`this section of the documentation <getting_started>`.


2. The Test Harness as a Platform
---------------------------------

This is a collection of **building blocks** designed to help you create a  
**custom test harness** for integration testing your specific SKA subsystem.  
It is a **generic framework** consisting of:

- A **core package** that provides fundamental building blocks for creating  
  a test harness.
- **Common extensions** that implement standard SKAO use cases (e.g. sending  
  **Tango Long Running Commands** and synchronising after execution).

You can take these **building blocks**, use them as-is, or extend them to  
develop your own **customised** test harness.

More details about this approach can be found in  
:doc:`this section of the documentation <ith_as_a_platform>`.

**IMPORTANT NOTE**:  
As of **March 2025 (version 0.4.0)**, the **Test Harness as a Platform**  
includes only a few building blocks, but it is actively growing.  
In the long term, this will be the **main focus** of the repository, and we  
hope many teams will find it useful and adopt it. For this reason,  
:ref:`it may still evolve based on your specific but generalisable  
needs <development_process>`. If you are interested in expanding the  
**ITH as a Platform**, please **get in touch with us**  
(*Giorgio Brajnik*, *Emanuele Lena*, *Verity Allan*).  

Let us know your needs, and we will do our best to accommodate them.  
The sooner you reach out, the greater your influence on the development  
process.  



.. toctree::
   :maxdepth: 2
   :caption: Contents:

   getting_started
   architecture_overview
   extend_and_apply_ith
   api/index
   ith_as_a_platform 
   platform-concepts/index
   api/core2_api
   api/extension2_api
