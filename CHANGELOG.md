# Changelog

## v0.3.0 (to be released)

- **SST-1012**: make the ITH to support TMC-X in Low integration tests.

## v0.2.4 (11th November 2024)

- **SST-982**: make various actions support the check for the LRC completion
  (pt. 2 - also dishes load configuration command).

## v0.2.3 (9th November 2024)

- **SST-982**: make various actions support the check for the LRC completion.

## v0.2.2 (14th November 2024)

- **SST-981**: small fix from the previous release, the observation state
  we support to reach is "RESTARTING", not "RESETTING". RESETTING is not
  (yet) supported.

## v0.2.1 (5th November 2024)

- **SST-981**: observation state reset permits to reach ABORTING, ABORTED
  and RESETTING states.
- **SST-982**: actions default timeout is now configurable, and also
  the timeout is now specifiable in the action call from the TMC facade.

## v0.2.0 (25th October 2024)

- **SST-975**: Add a mechanism to console log the Tango device versions
  when the tests are running.
- **SST-975**: Improvements in the documentation, creation of a new unique
  facade for TMC + other minor internal improvements.

## v0.1.2 (14th October 2024)

- **SAH-1597**: Removed condition applied to check CSP subarray off state.

## v0.1.1 (11th September 2024)

- **SP-4375**: small improvements to the README and to the API documentation

## v0.1.0 (9th September 2024)

- **SP-4375**: initial release (test harness for TMC-CSP in Mid, with some
  initial generalisations for other use cases always for TMC-X in Mid)
