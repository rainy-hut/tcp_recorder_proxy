from recorder_proxy.protocol.text.mml_detector import is_mml_text, is_probably_text
from recorder_proxy.protocol.text.text_framer import TextFramer


def test_mml_detector_recognizes_common_commands():
    assert is_mml_text(b"LST SOFTWARE:;\r\n")
    assert is_mml_text(b"neg opt:on=cc,st=on,para=150;")
    assert not is_mml_text(b"hello world")


def test_probably_text_rejects_dense_binary():
    assert is_probably_text("执行成功".encode("utf-8"))
    assert not is_probably_text(b"\x00\x01\x02\x03\x04\x05\x06\x07")


def test_text_framer_uses_exportable_classification_value():
    messages = TextFramer(bbu_mml_mode=True).feed(b"LST SOFTWARE:;\r\n")

    assert messages[0].classification == "BBU_MML_PLAIN"
