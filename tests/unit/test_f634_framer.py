from recorder_proxy.protocol.bbu.f634_framer import F634Framer


def test_f634_framer_handles_split_and_sticky_frames():
    frame1 = bytes.fromhex("f6340002aabb")
    frame2 = bytes.fromhex("f6340001cc")
    framer = F634Framer()

    assert framer.feed(frame1[:3]) == []
    out = framer.feed(frame1[3:] + frame2)

    assert [item.frame for item in out] == [frame1, frame2]
    assert [item.error for item in out] == [None, None]
