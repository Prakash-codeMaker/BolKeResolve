"""Regression tests for merchant-specific, first-party support routes."""
import unittest

from backend.support_directory import build_quick_support_draft, find_support_destinations


class OfficialSupportDirectoryTests(unittest.TestCase):
    def test_zomato_refund_routes_to_merchant_then_consumer_helpline(self):
        destinations = find_support_destinations(
            merchant="Zomato",
            description="The refund was promised in three days but has not arrived.",
            issue_type="Refund not received",
        )
        self.assertGreaterEqual(len(destinations), 2)
        self.assertEqual(destinations[0]["id"], "zomato")
        self.assertEqual(destinations[1]["id"], "national_consumer_helpline")
        self.assertTrue(all(item["url"].startswith("https://") for item in destinations))

    def test_razorpay_gateway_settlement_routes_only_to_razorpay_merchant_support(self):
        destinations = find_support_destinations(
            merchant="Razorpay",
            description="Customer payments are not settling to our business bank account.",
            issue_type="Merchant settlement not credited",
        )
        self.assertEqual([item["id"] for item in destinations], ["razorpay"])
        self.assertIn("Transactions → Payments", destinations[0]["action"])
        self.assertTrue(destinations[0]["url"].startswith("https://"))

    def test_upi_pending_route_includes_npci_guidance(self):
        destinations = find_support_destinations(
            description="UPI payment pending and recipient not credited after amount debited.",
            issue_type="UPI payment pending / recipient not credited",
        )
        self.assertTrue(any(item["id"] == "npci_upi" for item in destinations))

    def test_urgent_unauthorised_transaction_prioritises_cyber_safety_route(self):
        destinations = find_support_destinations(
            merchant="PhonePe",
            description="I don't recognise this transaction; I suspect fraud.",
            issue_type="Suspected fraud or unauthorised transaction",
        )
        self.assertEqual(destinations[0]["id"], "cybercrime_india")
        self.assertLessEqual(len(destinations), 2)
        self.assertIn("bank/payment provider immediately", destinations[0]["action"])

    def test_unknown_merchant_never_invents_a_provider_contact(self):
        destinations = find_support_destinations(
            merchant="ImaginaryPay 123",
            description="Refund not received.",
            issue_type="Refund not received",
        )
        self.assertTrue(destinations)
        self.assertNotIn("ImaginaryPay", " ".join(item["name"] for item in destinations))
        self.assertTrue(all(item["url"].startswith("https://") for item in destinations))

    def test_short_alias_does_not_match_inside_an_unrelated_word(self):
        destinations = find_support_destinations(
            merchant="preMMTpost is not a distinct short alias",
            description="A refund is late.",
            issue_type="Refund not received",
        )
        # A token-style alias may match as a full token only. Longer unrelated strings must not.
        self.assertNotEqual(destinations[0]["id"], "makemytrip")

    def test_support_draft_is_specific_but_never_claims_to_be_sent(self):
        draft = build_quick_support_draft(
            merchant="Zomato", issue_type="Refund not received",
            description="Refund promised in 3 days; still pending after 8 days.", amount=350,
        )
        self.assertIn("Hello Zomato Support", draft["message"])
        self.assertIn("₹350", draft["message"])
        self.assertIn("as reported by me", draft["message"])
        self.assertIn("has not contacted", draft["notice"])
        self.assertIn("Draft only", draft["notice"])
        self.assertNotIn("refund has been initiated", draft["message"].lower())


    def test_razorpay_gateway_money_to_business_account_does_not_add_consumer_helpline(self):
        from backend.support_directory import find_support_destinations, build_quick_support_draft
        story = (
            "Refund 350 rupees from Razorpay. I made several customer payments. "
            "I am trying to extract the money from Razorpay to our business account."
        )
        routes = find_support_destinations("Razorpay", story, "Merchant settlement not credited")
        self.assertEqual([item["id"] for item in routes], ["razorpay"])
        draft = build_quick_support_draft("Razorpay", "Merchant settlement not credited", story, 350)
        self.assertIn("merchant settlement/payout", draft["message"])
        self.assertIn("settlement id", draft["message"].lower())
        self.assertIn("UTR", draft["message"])
        self.assertIn("customer collections", draft["message"])
        self.assertNotIn("order id", draft["message"].lower())
        self.assertIn("Transactions → Payments", routes[0]["action"])

if __name__ == "__main__":
    unittest.main()
