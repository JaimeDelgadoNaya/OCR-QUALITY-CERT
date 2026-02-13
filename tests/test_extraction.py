from certsplit.extraction import CERT_LABEL_RE, HEAT_LABEL_RE, normalize_token


def test_cert_patterns_variants():
    text = "Inspection certificate No: 80209171-01-280\nZeugnis-Nr. 0000369904/1\n"
    vals = [normalize_token(m.group(1)) for m in CERT_LABEL_RE.finditer(text)]
    assert "80209171-01-280" in vals
    assert "0000369904/1" in vals


def test_heat_patterns_variants():
    text = "Heat No. H12345\nSchmelze: ABC987\nColada: 445566\n"
    vals = [normalize_token(m.group(1)) for m in HEAT_LABEL_RE.finditer(text)]
    assert {"H12345", "ABC987", "445566"}.issubset(set(vals))
