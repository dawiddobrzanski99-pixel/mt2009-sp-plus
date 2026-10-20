"""MT2009_PLUS_MARKET_PREVIEW_V1: the market preview's rules and snapshot on
fake data - no database, no Flask. python3 test_market_preview.py"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from market_preview import rules, sheet, snapshot  # noqa: E402

P = snapshot.Proto


def protos():
    return {
        19: P(19, rules.ITEM_WEAPON, 0, 0, 1, (22, 0, 0, 15, 19, 3), (), 9, "Miecz+9"),
        10: P(10, rules.ITEM_WEAPON, 0, 1 << 3, 1, (22, 0, 0, 15, 19, 3), (), 0, "Miecz+0"),
        50300: P(50300, rules.ITEM_SKILLBOOK, 0, 0, 0, (0,) * 6, (), -1, "Księga Umiejętności"),
        27799: P(27799, rules.ITEM_MATERIAL, 0, 0, 0, (0,) * 6, (), -1, "Rybia Ość"),
    }


SHOPS = {100: (1, 469000, 964000, 1, True, "Sklep Ani"), 200: (21, 55000, 157000, 1, False, "Stary")}
OWNERS = {100: ("Ania", True, 1), 200: ("Gracz", False, 2)}


def items():
    no = (0,) * 14
    bonus = (44, 20, 122, 45) + (0,) * 10
    return [
        (1, 100, 19, 1, 0, 0, 0, bonus, 5000000),
        (2, 100, 10, 1, 0, 0, 0, no, 20000),
        (3, 100, 50300, 1, 2, 0, 0, no, 300000),
        (4, 100, 27799, 10, 0, 0, 0, no, 1000000),
        (5, 200, 10, 1, 0, 0, 0, no, 25000),
        (6, 100, 50300, 1, 2, 0, 0, no, 99000000),        # five times the price list: a slip
    ]


def build(samples=None):
    names = {(19, 0): "Miecz+9", (10, 0): "Miecz+0", (50300, 2): "Wir Miecza — Księga", (27799, 0): "Rybia Ość"}
    return snapshot.build_snapshot(items(), protos(), SHOPS, OWNERS, {44: 20}, names, samples or {}, 100)


class Rules(unittest.TestCase):
    def test_prices(self):
        self.assertEqual(rules.parse_price("1.5kk"), 1500000)
        self.assertEqual(rules.parse_price("500k"), 500000)
        self.assertEqual(rules.parse_price("1 500 000"), 1500000)
        self.assertIsNone(rules.parse_price(""))
        with self.assertRaises(ValueError):
            rules.parse_price("abc")

    def test_categories_and_classes(self):
        self.assertEqual(rules.classify(rules.ITEM_WEAPON, 0, 19), (1, 1))
        self.assertEqual(rules.classify(rules.ITEM_SKILLBOOK, 0, 50300, 2), (6, 1))
        self.assertEqual(rules.classify(rules.ITEM_METIN, 0, 28431), (7, 5))
        self.assertEqual(rules.class_mask(rules.ITEM_WEAPON, 1 << 3), 15 & ~2)

    def test_filters_are_parameters(self):
        f, errors = rules.parse_filters({"q": "Łuk", "pmin": "1kk", "pmax": "5k", "cat": "weapons", "sub": "bows",
                                         "b1": "44", "b1v": "10", "sort": "x"}, bonus_points=(44,))
        self.assertEqual(errors.get("pmax"), "range")
        self.assertEqual(errors.get("sort"), "invalid")
        where, params = rules.build_where(f)
        self.assertNotIn("luk", where)
        self.assertIn("%luk%", params)

    def test_yang_rate(self):
        self.assertEqual(rules.yang_rate_price_pct(100), 100)
        self.assertEqual(rules.yang_rate_price_pct(150), 160)
        self.assertEqual(rules.yang_rate_price_pct(20000), 20000)

    def test_bonus_multiplier(self):
        plain = rules.reference_multiplier(rules.ITEM_WEAPON, 0, 1, [], [], {})
        rich = rules.reference_multiplier(rules.ITEM_WEAPON, 0, 1, [(44, 20)], [(122, 45)], {44: 20})
        self.assertEqual(plain, 1.0)
        self.assertGreater(rich, 4.0)


class Snapshot(unittest.TestCase):
    def test_build_and_page(self):
        snap = build()
        self.assertEqual(snap.offers, 6)
        f, _ = rules.parse_filters({})
        rows, total, counts, _page, _pages = snap.page(f)
        self.assertEqual(total, 4)                    # the closed shop and the slip are hidden
        self.assertEqual(counts[(1, 1)], 2)
        f, _ = rules.parse_filters({"expired": "1", "hideslip": "0"})
        self.assertEqual(snap.page(f)[1], 6)
        f, _ = rules.parse_filters({"q": "wir miecza"})
        self.assertEqual([r["id"] for r in snap.page(f)[0]], [3])
        f, _ = rules.parse_filters({"b1": "44", "b1v": "20"}, snap.bonus_points)
        self.assertEqual([r["id"] for r in snap.page(f)[0]], [1])
        self.assertEqual(snap.shops[100]["x"], 469000)

    def test_reference_and_bargain(self):
        snap = build()
        row = snap.execute("SELECT ref, bkey, rsrc FROM offers WHERE id = 2")[0]
        self.assertAlmostEqual(row[0], sheet.GEAR[10][1][0])  # the price list's +0
        self.assertEqual(row[2], rules.REF_SHEET)
        self.assertEqual(row[1], rules.bargain_pct(20000, row[0]))
        week = {(10, 0, 0): (40000.0,) * 5}
        row = build(week).execute("SELECT ref, bkey, rsrc FROM offers WHERE id = 2")[0]
        self.assertEqual((row[0], row[1], row[2]), (40000.0, 50, rules.REF_WEEK))

    def test_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            history = snapshot.History(os.path.join(tmp, "h.sqlite"))
            history.record([(i, 10, 0, 0, 1000.0 + i, 1000.0 + i) for i in range(6)], now=1000000)
            self.assertEqual(len(history.compute_samples(now=1000000)[(10, 0, 0)]), 6)
            self.assertEqual(len(history.chart(10, 0, 0, now=1000000)), 1)

    def test_bots_fair_prices(self):
        # MT2009_PLUS_MARKET_FAIR_EXPORT_V1: the bots' own price of a line wins.
        with tempfile.TemporaryDirectory() as tmp:
            path = snapshot.default_fair_path(tmp)
            with open(path, "w") as fh:
                fh.write("# header\n2\t40000\n4\t50000\n999\t7\nbad line\n")
            fair = snapshot.read_fair_prices(path, {1, 2, 3, 4, 5, 6})
            self.assertEqual(fair, {2: 40000, 4: 50000})
            self.assertEqual(snapshot.read_fair_prices(path, {2}, now=os.path.getmtime(path) + 3600), {})
            self.assertEqual(snapshot.read_fair_prices(os.path.join(tmp, "none"), {2}), {})
        names = {(19, 0): "Miecz+9", (10, 0): "Miecz+0", (50300, 2): "Wir", (27799, 0): "Ość"}
        snap = snapshot.build_snapshot(items(), protos(), SHOPS, OWNERS, {44: 20}, names, {}, 100, fair)
        rows = {r[0]: r for r in snap.execute("SELECT id, ref, bkey, rsrc FROM offers")}
        self.assertEqual(rows[2][1], 40000)
        self.assertEqual(rows[2][2], 50)                 # 20 000 against 40 000
        self.assertEqual(rows[2][3], rules.REF_BOTS)
        self.assertEqual(rows[4][3], rules.REF_BOTS)     # 100 000 a piece against 50 000: dearer
        self.assertEqual(rows[4][2], -100)
        self.assertNotEqual(rows[3][3], rules.REF_BOTS)


if __name__ == "__main__":
    unittest.main()
