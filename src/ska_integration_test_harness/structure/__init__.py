"""A collection of wrappers for various system components.

``TelescopeWrapper`` is the main entry point for the telescope system.

Right now, it exposes the following sub-systems (through a wrapper for each):

- TMC
- SDP
- CSP
- Dishes

All the subsystems wrappers are represented by abstract classes, so you can
create your own implementation for each one (e.g., an implementation that
points to the devices of a real subsystem, or an implementation that points
to the devices of an emulated subsystem).
"""
