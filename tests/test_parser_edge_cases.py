from custom_components.erftverband_riverlevel.api import parse_german_datetime, parse_german_number


class TestNumberEdgeCases:
    def test_leading_plus(self):
        assert parse_german_number("+     1") == 1.0
        assert parse_german_number("+0") == 0.0
        assert parse_german_number("+ 14") == 14.0

    def test_leading_plus_with_space(self):
        assert parse_german_number("+     0") == 0.0
        assert parse_german_number("+     2") == 2.0

    def test_trend_values(self):
        assert parse_german_number("-0") == -0.0
        assert parse_german_number("-1") == -1.0
        assert parse_german_number("-14") == -14.0
        assert parse_german_number("-0.001") == -0.001
        assert parse_german_number("-0.000") == -0.0
        assert parse_german_number("-0.09") == -0.09

    def test_thousands_with_comma(self):
        assert parse_german_number("1.234,56") == 1234.56
        assert parse_german_number("1.234,0") == 1234.0

    def test_thousands_with_dot(self):
        assert parse_german_number("1,234.56") == 1234.56

    def test_whitespace_variants(self):
        assert parse_german_number("  12,4  ") == 12.4
        assert parse_german_number("\t5.1\n") == 5.1

    def test_nbsp(self):
        assert parse_german_number("1\xa0234,5") == 1234.5

    def test_html_entities(self):
        assert parse_german_number("&nbsp;12,4") == 12.4

    def test_single_dash(self):
        assert parse_german_number("-") is None

    def test_em_dash(self):
        assert parse_german_number("—") is None

    def test_en_dash(self):
        assert parse_german_number("–") is None

    def test_triple_dash(self):
        assert parse_german_number("---") is None

    def test_ka(self):
        assert parse_german_number("k.A.") is None

    def test_empty_after_cleanup(self):
        assert parse_german_number("cm") is None
        assert parse_german_number("k.A.") is None

    def test_narrow_nbsp(self):
        assert parse_german_number("12\u20094,5") == 124.5  # thin space as thousands separator


class TestDatetimeEdgeCases:
    def test_two_digit_year_variants(self):
        dt = parse_german_datetime("21.07.26 07:01")
        assert dt is not None
        assert dt.year == 2026

        dt = parse_german_datetime("31.12.99 23:59")
        assert dt is not None
        assert dt.year == 2099

    def test_four_digit_year(self):
        dt = parse_german_datetime("21.07.2026 07:01")
        assert dt is not None
        assert dt.year == 2026

        dt = parse_german_datetime("01.01.2000 00:00")
        assert dt is not None
        assert dt.year == 2000

    def test_single_digit_hour(self):
        dt = parse_german_datetime("21.07.26 7:01")
        assert dt is not None
        assert dt.hour == 7

    def test_leading_spaces(self):
        dt = parse_german_datetime("  21.07.26 07:01  ")
        assert dt is not None

    def test_nbsp_in_datetime(self):
        dt = parse_german_datetime("21.07.26\xa007:01")
        assert dt is not None
        assert dt.hour == 7

    def test_none_input(self):
        assert parse_german_datetime(None) is None

    def test_empty_input(self):
        assert parse_german_datetime("") is None

    def test_whitespace_only(self):
        assert parse_german_datetime("   ") is None

    def test_malformed(self):
        assert parse_german_datetime("not a date") is None
        assert parse_german_datetime("21-07-26 07:01") is None
        assert parse_german_datetime("21.07.26") is None


class TestCombinedEdgeCases:
    def test_zieverich_water_level_only(self):
        """Zieverich has water level but no discharge."""
        assert parse_german_number("89") == 89.0
        assert parse_german_number("-") is None

    def test_niederberg_no_discharge(self):
        """Niederberg has water level but no discharge or thresholds."""
        assert parse_german_number("9") == 9.0
        assert parse_german_number("-") is None

    def test_vussem_no_thresholds(self):
        """Vussem has no HQ thresholds."""
        assert parse_german_number("17") == 17.0
        assert parse_german_number("0.06") == 0.06

    def test_fuessenich_ow_special(self):
        """Füssenich OW has special discharge meaning."""
        assert parse_german_number("42") == 42.0
        assert parse_german_number("0.00") == 0.0
        assert parse_german_number("-") is None  # Tendenz discharge

    def test_hqextrem_only_q(self):
        """Some stations have HQExtrem only for Q, not W."""
        assert parse_german_number("78") == 78.0  # Essig HQ100 Q
        assert parse_german_number("-") is None  # Essig HQ100 W
        assert parse_german_number("215") == 215.0  # Essig HQExtrem Q
        assert parse_german_number("-") is None  # Essig HQExtrem W
