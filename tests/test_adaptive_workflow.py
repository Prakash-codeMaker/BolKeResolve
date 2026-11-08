from __future__ import annotations

import unittest

from backend.adaptive_workflow import build_adaptive_workflow, extract_workflow_facts


class AdaptiveWorkflowTests(unittest.TestCase):
    def test_partial_story_waits_without_recommendation(self):
        workflow = build_adaptive_workflow("I have a problem with an order from Meesho.", intake_complete=False)
        self.assertEqual(workflow["status"], "collecting_story")
        self.assertIsNone(workflow["next_question"])
        self.assertIsNone(workflow["current_step"])

    def test_meesho_refund_spoken_amount_waits_for_order_outcome(self):
        story = "I did not receive my refund of three thousand five hundred from Meesho. It has been three weeks."
        facts = extract_workflow_facts(story)
        self.assertEqual(facts["merchant"], "Meesho")
        self.assertEqual(facts["amount"], 3500.0)
        self.assertEqual(facts["elapsed"], "three weeks")
        workflow = build_adaptive_workflow(story, intake_complete=True)
        self.assertEqual(workflow["next_question"]["field"], "order_outcome")
        self.assertIsNone(workflow["current_step"])

    def test_refund_progression_asks_status_then_deadline_then_prior_support(self):
        story = "I did not receive ₹3,000 refund from Meesho for three weeks."
        state = build_adaptive_workflow(story, intake_complete=True)
        self.assertEqual(state["next_question"]["field"], "order_outcome")
        facts = state["facts"]
        conversation = story + "\nThe return was picked up."
        facts = extract_workflow_facts(conversation, facts)
        state = build_adaptive_workflow(conversation, previous={"facts": facts, "intake_complete": True}, intake_complete=True)
        self.assertEqual(state["next_question"]["field"], "refund_scope")
        conversation += "\nThe refund is for the entire order."
        facts = extract_workflow_facts(conversation, state["facts"])
        state = build_adaptive_workflow(conversation, previous={"facts": facts, "intake_complete": True}, intake_complete=True)
        self.assertEqual(state["next_question"]["field"], "refund_status")
        story += "\nThe return was picked up. The refund is for the entire order.\nThe app says refund initiated."
        facts = extract_workflow_facts(story, state["facts"])
        state = build_adaptive_workflow(story, previous={"facts": facts, "intake_complete": True}, intake_complete=True)
        self.assertEqual(state["next_question"]["field"], "promised_timeline")
        story += "\nThe app said 7 working days."
        facts = extract_workflow_facts(story, state["facts"])
        state = build_adaptive_workflow(story, previous={"facts": facts, "intake_complete": True}, intake_complete=True)
        self.assertEqual(state["status"], "action")
        self.assertEqual(state["stage"], "overdue_refund_promise")

    def test_whole_order_colloquial_answer_does_not_repeat_refund_scope(self):
        story = "Hey Flipkart, I have not got the refund of 3,000 rupees. The order was cancelled because a product was unavailable. Support says the refund is in process."
        state = build_adaptive_workflow(story, intake_complete=True)
        self.assertEqual(state["next_question"]["field"], "refund_scope")
        answer = "Whole order ma'am"
        facts = extract_workflow_facts(story + "\n" + answer, state["facts"], "refund_scope")
        self.assertEqual(facts["refund_scope"], "full_order")
        next_state = build_adaptive_workflow(story + "\n" + answer, previous={"facts": facts, "intake_complete": True, "next_question": state["next_question"]}, intake_complete=True)
        self.assertNotEqual(next_state.get("next_question", {}).get("field"), "refund_scope")

    def test_full_order_hinglish_and_devanagari_variants_are_recognised(self):
        for answer in ("poora order", "pura order", "saara order", "पूरे ऑर्डर का refund", "all of it"):
            with self.subTest(answer=answer):
                facts = extract_workflow_facts(answer, {}, "refund_scope")
                self.assertEqual(facts["refund_scope"], "full_order")



    def test_contacting_their_support_and_support_said_is_recognised(self):
        for phrase in (
            "I have contacted their support and they said the refund is processing.",
            "I reached out to the support team; they told me the refund will be processed.",
            "I spoke to their support yesterday.",
        ):
            with self.subTest(phrase=phrase):
                facts = extract_workflow_facts(phrase)
                self.assertTrue(facts["support_contacted"])

    def test_refund_reported_as_in_process_or_procedure_is_not_asked_again_as_unknown(self):
        for phrase in (
            "Support said the refund is in process.",
            "They are processing the refund.",
            "They said the procedure to give the refund back is underway.",
            "The refund is being processed.",
        ):
            with self.subTest(phrase=phrase):
                facts = extract_workflow_facts("Flipkart refund not received. " + phrase)
                self.assertEqual(facts["refund_status"], "pending")

    def test_partial_refund_asks_item_count_and_not_initiated_reason(self):
        story = "Meesho refund not received. The return was picked up."
        state = build_adaptive_workflow(story, intake_complete=True)
        facts = state["facts"]
        conversation = story + "\nThe refund is for selected products only."
        facts = extract_workflow_facts(conversation, facts)
        state = build_adaptive_workflow(conversation, previous={"facts": facts, "intake_complete": True}, intake_complete=True)
        self.assertEqual(state["next_question"]["field"], "item_count")
        facts = extract_workflow_facts(conversation + "\n2", state["facts"], "item_count")
        self.assertEqual(facts["item_count"], 2)
        conversation += "\nThe refund is for 2 products.\nThe app shows that the refund has not been initiated."
        facts = extract_workflow_facts(conversation, facts)
        state = build_adaptive_workflow(conversation, previous={"facts": facts, "intake_complete": True}, intake_complete=True)
        self.assertEqual(state["next_question"]["field"], "refund_reason")

    def test_spoken_duration_does_not_overwrite_refund_amount_or_swap_deadline_fields(self):
        first = extract_workflow_facts("I have not received my six thousand rupees refund from Meesho.")
        second = extract_workflow_facts(
            "They told me the refund would come in two days, but it has been more than six days.",
            first,
        )
        self.assertEqual(second["amount"], 6000.0)
        self.assertEqual(second["promised_days"], 2)
        self.assertEqual(second["elapsed_days"], 6)

    def test_order_age_is_not_automatically_treated_as_refund_waiting_time(self):
        facts = extract_workflow_facts("I ordered this three weeks ago but don't know when the refund was initiated.")
        self.assertEqual(facts["elapsed"], "three weeks")
        self.assertIsNone(facts["elapsed_days"])

    def test_meesho_unavailable_products_two_day_promise_over_six_days_routes_to_action(self):
        # Exact user-reported scenario: the engine must not ask the old
        # "what happened to the order?" question after the story contains it.
        story = (
            "I have not got the refund back of 6,000 rupees from MeeShop.\n"
            "Some of the products were not available, so they were not able to deliver it. "
            "They told me to give the refund back in two days, but it has been more than six days "
            "and I have not got the refund back."
        )
        facts = extract_workflow_facts(story)
        self.assertEqual(facts["merchant"], "Meesho")
        self.assertEqual(facts["amount"], 6000.0)
        self.assertEqual(facts["order_outcome"], "merchant_unable_to_fulfil")
        self.assertEqual(facts["refund_status"], "pending")
        self.assertEqual(facts["promised_days"], 2)
        self.assertEqual(facts["elapsed_days"], 6)
        self.assertEqual(facts["promised_timeline"], "two days")
        self.assertIn("more than six days", facts["elapsed"])

        workflow = build_adaptive_workflow(story, intake_complete=True)
        self.assertEqual(workflow["status"], "action")
        self.assertEqual(workflow["stage"], "overdue_refund_promise")
        self.assertIsNone(workflow["next_question"])
        self.assertEqual(workflow["support_destinations"][0]["id"], "meesho")
        self.assertIn("existing refund promise", workflow["current_step"]["title"])
        self.assertIn("₹6,000", workflow["support_draft"]["message"])
        self.assertIn("two days", workflow["support_draft"]["message"])
        self.assertIn("6 days", workflow["support_draft"]["message"])
        self.assertIn("refund initiation date", workflow["message"])
        self.assertIn("payment proof", workflow["message"])
        self.assertNotIn("What happened to the order", workflow["message"])

    def test_meesho_full_live_intake_turn_advances_from_order_outcome_to_overdue_action(self):
        first_turn = "I have not got the refund back of 6,000 rupees from Meesho."
        first = build_adaptive_workflow(first_turn, intake_complete=True)
        self.assertEqual(first["next_question"]["field"], "order_outcome")

        second_turn = (
            "Some of the products were not available, so they were not able to deliver it. "
            "They told me to give the refund back in two days, but it has been more than six days "
            "and I have not got the refund back."
        )
        full_conversation = first_turn + "\n" + first["next_question"]["prompt"] + "\n" + second_turn
        next_workflow = build_adaptive_workflow(
            full_conversation,
            previous=first,
            intake_complete=True,
        )
        self.assertEqual(next_workflow["status"], "action")
        self.assertEqual(next_workflow["stage"], "overdue_refund_promise")
        self.assertNotEqual((next_workflow.get("next_question") or {}).get("field"), "order_outcome")
        self.assertIn("overdue", next_workflow["title"].casefold())

    def test_refund_promise_not_overdue_does_not_claim_it_is_overdue(self):
        story = (
            "Meesho refund of ₹6,000. Some products were out of stock so the order could not be fulfilled. "
            "They promised the refund in two days and it has been one day."
        )
        workflow = build_adaptive_workflow(story, intake_complete=True)
        self.assertNotEqual(workflow.get("stage"), "overdue_refund_promise")
        self.assertNotIn("overdue", workflow.get("title", "").casefold())

    def test_meesho_route_is_official_and_specific_after_intake(self):
        story = "Meesho refund of ₹3,000 not received. Return was picked up. The refund is for the entire order. Refund initiated. No date was given. I already contacted support and got no response."
        workflow = build_adaptive_workflow(story, intake_complete=True)
        self.assertEqual(workflow["status"], "action")
        self.assertTrue(workflow["support_destinations"])
        self.assertEqual(workflow["support_destinations"][0]["id"], "meesho")
        self.assertIn("order-specific", workflow["current_step"]["title"])
        self.assertIn("Draft only", workflow["support_draft"]["notice"])

    def test_unknown_merchant_does_not_get_an_invented_route(self):
        story = "Refund not received from a small local app. The order was cancelled. Refund not initiated. I have not contacted support."
        workflow = build_adaptive_workflow(story, intake_complete=True)
        self.assertEqual(workflow["status"], "question")
        # Merchant identity remains a question if we cannot identify a supported platform.
        self.assertEqual(workflow["next_question"]["field"], "merchant")

    def test_unlisted_merchant_can_be_named_without_inventing_its_route(self):
        first = "Refund not received from another app or store."
        facts = extract_workflow_facts(first)
        self.assertEqual(facts["merchant"], "Other / unlisted platform")
        conversation = first + "\nThis order is from another app or store.\nShopClues"
        facts = extract_workflow_facts(conversation, facts)
        self.assertEqual(facts["merchant"], "ShopClues")
        workflow = build_adaptive_workflow(conversation + " The order was cancelled. The refund is for the entire order. Refund not initiated. I have not contacted support.", previous={"facts": facts}, intake_complete=True)
        followup_story = conversation + " The order was cancelled. The refund is for the entire order. Refund not initiated. The app shows no reason. I have not contacted support."
        workflow = build_adaptive_workflow(followup_story, previous={"facts": facts}, intake_complete=True)
        self.assertEqual(workflow["status"], "action")
        self.assertEqual(workflow["support_destinations"], [])
        self.assertIn("official app", workflow["current_step"]["detail"])

    def test_blinkit_damage_case_asks_order_outcome_before_action(self):
        story = "My Blinkit order arrived with a damaged item."
        workflow = build_adaptive_workflow(story, intake_complete=True)
        self.assertEqual(workflow["next_question"]["field"], "support_contacted")
        self.assertEqual(workflow["support_destinations"][0]["id"], "blinkit")

    def test_order_issue_uses_merchant_route_and_item_evidence(self):
        story = "The wrong item came in my Zepto order. I have not contacted support yet."
        workflow = build_adaptive_workflow(story, intake_complete=True)
        self.assertEqual(workflow["status"], "action")
        self.assertEqual(workflow["support_destinations"][0]["id"], "zepto")
        self.assertIn("photos/video", workflow["evidence_request"]["detail"])

    def test_upi_payment_is_separate_from_merchant_refund(self):
        story = "My Google Pay UPI payment was debited but the recipient was not credited yesterday."
        workflow = build_adaptive_workflow(story, intake_complete=True)
        self.assertEqual(workflow["stage"], "upi_dispute")
        self.assertTrue(any(item["id"] == "npci_upi" for item in workflow["support_destinations"]))

    def test_unauthorised_payment_takes_safety_path(self):
        workflow = build_adaptive_workflow("I did not make this UPI transaction. It looks fraudulent.", intake_complete=True)
        self.assertEqual(workflow["stage"], "urgent_safety")
        self.assertTrue(any(item["id"] == "cybercrime_india" for item in workflow["support_destinations"]))

    def test_razorpay_customer_collections_to_business_account_are_settlement_not_refund(self):
        story = (
            "Hey, we have not got the refund of 350 rupees from Razorpay that we have like I have make several payments so\n"
            "When I try to like extract it from Razorpay to our account\n"
            "They are not able to do it, and they have told that they will give, they were trying and give the money back in like\n"
            "Four days but it has been more than twelve days but I have not got anything back yet so please help me in getting it back"
        )
        facts = extract_workflow_facts(story)
        self.assertEqual(facts["merchant"], "Razorpay")
        self.assertEqual(facts["gateway_provider"], "Razorpay")
        self.assertEqual(facts["amount"], 350.0)
        self.assertTrue(facts["gateway_settlement"])
        self.assertEqual(facts["issue_family"], "merchant_settlement")
        self.assertEqual(facts["issue_type"], "Merchant settlement not credited")
        self.assertEqual(facts["promised_days"], 4)
        self.assertEqual(facts["elapsed_days"], 12)

        first = build_adaptive_workflow(story, intake_complete=True)
        self.assertEqual(first["status"], "question")
        self.assertEqual(first["stage"], "gateway_settlement_intake")
        self.assertEqual(first["next_question"]["field"], "settlement_status")
        self.assertIn("Razorpay Dashboard", first["next_question"]["prompt"])
        self.assertEqual(first["support_destinations"][0]["id"], "razorpay")
        self.assertNotIn("national_consumer_helpline", [item["id"] for item in first["support_destinations"]])
        self.assertNotIn("order_outcome", str(first["next_question"]))

        initiated = build_adaptive_workflow(
            story + "\nThe Dashboard says Initiated.", previous=first, intake_complete=True
        )
        self.assertEqual(initiated["stage"], "gateway_settlement_overdue")
        self.assertIn("four days", initiated["message"])
        self.assertIn("twelve days", initiated["message"])
        self.assertIn("settlement ID", initiated["current_step"]["detail"])
        self.assertIn("Dashboard", initiated["support_draft"]["message"])

        processed = build_adaptive_workflow(
            story + "\nThe Dashboard says Processed.", previous=first, intake_complete=True
        )
        self.assertEqual(processed["stage"], "gateway_settlement_processed_trace")
        self.assertIn("UTR", processed["message"])
        failed = build_adaptive_workflow(
            story + "\nThe Dashboard says Failed.", previous=first, intake_complete=True
        )
        self.assertEqual(failed["stage"], "gateway_settlement_failed")
        self.assertIn("failure reason", failed["message"].lower())

    def test_reopened_case_collects_update_until_user_finishes(self):
        workflow = build_adaptive_workflow(
            "Meesho refund of ₹3,000 not received. Return picked up. Refund initiated.",
            previous={"intake_complete": True, "collecting_update": True}, intake_complete=True,
        )
        self.assertEqual(workflow["status"], "collecting_update")
        self.assertTrue(workflow["collecting_update"])
        self.assertIsNone(workflow["next_question"])


if __name__ == "__main__":
    unittest.main()
