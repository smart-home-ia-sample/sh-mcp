LEAVE_HOME = """The user is leaving the house. Check home://security and home://environment,
then lock all doors, arm the alarm, and turn off nonessential devices (lights, TV, AC,
coffee maker). Keep the refrigerator running. Confirm the resulting state via home://security
and home://environment before reporting success."""

BEDTIME = """The user is going to sleep. Turn off lights in common areas (living_room, kitchen),
set the bedroom AC to a comfortable sleeping temperature, and check home://security for any
unlocked doors or open windows that should be addressed before bed."""

ENERGY_OPTIMIZATION = """Read home://energy. Summarize total consumption, identify the top
consumers, and present the recommendations already computed. Suggest turning off any
nonessential device that is unexpectedly on."""

HOME_STATUS = """Read home://security, home://devices, home://environment, home://energy and
home://events. Produce a concise summary covering security state, active devices, environment
conditions, energy consumption, and recent events."""


def leave_home() -> str:
    return LEAVE_HOME


def bedtime() -> str:
    return BEDTIME


def energy_optimization() -> str:
    return ENERGY_OPTIMIZATION


def home_status() -> str:
    return HOME_STATUS
