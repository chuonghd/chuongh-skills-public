"""Daily spend alarm: stop at every $10 of today's spend until the user acknowledges that level."""

import json
import unittest
from datetime import date, timedelta

from helpers import IsolatedStoreTest, daily_spend_guard, ledger_record, openai_response


class DailySpendAlarmTest(IsolatedStoreTest):
    def setUp(self):
        super().setUp()
        self.api = self.api_returns(openai_response())  # each generation adds ~$0.0105

    def generate(self, *extra):
        return self.run_script("--prompt", "x", *extra)

    def test_under_10_generates(self):
        self.seed(ledger_record(9.98))
        code, text, _ = self.generate()
        self.assertEqual(code, 0, text)

    def test_reaching_10_stops_before_the_api_with_exit_3(self):
        self.seed(ledger_record(10.0))
        code, text, _ = self.generate()
        self.assertEqual(code, daily_spend_guard.HALT_EXIT_CODE)
        self.assertIn("DAILY SPEND ALERT", text)
        self.assertIn("--ack-daily-spend 10", text)
        self.api.assert_not_called()
        self.assertEqual(self.run_dirs(), [])

    def test_crossing_10_during_the_day_stops_the_next_run(self):
        self.seed(ledger_record(9.995))
        self.assertEqual(self.generate()[0], 0)        # this run takes the day past $10
        self.assertEqual(self.generate()[0], daily_spend_guard.HALT_EXIT_CODE)

    def test_acknowledging_10_continues_until_20(self):
        self.seed(ledger_record(10.0))
        self.assertEqual(self.generate("--ack-daily-spend", "10")[0], 0)
        self.assertEqual(self.generate()[0], 0)        # still acknowledged, still under $20
        self.seed(ledger_record(10.0))                 # day now past $20
        code, text, _ = self.generate()
        self.assertEqual(code, daily_spend_guard.HALT_EXIT_CODE)
        self.assertIn("--ack-daily-spend 20", text)

    def test_ack_must_match_the_current_level(self):
        self.seed(ledger_record(10.0))
        self.assertIn("step to acknowledge is 10", self.generate("--ack-daily-spend", "20")[1])
        self.seed(ledger_record(10.0))
        self.assertIn("step to acknowledge is 20", self.generate("--ack-daily-spend", "10")[1])
        self.api.assert_not_called()

    def test_ack_when_no_alert_is_refused(self):
        code, text, _ = self.generate("--ack-daily-spend", "10")
        self.assertNotEqual(code, 0)
        self.assertIn("no alert is active", text)

    def test_big_jump_skips_to_the_highest_level_reached(self):
        self.seed(ledger_record(25.0))
        self.assertIn("--ack-daily-spend 20", self.generate()[1])

    def test_only_todays_successful_runs_count(self):
        self.seed(ledger_record(50.0, days_ago=1), ledger_record(None, status="error"), ledger_record(9.0))
        self.assertEqual(self.generate()[0], 0)

    def test_yesterdays_ack_does_not_carry_over(self):
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        (self.store / daily_spend_guard.ACK_FILE).write_text(json.dumps({"date": yesterday, "acknowledged_usd": 20}))
        self.seed(ledger_record(12.0))
        self.assertEqual(self.generate()[0], daily_spend_guard.HALT_EXIT_CODE)

    def test_dry_run_reports_status_and_never_stops(self):
        self.seed(ledger_record(12.0))
        code, text, data = self.run_script("--prompt", "x", "--dry-run")
        self.assertEqual(code, 0, text)
        self.assertEqual(data["daily_spend"], {"spent_today_usd": 12.0, "reached_usd": 10, "acknowledged_usd": 0, "halted": True})


if __name__ == "__main__":
    unittest.main()
