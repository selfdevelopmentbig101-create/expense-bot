from types import SimpleNamespace as Msg

from app.core.messages import MAX_TEXT_LENGTH, is_plain_text, message_text


def test_text_and_captions():
    assert message_text(Msg(text="10000 bread", caption=None)) == "10000 bread"
    assert message_text(Msg(text=None, caption="10000 bread")) == "10000 bread"
    assert message_text(Msg(text=None, caption=None)) is None  # a sticker
    assert message_text(Msg()) is None


def test_plain_text_is_anything_with_words_that_is_not_a_command():
    assert is_plain_text(Msg(text="10000", caption=None))
    assert is_plain_text(Msg(text=None, caption="10000 bread"))  # a photo of a receipt with a note
    assert not is_plain_text(Msg(text="/today", caption=None))
    assert not is_plain_text(Msg(text="/start@my_bot", caption=None))
    assert not is_plain_text(Msg(text=None, caption=None))
    assert not is_plain_text(Msg(text="", caption=None))


def test_a_caption_that_looks_like_a_command_is_just_text():
    assert is_plain_text(Msg(text=None, caption="/today"))


def test_the_length_limit_is_sensible():
    assert MAX_TEXT_LENGTH == 1000
