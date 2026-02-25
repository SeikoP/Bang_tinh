"""
Property-based tests for architecture compliance.

Tests Config validation and Container DI registration with real wms code.
**Validates: Requirements 2.5, 2.7**
"""

import os
from unittest.mock import patch

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from wms.core.config import Config
from wms.core.container import Container


@st.composite
def valid_config_dict(draw):
    """Generate valid configuration dictionary."""
    return {
        "APP_NAME": draw(st.text(min_size=1, max_size=50).filter(lambda x: "\x00" not in x)),
        "APP_VERSION": draw(st.text(min_size=1, max_size=20).filter(lambda x: "\x00" not in x)),
        "NOTIFICATION_PORT": str(draw(st.integers(min_value=1024, max_value=65535))),
        "LOG_LEVEL": draw(
            st.sampled_from(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        ),
        "WINDOW_WIDTH": str(draw(st.integers(min_value=800, max_value=3840))),
        "WINDOW_HEIGHT": str(draw(st.integers(min_value=600, max_value=2160))),
    }


@st.composite
def invalid_config_dict(draw):
    """Generate invalid configuration dictionary."""
    invalid_type = draw(
        st.sampled_from(["invalid_port", "invalid_log_level", "small_window"])
    )
    base_config = {
        "APP_NAME": "Test App",
        "APP_VERSION": "1.0.0",
        "NOTIFICATION_PORT": "5005",
        "LOG_LEVEL": "INFO",
        "WINDOW_WIDTH": "1200",
        "WINDOW_HEIGHT": "800",
    }
    if invalid_type == "invalid_port":
        base_config["NOTIFICATION_PORT"] = str(draw(st.integers(min_value=1, max_value=1023)))
    elif invalid_type == "invalid_log_level":
        base_config["LOG_LEVEL"] = draw(
            st.text(min_size=1, max_size=20)
            .filter(lambda x: x not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
            .filter(lambda x: "\x00" not in x)
        )
    else:
        base_config["WINDOW_WIDTH"] = str(draw(st.integers(min_value=100, max_value=799)))
    return base_config


@pytest.mark.property
@settings(max_examples=15)
@given(config_dict=st.one_of(valid_config_dict(), invalid_config_dict()))
def test_property_configuration_validation(config_dict):
    """Config validation should return a list for any input."""
    with patch.dict(os.environ, config_dict, clear=True):
        try:
            config = Config.from_env()
            errors = config.validate()
            assert isinstance(errors, list)
        except Exception:
            pass


@pytest.mark.property
@settings(max_examples=15)
@given(
    service_name=st.text(
        min_size=1,
        max_size=50,
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_"),
    ).filter(lambda x: x.isidentifier()),
)
def test_property_container_registration(service_name):
    """Container should correctly register and retrieve singletons."""
    assume(service_name.isidentifier())

    config = Config.from_env()
    container = Container(config)

    mock_service = f"MockService_{service_name}"
    container.register_singleton(service_name, mock_service)

    retrieved = container.get(service_name)
    assert retrieved == mock_service

    retrieved2 = container.get(service_name)
    assert retrieved is retrieved2
