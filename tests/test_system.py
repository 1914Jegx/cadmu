from cadmu.core import system


def test_detect_host():
    identity = system.detect_host()
    assert identity.effective_user
    assert identity.home.exists()
