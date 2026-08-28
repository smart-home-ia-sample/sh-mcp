from app import prompts


def test_prompt_helpers_return_their_constants():
    assert prompts.leave_home() == prompts.LEAVE_HOME
    assert prompts.bedtime() == prompts.BEDTIME
    assert prompts.energy_optimization() == prompts.ENERGY_OPTIMIZATION
    assert prompts.home_status() == prompts.HOME_STATUS


def test_prompts_reference_the_expected_resources():
    assert "home://security" in prompts.LEAVE_HOME
    assert "bedroom" in prompts.BEDTIME.lower()
    assert "home://energy" in prompts.ENERGY_OPTIMIZATION
    for uri in ("home://security", "home://devices", "home://energy", "home://events"):
        assert uri in prompts.HOME_STATUS
