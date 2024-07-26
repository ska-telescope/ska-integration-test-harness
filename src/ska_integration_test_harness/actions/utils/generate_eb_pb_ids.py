"""Given a JSON input, generate the EB and PB IDs for the subarray."""

import logging
import re
from datetime import datetime

from ska_ser_logging import configure_logging

from ska_integration_test_harness.inputs.dict_json_input import DictJSONInput
from ska_integration_test_harness.inputs.json_input import JSONInput

configure_logging(logging.DEBUG)
LOGGER = logging.getLogger(__name__)
EB_PB_ID_LENGTH = 15


def generate_id(id_pattern: str) -> str:
    """
    Generate a time-based unique id.

    :param id_pattern: the string pattern as to how the unique id should
        be rendered.
        e.g :
            input: eb-mvp01-********-*****
            output: eb-mvp01-35825416-12979

    :return: the id rendered according to the requested pattern
    """
    prefix, suffix = re.split(r"(?=\*)[\*-]*(?<=\*)", id_pattern)
    id_pattern = re.findall(r"(?=\*)[\*-]*(?<=\*)", id_pattern)[0]
    length = id_pattern.count("*")
    assert length <= EB_PB_ID_LENGTH
    LOGGER.info("<SB or PB ID >Length: %s", length)
    timestamp = str(datetime.now().timestamp()).replace(".", "")
    sections = id_pattern.split("-")
    unique_id = ""
    sections.reverse()
    for section in sections:
        section_length = len(section)
        section_id = timestamp[-section_length:]
        timestamp = timestamp[:-section_length]
        if unique_id:
            unique_id = f"{section_id}-{unique_id}"
        else:
            unique_id = section_id
    return f"{prefix}{unique_id}{suffix}"


def generate_eb_pb_ids(input_json: JSONInput) -> JSONInput:
    """Given a JSON input, generate the EB and PB IDs for the subarray.

    :param input_json: input to use as a starting point to update the values.

    :return: the input JSON with the EB and PB IDs updated.
    """
    input_as_dict = input_json.get_json_dict()
    input_as_dict["sdp"]["execution_block"]["eb_id"] = generate_id(
        "eb-mvp01-********-*****"
    )
    for pb in input_as_dict["sdp"]["processing_blocks"]:
        pb["pb_id"] = generate_id("pb-mvp01-********-*****")

    return DictJSONInput(input_as_dict)
