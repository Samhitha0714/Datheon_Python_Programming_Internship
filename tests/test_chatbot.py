"""
Unit tests for Task 4: Rule-Based Interactive Chatbot (chatbot.py)
Tests cover all Datheon requirements:
- Each of the 11 supported intents individually
- Greetings
- Multiple intents recognized in a single compound sentence
- Prevention of duplicate intent responses
- Unknown questions triggering the friendly fallback
- Empty input handling
- Standalone exit commands vs contextual exit mentions
- Word boundary matching (\b)
- Case-insensitive and whitespace-tolerant matching
- Graceful termination in interactive session
"""

import unittest
import chatbot


class TestChatbotIntentMatching(unittest.TestCase):
    """Tests regex intent detection, normalization, and responses."""

    def test_all_individual_intents(self):
        """Verify each of the 11 intents is recognized with standard queries."""
        intent_samples = [
            ("greeting", "Hello there!"),
            ("business_hours", "What are your hours of operation?"),
            ("internship_submission", "How do I submit my internship project?"),
            ("certificate_inquiry", "When will I receive my certificate?"),
            ("product_faqs", "What products do you sell in your store?"),
            ("pricing", "What is the price of your merchandise?"),
            ("payment_methods", "What payment methods do you accept?"),
            ("order_tracking", "How do I track my order status?"),
            ("delivery_info", "How long will delivery and shipping take?"),
            ("returns_refunds", "What is your return policy and refund process?"),
            ("contact_info", "How can I contact customer support?"),
            ("thanks", "Thank you very much for the help!"),
            ("goodbye", "Goodbye for now!")
        ]

        for expected_intent, sample_text in intent_samples:
            intents, responses = chatbot.match_intents(sample_text)
            self.assertIn(
                expected_intent,
                intents,
                f"Failed to match intent '{expected_intent}' from input: '{sample_text}'"
            )
            self.assertTrue(len(responses) >= 1)

    def test_datheon_official_faq_exact_answers(self):
        """Verify the exact responses provided in Datheon's faqs.json."""
        reply1 = chatbot.get_chatbot_reply("What are your hours of operation?")
        self.assertIn("Monday through Friday from 9:00 AM to 6:00 PM IST", reply1)

        reply2 = chatbot.get_chatbot_reply("How do I submit my internship project?")
        self.assertIn("Student Workspace", reply2)

        reply3 = chatbot.get_chatbot_reply("When will I receive my certificate?")
        self.assertIn("3-5 business days after your code review", reply3)

    def test_load_faqs_data_from_json(self):
        """Verify load_faqs_data parses the sample_data/faqs.json file properly."""
        greetings, faqs = chatbot.load_faqs_data()
        self.assertIn("hello", greetings)
        self.assertTrue(len(faqs) >= 3)

    def test_case_insensitivity_and_whitespace(self):
        """Verify normalization handles strange casing and irregular spaces."""
        text = "   hElLo   !  wHaT   aRe   YoUr   bUsInEsS   hOuRs  ?  "
        intents, responses = chatbot.match_intents(text)
        self.assertIn("greeting", intents)
        self.assertIn("business_hours", intents)

    def test_multiple_intents_in_single_message(self):
        """Verify compound inquiries trigger all corresponding distinct responses."""
        compound = "Can you tell me about your pricing, accepted payment methods, and return policy?"
        intents, responses = chatbot.match_intents(compound)
        self.assertIn("pricing", intents)
        self.assertIn("payment_methods", intents)
        self.assertIn("returns_refunds", intents)
        self.assertEqual(len(intents), 3)
        self.assertEqual(len(responses), 3)

    def test_avoid_duplicate_responses_for_same_intent(self):
        """Verify multiple keywords for the same intent do NOT produce duplicate responses."""
        # Query contains multiple keywords matching 'pricing': 'price', 'cost', 'how much'
        text = "What is the price and cost, and how much are items?"
        intents, responses = chatbot.match_intents(text)
        self.assertEqual(intents.count("pricing"), 1)
        self.assertEqual(len(responses), 1)

    def test_word_boundary_isolation(self):
        """Verify word boundaries prevent substring false-positives."""
        # 'this' contains 'hi', 'shipment' contains 'hi', but should NOT trigger greeting
        intents, _ = chatbot.match_intents("This is a question about shipping.")
        self.assertNotIn("greeting", intents)
        self.assertIn("delivery_info", intents)

    def test_unknown_question_fallback(self):
        """Verify queries outside known intents trigger friendly fallback."""
        unrelated = "Can you write a poem about quantum physics in French?"
        intents, responses = chatbot.match_intents(unrelated)
        self.assertEqual(intents, [])
        self.assertEqual(len(responses), 1)
        self.assertIn("I'm sorry, I didn't quite catch that", responses[0])

    def test_empty_input_handling(self):
        """Verify empty or whitespace-only input returns a prompt rather than crashing."""
        for empty_val in ["", "   ", "\t\n", None]:
            intents, responses = chatbot.match_intents(empty_val)
            self.assertEqual(intents, [])
            self.assertIn("Please enter a question or message", responses[0])


class TestChatbotExitBehavior(unittest.TestCase):
    """Tests session exit detection and full interactive flow."""

    def test_is_exit_command_exact(self):
        """Verify standalone exit phrases are recognized."""
        valid_exits = ["exit", "QUIT", "bye", "goodbye", "exit please", "quit now", "q"]
        for cmd in valid_exits:
            self.assertTrue(chatbot.is_exit_command(cmd), f"Should match exit command: {cmd!r}")

    def test_is_exit_command_not_triggered_by_questions(self):
        """Verify questions that merely contain exit words do not trigger exit."""
        not_exits = [
            "How do I exit a subscription plan?",
            "Can I quit my account?",
            "I want to know if there is an exit fee"
        ]
        for sentence in not_exits:
            self.assertFalse(chatbot.is_exit_command(sentence), f"Should NOT exit on: {sentence!r}")

    def test_run_chatbot_session_flow(self):
        """Verify full simulated session with question and exit."""
        inputs = ["What are your business hours?", "exit"]
        outputs = []

        def mock_input(prompt):
            return inputs.pop(0)

        def mock_print(*args, **kwargs):
            outputs.append(" ".join(str(a) for a in args))

        chatbot.run_chatbot_session(input_func=mock_input, print_func=mock_print)

        combined = "\n".join(outputs)
        self.assertIn("Monday through Friday", combined)
        self.assertIn("Goodbye!", combined)


if __name__ == "__main__":
    unittest.main()
