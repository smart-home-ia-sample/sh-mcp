from app.tools_catalog import TOOLS

VERBS = {
    "turn_on", "turn_off", "set_brightness", "set_temperature",
    "open", "close", "lock", "unlock", "arm", "disarm",
}


def test_catalog_covers_the_ten_verbs_with_examples_and_tags():
    assert {t["id"] for t in TOOLS} == VERBS
    for tool in TOOLS:
        assert tool["id"] == tool.get("id")
        assert tool["description"]
        assert tool["tags"]
        assert tool["examples"]
