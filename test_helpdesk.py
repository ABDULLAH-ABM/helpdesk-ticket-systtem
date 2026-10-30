import unittest
import helpdesk


class HelpdeskTests(unittest.TestCase):
    def setUp(self):
        self.conn = helpdesk.connect(":memory:")

    def test_add_and_get(self):
        tid = helpdesk.add_ticket(self.conn, "Printer jam", "", "hardware", "low", "sara")
        self.assertEqual(helpdesk.get_ticket(self.conn, tid)["status"], "open")

    def test_priority_ordering(self):
        helpdesk.add_ticket(self.conn, "A", "", "other", "low", "x")
        helpdesk.add_ticket(self.conn, "B", "", "network", "critical", "x")
        self.assertEqual(helpdesk.list_tickets(self.conn)[0]["title"], "B")

    def test_update_and_report(self):
        tid = helpdesk.add_ticket(self.conn, "VPN down", "", "network", "high", "x")
        self.assertTrue(helpdesk.update_ticket(self.conn, tid, status="resolved"))
        self.assertFalse(helpdesk.update_ticket(self.conn, 999, status="closed"))
        self.assertEqual(helpdesk.report(self.conn)["status"], {"resolved": 1})

    def test_comments(self):
        tid = helpdesk.add_ticket(self.conn, "Email", "", "account", "medium", "x")
        self.assertTrue(helpdesk.add_comment(self.conn, tid, "tech1", "Reset password"))
        self.assertEqual(len(helpdesk.get_comments(self.conn, tid)), 1)


if __name__ == "__main__":
    unittest.main()
