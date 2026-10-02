"""
test_chatbot.py
----------------
Automated tests for the rule-based intent recognition in chatbot.py.

Run with:
    python -m pytest tests/test_chatbot.py -v

or simply:
    python tests/test_chatbot.py
"""

import os
import sys

# Allow running this file directly (adds the project root to the import path)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from chatbot import recognize_intent, preprocess_text, get_response  # noqa: E402


# ======================================================================
# 1. CORE INTENT TESTS (30+ queries covering every required intent)
# ======================================================================

CORE_CASES = [
    # Greeting
    ("Hi", "greeting"),
    ("Hello there", "greeting"),
    ("hey!!!", "greeting"),
    ("good morning", "greeting"),

    # Order status
    ("Where is my order?", "order_status"),
    ("Can I track my package?", "order_status"),
    ("When will my parcel arrive?", "order_status"),
    ("track my order", "order_status"),
    ("Where's my package", "order_status"),

    # Order cancellation
    ("I want to cancel my order", "order_cancellation"),
    ("Please cancel my purchase", "order_cancellation"),
    ("how can I cancel", "order_cancellation"),

    # Return / refund
    ("I want a refund", "return_refund"),
    ("How do I return something?", "return_refund"),
    ("My product arrived damaged", "return_refund"),
    ("return my order", "return_refund"),

    # Payment
    ("My payment failed", "payment"),
    ("Money was deducted but payment failed", "payment"),
    ("transaction failed", "payment"),

    # Delivery
    ("How long does delivery take?", "delivery"),
    ("What is the shipping time?", "delivery"),
    ("delivery information", "delivery"),

    # Product information
    ("Tell me about the product", "product_information"),
    ("Where can I find product specifications?", "product_information"),

    # Customer support
    ("How do I contact customer care?", "customer_support"),
    ("I want to talk to a human", "customer_support"),

    # Help
    ("Help", "help"),
    ("What can you do?", "help"),

    # Goodbye
    ("Bye", "goodbye"),
    ("thanks bye", "goodbye"),

    # Extra use-case intents
    ("I forgot my password", "account_login"),
    ("I need a GST invoice", "invoice_billing"),
    ("my coupon code isn't working", "coupon_discount"),
    ("I received the wrong size, can I exchange it", "product_exchange"),
    ("is my product still under warranty", "warranty_claim"),
    ("I want to file a complaint", "complaint_feedback"),
    ("I need to update my delivery address", "order_modification"),
    ("do you ship internationally", "international_shipping"),
]


def test_core_intents():
    passed, failed = 0, []
    for text, expected in CORE_CASES:
        intent, score = recognize_intent(text)
        if intent == expected:
            passed += 1
        else:
            failed.append((text, expected, intent, score))

    print(f"\nCore intent tests: {passed}/{len(CORE_CASES)} passed")
    for text, expected, got, score in failed:
        print(f"  FAILED: '{text}' -> expected '{expected}', got '{got}' (score={score})")

    assert not failed, f"{len(failed)} core intent test(s) failed"


# ======================================================================
# 2. EDGE CASE TESTS
# ======================================================================

def test_empty_input():
    intent, score = recognize_intent("")
    assert intent == "unknown"


def test_whitespace_only_input():
    intent, score = recognize_intent("      ")
    assert intent == "unknown"


def test_uppercase_text():
    intent, _ = recognize_intent("WHERE IS MY ORDER???")
    assert intent == "order_status"


def test_extra_spaces_and_punctuation():
    intent, _ = recognize_intent("   payment    failed   !!!   ")
    assert intent == "payment"


def test_mixed_case():
    intent, _ = recognize_intent("WheRe Is mY OrDeR")
    assert intent == "order_status"


def test_greeting_with_punctuation():
    intent, _ = recognize_intent("hi!!!")
    assert intent == "greeting"


def test_unknown_question():
    intent, _ = recognize_intent("what is the meaning of life")
    assert intent == "unknown"


def test_very_long_input():
    long_text = "I have a question " * 50 + "about my order status please"
    intent, _ = recognize_intent(long_text)
    # Should not crash, and should still lean towards order_status due to keyword presence
    assert intent in ("order_status", "unknown")


def test_special_characters():
    intent, _ = recognize_intent("@@@ where is my order### $$$")
    assert intent == "order_status"


def test_preprocess_normalizes_whitespace_and_case():
    result = preprocess_text("   HELLO    There!!!  ")
    # lowercased, punctuation stripped (only apostrophes are kept), spacing normalized
    assert result == "hello there"


# ======================================================================
# 3. CONVERSATION CONTEXT TEST
# ======================================================================

def test_context_followup_after_general_issue():
    # First message: vague general issue
    intent1, _ = recognize_intent("I have a problem with my order")
    assert intent1 == "general_order_issue"

    # Follow-up message referring back with "it" -> should resolve via context
    intent2, _ = recognize_intent("I want to cancel it", last_intent=intent1)
    assert intent2 == "order_cancellation"


# ======================================================================
# 4. RESPONSE GENERATION TEST
# ======================================================================

def test_get_response_returns_nonempty_string():
    response = get_response("order_status")
    assert isinstance(response, str) and len(response) > 0


def test_get_response_unknown_returns_fallback():
    response = get_response("unknown")
    assert isinstance(response, str) and len(response) > 0


# ======================================================================
# Allow running this file directly with `python tests/test_chatbot.py`
# ======================================================================

if __name__ == "__main__":
    test_functions = [
        test_core_intents,
        test_empty_input,
        test_whitespace_only_input,
        test_uppercase_text,
        test_extra_spaces_and_punctuation,
        test_mixed_case,
        test_greeting_with_punctuation,
        test_unknown_question,
        test_very_long_input,
        test_special_characters,
        test_preprocess_normalizes_whitespace_and_case,
        test_context_followup_after_general_issue,
        test_get_response_returns_nonempty_string,
        test_get_response_unknown_returns_fallback,
    ]

    passed, failed = 0, 0
    for fn in test_functions:
        try:
            fn()
            print(f"PASS: {fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL: {fn.__name__} -> {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
