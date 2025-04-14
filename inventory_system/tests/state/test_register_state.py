import functools

# --- Test handle_registration_with_email ---
from unittest.mock import AsyncMock, MagicMock, PropertyMock, create_autospec

import pytest
import reflex_local_auth

from inventory_system import routes
from inventory_system.constants import DEFAULT_PROFILE_PICTURE
from inventory_system.models.user import UserInfo
from inventory_system.state.register_state import (
    CustomRegisterState,
)


@pytest.fixture
def mock_state(mocker):
    """Fixture to create a mocked CustomRegisterState instance."""
    mocker.patch("inventory_system.state.register_state.load_user_data")
    # Patch logger once and capture the mock
    mock_audit_logger = mocker.patch(
        "inventory_system.state.register_state.audit_logger"
    )
    mocker.patch("reflex.toast", new_callable=MagicMock)
    mocker.patch("reflex.redirect", new_callable=MagicMock)
    mocker.patch("asyncio.sleep", new_callable=AsyncMock)

    # Mock the session context manager and its methods
    mock_session = MagicMock()
    mock_session_instance = MagicMock()
    mock_session.return_value.__enter__.return_value = mock_session_instance
    mocker.patch("reflex.session", mock_session)

    # Mock the base class handle_registration
    mocker.patch(
        "reflex_local_auth.RegistrationState.handle_registration",
        return_value=None,  # Base method doesn't yield/return typically
    )
    # Patch the inherited error_message at the base class level
    mocker.patch(
        "reflex_local_auth.RegistrationState.error_message",
        new_callable=PropertyMock,  # Allows setting/getting if needed
        return_value="",  # Initial value
    )

    # Mock router/session attributes if needed
    mock_router = MagicMock()
    mock_router.session.client_ip = "127.0.0.1"

    # Create state instance and attach mocks
    state = CustomRegisterState()
    # Use object.__setattr__ to bypass Reflex State's __setattr__ logic for router
    object.__setattr__(state, "router", mock_router)
    # Use object.__setattr__ also for test-specific attributes
    object.__setattr__(state, "mock_session_instance", mock_session_instance)
    # Treat inherited 'error_message' as a local var for testing
    # state.vars["error_message"] = None # Remove this attempt

    # Return state and logger mock
    return state, mock_audit_logger


@pytest.fixture
def valid_form_data():
    """Fixture for valid registration form data."""
    return {
        "username": "testuser",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "email": "test@example.com",
        "id": "12345",
    }


# --- Test reset_form_state ---


def test_reset_form_state(mock_state):
    """Test that reset_form_state clears errors and submitting flag."""
    state, _ = mock_state  # Unpack state
    state.registration_error = "Some error"
    state.is_submitting = True

    state.reset_form_state()

    assert state.registration_error == ""
    assert not state.is_submitting


# --- Test validate_user ---


def test_validate_user_valid(mock_state, valid_form_data, mocker):
    """Test validate_user with matching ID and email."""
    state, _ = mock_state  # Unpack state
    mock_load_user_data = mocker.patch(
        "inventory_system.state.register_state.load_user_data"
    )
    mock_load_user_data.return_value = [
        {"ID": "12345", "Email": "test@example.com"},
        {"ID": "67890", "Email": "another@example.com"},
    ]

    is_valid = state.validate_user(valid_form_data)

    assert is_valid
    mock_load_user_data.assert_called_once()


def test_validate_user_invalid_id(mock_state, valid_form_data, mocker):
    """Test validate_user with non-matching ID."""
    state, _ = mock_state
    mock_load_user_data = mocker.patch(
        "inventory_system.state.register_state.load_user_data"
    )
    mock_load_user_data.return_value = [{"ID": "99999", "Email": "test@example.com"}]
    invalid_data = valid_form_data.copy()
    invalid_data["id"] = "00000"

    is_valid = state.validate_user(invalid_data)

    assert not is_valid


def test_validate_user_invalid_email(mock_state, valid_form_data, mocker):
    """Test validate_user with non-matching email."""
    state, _ = mock_state
    mock_load_user_data = mocker.patch(
        "inventory_system.state.register_state.load_user_data"
    )
    mock_load_user_data.return_value = [{"ID": "12345", "Email": "wrong@example.com"}]

    is_valid = state.validate_user(valid_form_data)

    assert not is_valid


def test_validate_user_case_insensitive_email(mock_state, valid_form_data, mocker):
    """Test validate_user email check is case-insensitive."""
    state, _ = mock_state
    mock_load_user_data = mocker.patch(
        "inventory_system.state.register_state.load_user_data"
    )
    mock_load_user_data.return_value = [
        {"ID": "12345", "Email": "TEST@EXAMPLE.COM"}
    ]  # Uppercase in data

    is_valid = state.validate_user(valid_form_data)  # Lowercase in form

    assert is_valid


def test_validate_user_empty_data(mock_state, valid_form_data, mocker):
    """Test validate_user when user_data.json is empty or not found."""
    state, _ = mock_state
    mock_load_user_data = mocker.patch(
        "inventory_system.state.register_state.load_user_data"
    )
    mock_load_user_data.return_value = []

    is_valid = state.validate_user(valid_form_data)

    assert not is_valid


# --- Test _validate_fields ---


# Helper to mock DB query for username uniqueness
def mock_db_user_check(mocker, state, username_exists=False):
    mock_session_instance = state.mock_session_instance
    mock_user = (
        MagicMock(spec=reflex_local_auth.user.LocalUser) if username_exists else None
    )
    mock_session_instance.exec.return_value.one_or_none.return_value = mock_user


@pytest.mark.parametrize(
    "username, password, confirm_password, expected_error",
    [
        ("", "Pass1!", "Pass1!", "Username cannot be empty"),
        ("usr", "Pass1!", "Pass1!", "Username must be at least 4 characters long"),
        ("a" * 21, "Pass1!", "Pass1!", "Username cannot exceed 20 characters"),
        (
            "user name",
            "Pass1!",
            "Pass1!",
            "Username can only contain letters, numbers, and underscores (_)",
        ),
        ("validuser", "", "", "Password cannot be empty"),
        ("validuser", "short", "short", "Password must be at least 8 characters long"),
        (
            "validuser",
            "nouppercase1!",
            "nouppercase1!",
            "Password must contain an uppercase letter",
        ),
        (
            "validuser",
            "NOLOWERCASE1!",
            "NOLOWERCASE1!",
            "Password must contain a lowercase letter",
        ),
        ("validuser", "NoNumber!", "NoNumber!", "Password must contain a number"),
        (
            "validuser",
            "NoSpecial1",
            "NoSpecial1",
            "Password must contain a special character",
        ),
        ("validuser", "ValidPass1!", "Mismatch1!", "Passwords do not match"),
    ],
)
def test_validate_fields_invalid(
    mock_state, username, password, confirm_password, expected_error, mocker
):
    """Test various invalid field combinations for _validate_fields."""
    state, _ = mock_state
    # Assume username doesn't exist in DB for these checks
    mock_db_user_check(mocker, state, username_exists=False)

    is_valid = state._validate_fields(username, password, confirm_password)

    assert not is_valid
    assert state.registration_error == expected_error


def test_validate_fields_username_exists(mock_state, mocker):
    """Test _validate_fields when the username already exists."""
    state, _ = mock_state
    username = "existinguser"
    password = "Password123!"
    # Mock that the username *does* exist
    mock_db_user_check(mocker, state, username_exists=True)

    is_valid = state._validate_fields(username, password, password)

    assert not is_valid
    assert (
        state.registration_error
        == f"Username {username} is already registered. Try a different name"
    )
    # Check that the DB query was made
    state.mock_session_instance.exec.assert_called_once()


def test_validate_fields_valid(mock_state, mocker):
    """Test _validate_fields with valid inputs and non-existent username."""
    state, _ = mock_state
    username = "new_valid_user"
    password = "Password123!"
    # Mock that the username *does not* exist
    mock_db_user_check(mocker, state, username_exists=False)

    is_valid = state._validate_fields(username, password, password)

    assert is_valid
    assert state.registration_error == ""
    # Check that the DB query was made
    state.mock_session_instance.exec.assert_called_once()


@pytest.mark.asyncio
async def test_handle_registration_success(mock_state, valid_form_data, mocker):
    """Test the successful registration flow."""
    state, mock_audit_logger = mock_state  # Unpack

    # --- Patch __setattr__ to allow setting error_message and new_user_id ---
    original_setattr = CustomRegisterState.__setattr__

    @functools.wraps(original_setattr)
    def patched_setattr(self, name, value):
        if name in ("error_message", "new_user_id"):
            object.__setattr__(self, name, value)
        else:
            original_setattr(self, name, value)

    mocker.patch.object(CustomRegisterState, "__setattr__", new=patched_setattr)

    # Mock dependencies for success path
    mocker.patch(
        "inventory_system.state.register_state.load_user_data",
        return_value=[{"ID": "12345", "Email": "test@example.com"}],
    )
    # Explicitly mock validate_user
    mock_validate_user = mocker.patch(
        "inventory_system.state.register_state.CustomRegisterState.validate_user",
        return_value=True,
    )
    # Mock base class handle_registration
    mock_handle_registration = mocker.patch(
        "reflex_local_auth.RegistrationState.handle_registration"
    )

    # Mock session operations
    mock_session_instance = state.mock_session_instance
    # Mock sqlmodel.select to prevent metadata access
    mock_select = mocker.patch("sqlmodel.select")
    mock_query = MagicMock()
    mock_select.return_value = mock_query
    # Configure exec to handle the query and return None for first()
    mock_session_instance.exec.return_value.first.return_value = None
    # Explicitly mock add, commit, refresh, and rollback
    mock_session_instance.add = MagicMock()
    mock_session_instance.commit = MagicMock()
    mock_session_instance.refresh = MagicMock()
    mock_session_instance.rollback = MagicMock()

    # Simulate successful base registration
    def side_effect_handle_reg(*args, **kwargs):
        state.new_user_id = 1

    state.error_message = ""
    mock_handle_registration.side_effect = side_effect_handle_reg

    # Mock UserInfo creation and saving
    mock_user_info = create_autospec(UserInfo)
    mock_user_info.id = 101
    mock_user_info.role = "employee"
    mock_user_info.email = valid_form_data["email"]
    mock_user_info.user_id = 1
    mock_user_info.profile_picture = DEFAULT_PROFILE_PICTURE
    mock_user_info.is_admin = False
    mock_user_info.is_supplier = False
    mock_user_info.supplier = None  # Explicitly mock relationship
    mocker.patch(
        "inventory_system.state.register_state.UserInfo", return_value=mock_user_info
    )
    mock_user_info.set_role = MagicMock()

    # Run the async generator
    events = [e async for e in state.handle_registration_with_email(valid_form_data)]

    # Assertions
    assert state.is_submitting is False
    assert state.registration_error == ""
    # Verify mocks were called as expected
    mock_validate_user.assert_called_once_with(valid_form_data)
    mock_handle_registration.assert_called_once_with(valid_form_data)
    mock_session_instance.add.assert_called_once_with(mock_user_info)
    mock_session_instance.commit.assert_called_once()
    mock_session_instance.refresh.assert_called_once_with(mock_user_info)
    mock_user_info.set_role.assert_called_once()

    # Logging assertions
    mock_audit_logger.info.assert_any_call(
        "success_registration",
        username="testuser",
        email="test@example.com",
        user_id=1,
        user_info_id=101,
        role="employee",
        ip_address="127.0.0.1",
    )

    # UI feedback assertions
    assert len(events) == 2
    mocker.patch("reflex.toast").success.assert_called_once()
    mocker.patch("asyncio.sleep").assert_called_once_with(2)
    mocker.patch("reflex.redirect").assert_called_once_with(routes.LOGIN_ROUTE)
