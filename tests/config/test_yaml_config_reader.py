"""Unit tests for YAMLConfigurationReader class."""

import pytest
import yaml
from assertpy import assert_that

from ska_integration_test_harness.config.reader.yaml_config_reader import (
    YAMLConfigurationReader,
)


class TestYAMLConfigurationReader:
    """Unit tests for YAMLConfigurationReader class.

    Tests for YAMLConfigurationReader that validate the ability to correctly
    load and parse various configurations (TMC, CSP, SDP, Dishes)
    from a YAML file.
    Ensures that missing required fields are handled by setting them to None.
    """

    CONFIG_DATA_DIR = "tests/config_examples"

    @pytest.fixture(scope="class")
    def valid_yaml_path(self) -> str:
        """Path to a valid YAML config file."""
        return f"{self.CONFIG_DATA_DIR}/valid_test_harness_config.yaml"

    @pytest.fixture(scope="class")
    def missing_tmc_section_yaml_path(self) -> str:
        """Path to a YAML config file with a missing subsystem section.

        :return: The path to the YAML configuration file with
            missing TMC section.
        """
        return f"{self.CONFIG_DATA_DIR}/missing_tmc_section.yaml"

    @pytest.fixture(scope="class")
    def missing_tmc_centralnode_name_yaml_path(self) -> str:
        """Path to a YAML config file with a missing required field."""
        return f"{self.CONFIG_DATA_DIR}/missing_tmc_centralnode_name.yaml"

    @pytest.fixture(scope="class")
    def invalid_yaml_path(self) -> str:
        """Path to an invalid YAML config file."""
        return f"{self.CONFIG_DATA_DIR}/not_valid_yaml.yaml"

    def test_constructor_initialisation_does_not_crash(
        self, valid_yaml_path: str
    ) -> None:
        """A reader is initialised with a valid YAML file and does not crash.

        :param valid_yaml_path: Path to the valid YAML configuration file.
        """
        reader = YAMLConfigurationReader()
        reader.read_configuration_file(valid_yaml_path)
        assert_that(reader).is_not_none()

    def test_constructor_raises_file_not_found_error(self) -> None:
        """When the file does not exist, a FileNotFoundError is raised."""
        reader = YAMLConfigurationReader()
        with pytest.raises(FileNotFoundError):
            reader.read_configuration_file("non_existent_file")

    def test_constructor_raises_yaml_error(
        self, invalid_yaml_path: str
    ) -> None:
        """When the file is not a valid YAML file, a yaml.YAMLError is raised.

        :param invalid_yaml_path: Path to the invalid YAML configuration file.
        """
        reader = YAMLConfigurationReader()
        with pytest.raises(yaml.YAMLError):
            reader.read_configuration_file(invalid_yaml_path)

    def test_get_tmc_configuration_loads_correctly(
        self, valid_yaml_path: str
    ) -> None:
        """Load TMC config parses the file and returns the expected values.

        :param valid_yaml_path: Path to the valid YAML configuration file.
        """
        reader = YAMLConfigurationReader()
        reader.read_configuration_file(valid_yaml_path)

        tmc_config = reader.get_tmc_configuration()

        assert_that(tmc_config.is_emulated).is_false()
        assert_that(tmc_config.centralnode_name).is_equal_to(
            "ska_mid/tm_central/central_node"
        )
        assert_that(tmc_config.tmc_subarraynode1_name).is_equal_to(
            "ska_mid/tm_subarray_node/1"
        )
        assert_that(tmc_config.tmc_csp_master_leaf_node_name).is_equal_to(
            "ska_mid/tm_leaf_node/csp_master"
        )
        assert_that(tmc_config.tmc_csp_subarray_leaf_node_name).is_equal_to(
            "ska_mid/tm_leaf_node/csp_subarray01"
        )
        assert_that(tmc_config.tmc_sdp_master_leaf_node_name).is_equal_to(
            "ska_mid/tm_leaf_node/sdp_master"
        )
        assert_that(tmc_config.tmc_sdp_subarray_leaf_node_name).is_equal_to(
            "ska_mid/tm_leaf_node/sdp_subarray01"
        )
        assert_that(tmc_config.tmc_dish_leaf_node1_name).is_equal_to(
            "ska_mid/tm_leaf_node/d0001"
        )
        assert_that(tmc_config.tmc_dish_leaf_node2_name).is_equal_to(
            "ska_mid/tm_leaf_node/d0036"
        )
        assert_that(tmc_config.tmc_dish_leaf_node3_name).is_equal_to(
            "ska_mid/tm_leaf_node/d0063"
        )
        assert_that(tmc_config.tmc_dish_leaf_node4_name).is_equal_to(
            "ska_mid/tm_leaf_node/d0100"
        )

    def test_get_csp_configuration_loads_correctly(
        self, valid_yaml_path: str
    ) -> None:
        """Load CSP config parses the file and returns the expected values.

        :param valid_yaml_path: Path to the valid YAML configuration file.
        """
        reader = YAMLConfigurationReader()
        reader.read_configuration_file(valid_yaml_path)

        csp_config = reader.get_csp_configuration()

        assert_that(csp_config.is_emulated).is_false()
        assert_that(csp_config.csp_master_name).is_equal_to(
            "mid-csp/control/0"
        )
        assert_that(csp_config.csp_subarray1_name).is_equal_to(
            "mid-csp/subarray/01"
        )

    def test_get_sdp_configuration_loads_correctly(
        self, valid_yaml_path: str
    ) -> None:
        """Load SDP config parses the file and returns the expected values.

        :param valid_yaml_path: Path to the valid YAML configuration file.
        """
        reader = YAMLConfigurationReader()
        reader.read_configuration_file(valid_yaml_path)

        sdp_config = reader.get_sdp_configuration()

        assert_that(sdp_config.is_emulated).is_true()
        assert_that(sdp_config.sdp_master_name).is_equal_to(
            "mid-sdp/control/0"
        )
        assert_that(sdp_config.sdp_subarray1_name).is_equal_to(
            "mid-sdp/subarray/01"
        )

    def test_get_dishes_configuration_loads_correctly(
        self, valid_yaml_path: str
    ) -> None:
        """Load Dishes config parses the file and returns the expected values.

        :param valid_yaml_path: Path to the valid YAML configuration file.
        """
        reader = YAMLConfigurationReader()
        reader.read_configuration_file(valid_yaml_path)

        dishes_config = reader.get_dish_configuration()

        assert_that(dishes_config.is_emulated).is_true()
        assert_that(dishes_config.dish_master1_name).is_equal_to(
            "ska001/elt/master"
        )
        assert_that(dishes_config.dish_master2_name).is_equal_to(
            "ska036/elt/master"
        )
        assert_that(dishes_config.dish_master3_name).is_equal_to(
            "ska063/elt/master"
        )
        assert_that(dishes_config.dish_master4_name).is_equal_to(
            "ska100/elt/master"
        )

    def test_get_tmc_configuration_sets_missing_field_to_none(
        self, missing_tmc_centralnode_name_yaml_path: str
    ) -> None:
        """Load TMC config when a field is missing sets the field to None.

        :param missing_tmc_centralnode_name_yaml_path: Path to the YAML
            configuration file with a missing required field.
        """
        reader = YAMLConfigurationReader()
        reader.read_configuration_file(missing_tmc_centralnode_name_yaml_path)
        tmc_config = reader.get_tmc_configuration()

        # Verify that the missing field is set to None
        assert_that(tmc_config.centralnode_name).is_none()

    def test_get_tmc_configuration_returns_none_when_missing_section(
        self, missing_tmc_section_yaml_path: str
    ) -> None:
        """Load TMC config when the TMC section is missing returns None.

        :param missing_tmc_section_yaml_path: Path to the YAML configuration
            file with a missing TMC section.
        """
        reader = YAMLConfigurationReader()
        reader.read_configuration_file(missing_tmc_section_yaml_path)
        tmc_config = reader.get_tmc_configuration()

        assert_that(tmc_config).is_none()
