from temporal_join import Event, Match, Watermark, Flush, TemporalJoin, join


def oracle(items, within, lateness=0):
    """Small-input all-history oracle: intentionally no optimized eviction/index."""
    history = []
    watermarks = {"left": None, "right": None}
    result = []
    for item in items:
        if isinstance(item, Flush):
            break
        if isinstance(item, Watermark):
            watermarks[item.side] = item.timestamp
            continue
        w = watermarks[item.side]
        if w is not None and item.timestamp < w - lateness:
            continue
        matches = []
        for peer in history:
            if peer.side != item.side and peer.key == item.key:
                if abs(peer.timestamp - item.timestamp) <= within:
                    l, r = (item, peer) if item.side == "left" else (peer, item)
                    matches.append(Match(l, r, max(l.timestamp, r.timestamp)))
        matches.sort(key=lambda m: (m.left.timestamp, m.right.timestamp))
        result.extend(matches)
        history.append(item)
    return result


def check(items, within, lateness=0):
    expected = oracle(items, within, lateness)
    actual = list(join(iter(items), within, lateness))
    assert actual == expected
    engine = TemporalJoin(within, lateness)
    out = []
    for item in items:
        out.extend(engine.push(item))
        if isinstance(item, Flush):
            break
    assert out == expected
    return out
