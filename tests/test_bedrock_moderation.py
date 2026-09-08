import pytest

from bedrock_client import generate_image
from security import ModerationError


def test_generate_image_moderates_main_prompt():
    with pytest.raises(ModerationError):
        generate_image("un arma de fuego brillante sobre fondo negro", "Realismo")


def test_generate_image_moderates_negative_prompt():
    with pytest.raises(ModerationError):
        generate_image("un logo minimalista de cafetería", "Realismo", negative_prompt="discurso de odio")


def test_generate_image_allows_clean_prompts():
    image_bytes, seed = generate_image("un logo minimalista de cafetería", "Realismo")
    assert image_bytes
    assert isinstance(seed, int)
