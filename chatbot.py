"""
Datheon Python Programming Internship - Task 4: Rule-Based Interactive Chatbot

A customer support assistant for a terminal-based demonstration store:
- Normalizes user text and uses regular expressions with word boundaries (\b).
- Supports 11 core customer support intents:
  1. Greetings
  2. Business Hours
  3. Product FAQs
  4. Pricing
  5. Payment Methods
  6. Order Tracking
  7. Delivery Information
  8. Returns & Refunds
  9. Contact Information
  10. Thanks
  11. Goodbye
- Detects multiple intents in a single message without duplicate responses.
- Distinguishes standalone exit commands ('exit', 'quit', 'bye') from contextual questions.
- Clearly states all store policies, hours, and contact details as fictional demonstration content.
- Never claims access to private user data or live customer orders.
- Handles empty input, EOF, and keyboard interruptions gracefully.
"""

import json
from pathlib import Path
import re
import sys

DEFAULT_FAQS_FILE = Path("sample_data") / "faqs.json"


def load_faqs_data(faqs_path=DEFAULT_FAQS_FILE):
    """
    Loads custom FAQs and greetings from a JSON file if present.
    Returns (greetings_list, faqs_list).
    """
    path = Path(faqs_path)
    if path.exists() and path.is_file():
        try:
            with open(path, mode="r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("greetings", []), data.get("faqs", [])
        except (json.JSONDecodeError, OSError):
            pass
    return [], []


# Rule-based intent definitions with regex patterns and contextual responses
INTENT_RULES = [
    {
        "intent": "greeting",
        "patterns": [
            r"\b(hello|hi|hey|greetings|howdy)\b",
            r"\bgood\s+(morning|afternoon|evening)\b"
        ],
        "response": "Hello! Welcome to Support Bot (demonstration store and internship assistant). How can I help you today?"
    },
    {
        "intent": "business_hours",
        "patterns": [
            r"\b(business\s+)?hours(\s+of\s+operation)?\b",
            r"\bopening\s+(hours|times)\b",
            r"\bwhen\s+(are\s+you|do\s+you)\s+open\b",
            r"\boperating\s+hours\b",
            r"\bworking\s+hours\b",
            r"\bclosing\s+time\b"
        ],
        "response": "We operate Monday through Friday from 9:00 AM to 6:00 PM IST."
    },
    {
        "intent": "internship_submission",
        "patterns": [
            r"\b(submit|submission)\b.*\b(project|internship|github)\b",
            r"\bhow\s+(do|can)\s+i\s+submit\b",
            r"\bproject\s+submission\b"
        ],
        "response": "You can submit your public GitHub repository link through your Student Workspace."
    },
    {
        "intent": "certificate_inquiry",
        "patterns": [
            r"\b(when\s+will\s+i\s+receive\s+my\s+)?certificate\b",
            r"\bcertificate\s+(issuance|timeline|review)\b",
            r"\breceive\s+(my\s+)?certificate\b"
        ],
        "response": "Certificates are reviewed and issued within 3-5 business days after your code review."
    },
    {
        "intent": "product_faqs",
        "patterns": [
            r"\b(what\s+do\s+you\s+sell|what\s+products|product\s+(catalog|list|range|types|line))\b",
            r"\b(catalog|inventory|merchandise)\b",
            r"\bwhat\s+(items|products)\s+(do\s+you\s+have|are\s+available)\b"
        ],
        "response": "Our sample store catalog features computer accessories, developer gadgets, coding merchandise, and electronics."
    },
    {
        "intent": "pricing",
        "patterns": [
            r"\b(price|pricing|cost|costs|rates?|fees?)\b",
            r"\bhow\s+much\b",
            r"\bsubscription\s+(cost|plan|pricing|fee)\b"
        ],
        "response": "Our sample item prices range from $15 to $299. All prices are listed in USD with taxes calculated at checkout."
    },
    {
        "intent": "payment_methods",
        "patterns": [
            r"\b(payment\s+methods?|ways?\s+to\s+pay|how\s+(can|do)\s+i\s+pay)\b",
            r"\b(credit\s+card|debit\s+card|paypal|apple\s+pay|google\s+pay|cash|upi|net\s*banking)\b"
        ],
        "response": "We accept major credit cards (Visa, MasterCard, Amex), PayPal, Apple Pay, Google Pay, and UPI."
    },
    {
        "intent": "order_tracking",
        "patterns": [
            r"\btrack(\s+my)?\s+order\b",
            r"\border\s+(status|tracking|number)\b",
            r"\bwhere\s+is\s+my\s+(order|package|shipment)\b"
        ],
        "response": "To track an order in this demo system, check your order confirmation email for a fictional tracking link. (Note: As an automated rule-based demo, I do not have access to live customer account databases)."
    },
    {
        "intent": "delivery_info",
        "patterns": [
            r"\b(delivery|shipping|dispatch)\b",
            r"\bhow\s+long\s+(does|will)\s+(shipping|delivery)\s+take\b",
            r"\bshipping\s+(time|policy|rates?|cost|options)\b"
        ],
        "response": "Standard shipping takes 3-5 business days. Express 2-day delivery is also available for urgent demonstration orders."
    },
    {
        "intent": "returns_refunds",
        "patterns": [
            r"\b(returns?|refunds?|exchange|exchanges)\b",
            r"\bmoney\s*back\b",
            r"\breturn\s+policy\b"
        ],
        "response": "Our demonstration return policy allows returns within 30 days of delivery. Refunds are credited back to the original payment method within 5 business days."
    },
    {
        "intent": "contact_info",
        "patterns": [
            r"\b(contact|email|phone|call\s+us|customer\s+(service|support)|reach\s+(you|support))\b",
            r"\bspeak\s+to\s+(a\s+human|an\s+agent|someone)\b"
        ],
        "response": "You can reach our sample support team at support@example.com or phone 1-800-555-DEMO (Mon-Fri, 9am-6pm EST)."
    },
    {
        "intent": "thanks",
        "patterns": [
            r"\b(thank\s+you|thanks|thx|appreciate\s+it|grateful)\b"
        ],
        "response": "You're very welcome! Let me know if you have any other questions."
    },
    {
        "intent": "goodbye",
        "patterns": [
            r"\b(bye|goodbye|see\s+you|farewell|have\s+a\s+good\s+day)\b"
        ],
        "response": "Goodbye! Thank you for visiting our demo store. Have a wonderful day!"
    }
]

FALLBACK_RESPONSE = (
    "I'm sorry, I didn't quite catch that. You can ask me about:\n"
    "  - Hours of operation\n"
    "  - How to submit internship project\n"
    "  - When will certificate be issued\n"
    "  - Product catalog & pricing\n"
    "  - Payment methods & delivery\n"
    "  - Returns & refunds\n"
    "  - Customer support contact info\n"
    "Or type 'exit' to end our chat."
)


def normalize_input(raw_text):
    """
    Cleans and normalizes user input:
    - Strips leading and trailing whitespace
    - Converts to lowercase
    - Normalizes internal multiple spaces to a single space
    """
    if raw_text is None:
        return ""
    stripped = raw_text.strip().lower()
    return re.sub(r"\s+", " ", stripped)


def is_exit_command(text):
    """
    Checks if the user gave an explicit command to exit the session.
    Matches commands like 'exit', 'quit', 'bye', 'goodbye', 'exit please', etc.
    Avoids false positives on sentences that merely mention exit/quit in a question.
    """
    normalized = normalize_input(text)
    exit_patterns = [
        r"^(exit|quit|bye|goodbye)(\s+(now|please))?$",
        r"^(q)$"
    ]
    return any(re.match(pattern, normalized) for pattern in exit_patterns)


def match_intents(user_text):
    """
    Evaluates normalized user input against the intent rules.
    Returns: list of unique matched intent names and list of unique response strings.
    If no intents match, returns ([], [FALLBACK_RESPONSE]).
    """
    normalized = normalize_input(user_text)

    if not normalized:
        return [], ["Please enter a question or message, or type 'exit' to quit."]

    matched_intents = []
    matched_responses = []

    for rule in INTENT_RULES:
        intent_name = rule["intent"]
        for pattern in rule["patterns"]:
            if re.search(pattern, normalized):
                if intent_name not in matched_intents:
                    matched_intents.append(intent_name)
                    matched_responses.append(rule["response"])
                break  # Move to next rule once this rule has matched

    if not matched_responses:
        return [], [FALLBACK_RESPONSE]

    return matched_intents, matched_responses


def get_chatbot_reply(user_text):
    """
    Generates the composite reply string for a user message.
    Separates multiple intent responses with blank lines.
    """
    intents, responses = match_intents(user_text)
    return "\n\n".join(responses)


def run_chatbot_session(input_func=input, print_func=print):
    """
    Runs the interactive chatbot loop in the terminal until exit is triggered.
    """
    print_func("\n" + "=" * 65)
    print_func("     SUPPORT BOT - DEMONSTRATION CUSTOMER ASSISTANT")
    print_func("=" * 65)
    print_func("Ask me questions about store hours, products, shipping, returns,")
    print_func("payment methods, pricing, or order tracking.")
    print_func("[DISCLAIMER] All policies, hours, and contact info are fictional")
    print_func("             demonstration content for this student project.")
    print_func("Type 'exit', 'quit', or 'bye' at any time to leave.\n")

    while True:
        try:
            user_input = input_func("You: ")
        except (KeyboardInterrupt, EOFError):
            print_func("\n\nSession terminated by user. Goodbye!")
            break

        if is_exit_command(user_input):
            print_func("\nSupport Bot: Goodbye! Thank you for visiting our demo store. Have a great day!\n")
            break

        reply = get_chatbot_reply(user_input)
        print_func(f"\nSupport Bot: {reply}\n")


def main():
    """Main entry point."""
    run_chatbot_session()


if __name__ == "__main__":
    main()
