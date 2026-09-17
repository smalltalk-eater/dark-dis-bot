from cogs.moderation.verification import (
    VERIFICATION_BUTTON_ID,
    VerificationView,
)


def test_verification_button_is_persistent():
    view = VerificationView()

    assert view.timeout is None
    assert len(view.children) == 1
    assert view.children[0].custom_id == VERIFICATION_BUTTON_ID
