import textwrap
import pytest

from auto.spec_translator import translate


VALID_SPEC = textwrap.dedent(
    """
    # Get Post Details

    Return details for a post.

    ```json
    {
      "title": "get_post",
      "description": "Retrieve a post by id",
      "type": "object",
      "properties": {
        "id": {"type": "string", "description": "Post id"}
      },
      "required": ["id"]
    }
    ```
    """
)


def test_translate_valid_spec():
    spec = translate(VALID_SPEC)
    assert spec["name"] == "get_post_details"
    assert spec["description"] == "Return details for a post."
    assert spec["parameters"]["properties"]["id"]["type"] == "string"


def test_translate_missing_schema():
    with pytest.raises(ValueError):
        translate("# Title\nNo schema here.")


def test_translate_invalid_json():
    malformed = "# Title\n```json\n{invalid}\n```"
    with pytest.raises(ValueError):
        translate(malformed)
