"""
chatbot.py
----------
Core logic for SmartSupport — a RULE-BASED customer support chatbot.

No Machine Learning, Deep Learning, LLMs or external AI APIs are used anywhere
in this file. All "intelligence" comes from:
    - text preprocessing
    - keyword matching
    - regular expression (regex) matching
    - a simple additive scoring system
    - a small amount of session-context awareness (for follow-up messages)

This module is intentionally kept independent of Flask so it can be tested
and reused on its own (see tests/test_chatbot.py).
"""

import re
import random
import string

# ======================================================================
# 1. TEXT PREPROCESSING
# ======================================================================

def preprocess_text(text: str) -> str:
    """
    Clean and normalize user input:
      - lowercase everything
      - collapse repeated punctuation (e.g. "???" -> "?")
      - strip most punctuation (keep apostrophes so "don't" stays intact)
      - normalize whitespace (multiple spaces/tabs -> single space)
      - trim leading/trailing whitespace
    """
    if not text:
        return ""

    text = text.lower()

    # Collapse repeated punctuation like "!!!" or "???" down to one character
    text = re.sub(r"([!?.,])\1+", r"\1", text)

    # Remove punctuation except apostrophes (so "don't" / "can't" survive)
    keep = "'"
    text = "".join(ch for ch in text if ch not in string.punctuation or ch in keep)

    # Normalize all whitespace (spaces, tabs, newlines) to single spaces
    text = re.sub(r"\s+", " ", text).strip()

    return text


# ======================================================================
# 2. INTENT CONFIGURATION
# ======================================================================
# Each intent has:
#   keywords : list of individual words/short phrases  -> +1 point each
#   phrases  : more specific multi-word phrases         -> +2 points each
#   patterns : compiled regex patterns                  -> +3 points each
#   responses: list of possible responses (chosen randomly for variety)

INTENTS = {

    "greeting": {
        "keywords": ["hi", "hello", "hey", "yo", "hiya"],
        "phrases": ["good morning", "good evening", "good afternoon", "what's up"],
        "patterns": [r"\bhe?llo+\b", r"\bhi+\b", r"\bhey+\b", r"\byo+\b"],
        "responses": [
            "Hello! 👋 Welcome to SmartSupport. How can I help you today?",
            "Hi there! 😊 I'm SmartSupport — ask me about orders, returns, payments or delivery.",
        ],
    },

    "order_status": {
        "keywords": ["track", "tracking", "status"],
        "phrases": [
            "where is my order", "where is my package", "where's my order",
            "track my order", "order status", "check my delivery",
            "my parcel hasn't arrived", "when will my order arrive",
        ],
        "patterns": [
            r"\bwhere('?s| is)?\s+my\s+(order|package|parcel)\b",
            r"\btrack(ing)?\s+my\s+(order|package|parcel)\b",
            r"\bwhen\s+(will|does)\s+.*\b(order|package|parcel)\b.*\b(arrive|come|reach)\b",
        ],
        "responses": [
            "You can track your order from the Orders section of your account. If you need further assistance, please contact customer support with your order ID.",
            "Sure! You can check your order status from the Orders section of your account. If you have an order ID, you can also provide it to customer support.",
        ],
    },

    "order_cancellation": {
        "keywords": ["cancel", "cancellation"],
        "phrases": [
            "cancel my order", "cancel my purchase", "how can i cancel",
            "want to cancel", "cancel it",
        ],
        "patterns": [
            r"\bcancel\b.*\b(order|purchase|it)\b",
            r"\bhow\s+(can|do)\s+i\s+cancel\b",
        ],
        "responses": [
            "If your order has not been shipped yet, you may be able to cancel it from your Orders section. Otherwise, please contact customer support.",
            "You can cancel unshipped orders directly from the Orders page. If it's already shipped, our support team can help.",
        ],
    },

    "return_refund": {
        "keywords": ["return", "refund", "returned", "returning", "damaged", "defective", "broken"],
        "phrases": [
            "return my product", "return my order", "get a refund",
            "damaged product", "product return", "want to return",
            "return something",
        ],
        "patterns": [
            r"\breturn\b.*\b(product|order|item|something)\b",
            r"\bhow\s+(do|can)\s+i\s+return\b",
            r"\brefund\b",
            r"\b(damaged|defective|broken)\b",
        ],
        "responses": [
            "You can request a return from your Orders section. Refund eligibility may depend on the product and return policy.",
            "Sorry about that! Please start a return request from the Orders section — refunds are processed once the item is received back.",
        ],
    },

    "payment": {
        "keywords": ["payment", "transaction", "charged", "deducted"],
        "phrases": [
            "payment failed", "payment problem", "payment didn't work",
            "money was deducted", "payment issue", "transaction failed",
        ],
        "patterns": [
            r"\bpayment\s+(failed|issue|problem|didn'?t\s+work)\b",
            r"\b(money|amount)\s+(was\s+)?deducted\b",
            r"\btransaction\s+failed\b",
        ],
        "responses": [
            "If your payment failed but the amount was deducted, please wait for the transaction to be processed or reversed. If the issue continues, contact customer support with your transaction details.",
            "Payment issues are usually resolved automatically within a few hours. If money was deducted without order confirmation, it will be refunded — contact support if it takes longer than 3-5 business days.",
        ],
    },

    "delivery": {
        "keywords": ["delivery", "shipping"],
        "phrases": [
            "delivery time", "shipping time", "how long does delivery take",
            "delivery information", "when will it arrive",
        ],
        "patterns": [
            r"\bhow\s+long\s+.*\bdeliver",
            r"\bdelivery\s+(time|information|estimate)\b",
            r"\bshipping\s+time\b",
        ],
        "responses": [
            "Delivery time depends on your location and the selected shipping option. You can check the estimated delivery date during checkout or from your order details.",
            "Most orders are delivered within 3-7 business days depending on your location — check your order page for the exact estimate.",
        ],
    },

    "product_information": {
        "keywords": ["specifications", "specs", "warranty"],
        "phrases": [
            "tell me about the product", "product details", "product information",
            "does this product have warranty",
        ],
        "patterns": [
            r"\bproduct\s+(details|information|specs|specifications)\b",
            r"\bwhat\s+are\s+the\s+specifications\b",
        ],
        "responses": [
            "You can find product specifications, availability and warranty information on the product details page.",
            "Full product details — specs, materials and warranty — are listed on the product's page under the 'Details' tab.",
        ],
    },

    "customer_support": {
        "keywords": ["support", "agent", "representative"],
        "phrases": [
            "contact support", "talk to an agent", "customer care",
            "contact customer service", "need human support", "talk to a human",
        ],
        "patterns": [
            r"\bcontact\s+(support|customer\s+(service|care))\b",
            r"\btalk\s+to\s+(an?\s+)?(agent|human|representative)\b",
        ],
        "responses": [
            "Sure! Please contact our customer support team through the Support section for assistance from a human representative.",
            "You can reach a human agent anytime via the Support section, or email us — we usually reply within 24 hours.",
        ],
    },

    "goodbye": {
        "keywords": ["bye", "goodbye", "exit", "quit"],
        "phrases": ["see you", "thanks bye", "thank you bye"],
        "patterns": [r"\bbye+\b", r"\bgood\s*bye\b"],
        "responses": [
            "Thank you for contacting SmartSupport! 👋 Have a great day.",
            "Glad I could help! 👋 Feel free to come back anytime.",
        ],
    },

    "help": {
        "keywords": ["help", "options", "menu"],
        "phrases": ["what can you do", "what do you support"],
        "patterns": [r"\bwhat\s+can\s+you\s+do\b", r"^help$"],
        "responses": [
            "I can help you with order tracking, cancellations, returns, refunds, payments, delivery, product information and customer support.",
            "Ask me about: order status, cancellations, returns/refunds, payments, delivery times, product info, account issues, invoices, coupons, exchanges, warranty or contacting support!",
        ],
    },

    # --------------------------------------------------------------
    # EXTRA USE-CASE INTENTS (added beyond the original requirement)
    # --------------------------------------------------------------

    "account_login": {
        "keywords": ["login", "password", "signin", "account"],
        "phrases": [
            "can't login", "cannot login", "forgot password", "reset password",
            "account locked", "unable to sign in", "trouble logging in",
        ],
        "patterns": [
            r"\b(can'?t|cannot|unable\s+to)\s+(log\s*in|sign\s*in)\b",
            r"\b(forgot|reset)\s+(my\s+)?password\b",
            r"\baccount\s+(is\s+)?locked\b",
        ],
        "responses": [
            "You can reset your password using the 'Forgot Password' link on the login page. If your account is locked, please contact support.",
            "Try resetting your password from the login screen. If that doesn't work or your account seems locked, our support team can help you regain access.",
        ],
    },

    "invoice_billing": {
        "keywords": ["invoice", "bill", "billing", "gst"],
        "phrases": ["need invoice", "billing details", "gst invoice", "download invoice"],
        "patterns": [
            r"\b(gst\s+)?invoice\b",
            r"\bbilling\s+(details|information)\b",
        ],
        "responses": [
            "You can download your invoice from the Orders section under 'Invoice/Bill'. For GST invoices, make sure your GSTIN is added to your profile before ordering.",
            "Invoices are auto-generated and available in the Orders section a few hours after your order is confirmed.",
        ],
    },

    "coupon_discount": {
        "keywords": ["coupon", "promo", "discount", "offer"],
        "phrases": [
            "coupon not working", "promo code", "discount code invalid",
            "offer code", "code isn't working",
        ],
        "patterns": [
            r"\b(coupon|promo|discount|offer)\s+code\b",
            r"\b(coupon|code)\s+(not\s+working|invalid|isn'?t\s+working)\b",
        ],
        "responses": [
            "Please check that your coupon code hasn't expired and meets the minimum order value. If it still doesn't work, try a different browser or contact support.",
            "Coupon codes are usually case-sensitive and have minimum order or category restrictions — double check the terms, or reach out to support for help.",
        ],
    },

    "product_exchange": {
        "keywords": ["exchange", "swap"],
        "phrases": [
            "exchange product", "wrong size", "exchange for different size",
            "swap item", "exchange item",
        ],
        "patterns": [
            r"\bexchange\b.*\b(product|item|order|size)\b",
            r"\bwrong\s+size\b",
        ],
        "responses": [
            "You can request an exchange from the Orders section if the product is eligible. Choose 'Exchange' instead of 'Return' during the request.",
            "Size or variant exchanges are available for eligible products — start the request from your Orders page within the return window.",
        ],
    },

    "warranty_claim": {
        "keywords": ["warranty", "repair"],
        "phrases": [
            "warranty claim", "product under warranty", "repair request",
            "warranty period",
        ],
        "patterns": [
            r"\bwarranty\s+(claim|period)\b",
            r"\brepair\s+request\b",
            r"\bwarranty\b",
        ],
        "responses": [
            "For warranty claims, please check the warranty card included with your product or visit the brand's authorized service center listed on the product page.",
            "Warranty claims are usually handled directly by the manufacturer — check the product page for their service center details, or contact our support for guidance.",
        ],
    },

    "complaint_feedback": {
        "keywords": ["complaint", "feedback", "unhappy", "disappointed"],
        "phrases": [
            "file a complaint", "bad experience", "poor service", "not satisfied",
        ],
        "patterns": [
            r"\bfile\s+a\s+complaint\b",
            r"\b(bad|poor)\s+(experience|service)\b",
        ],
        "responses": [
            "We're sorry to hear that. Please share your feedback in detail through the Support section so our team can address it promptly.",
            "Thank you for letting us know — your feedback helps us improve. Please submit the details via the Support section and our team will follow up.",
        ],
    },

    "order_modification": {
        "keywords": ["address", "modify"],
        "phrases": [
            "change delivery address", "update address", "edit order",
            "change phone number on order", "update my address",
        ],
        "patterns": [
            r"\b(change|update|edit)\s+.*\baddress\b",
            r"\bedit\s+(my\s+)?order\b",
        ],
        "responses": [
            "You can update the delivery address only before the order is shipped, from the Orders section. Once shipped, please contact support for assistance.",
            "Address changes are possible until the order is packed for shipping — check the Orders section, or contact support if it's already on its way.",
        ],
    },

    "international_shipping": {
        "keywords": ["international", "overseas", "abroad"],
        "phrases": [
            "do you ship internationally", "international delivery",
            "ship outside india", "overseas shipping",
        ],
        "patterns": [
            r"\bship\s+(internationally|outside|abroad|overseas)\b",
            r"\binternational\s+(shipping|delivery)\b",
        ],
        "responses": [
            "International shipping availability depends on the product and destination country. Check the product page or contact support for details.",
            "Not all products ship internationally — look for the 'Ships to' info on the product page, or ask support to confirm for your country.",
        ],
    },

    # --------------------------------------------------------------
    # A deliberately "vague" intent used to demonstrate simple
    # conversation-context handling (see resolve_context_followup below)
    # --------------------------------------------------------------
    "general_order_issue": {
        "keywords": [],
        "phrases": [
            "problem with my order", "issue with my order", "issue with order",
            "something wrong with my order",
        ],
        "patterns": [r"\b(problem|issue)\s+with\s+my\s+order\b"],
        "responses": [
            "Sure! What would you like help with — tracking, cancellation or return?",
        ],
    },
}

# Compile all regex patterns once, up front, for speed
for _intent, _cfg in INTENTS.items():
    _cfg["compiled_patterns"] = [re.compile(p) for p in _cfg.get("patterns", [])]


# ======================================================================
# 3. FALLBACK RESPONSES
# ======================================================================

FALLBACK_RESPONSES = [
    "I'm not sure I understood that. 🤔 Could you rephrase your question?",
    "I couldn't find a matching support topic. You can ask me about orders, refunds, payments, delivery or returns.",
    "Sorry, I don't have information about that yet. Try asking about one of the available support topics.",
    "Hmm, I didn't quite catch that. Try one of the quick-action buttons below, or ask about orders, payments or returns.",
]

MIN_SCORE_THRESHOLD = 2  # minimum score an intent needs to be selected

# Words that hint the user is referring back to something mentioned earlier
CONTEXT_PRONOUNS = ["it", "that", "this one", "this order", "this"]

# Maps an action-word found in a vague follow-up message to a concrete intent
FOLLOWUP_ACTION_MAP = {
    "cancel": "order_cancellation",
    "track": "order_status",
    "status": "order_status",
    "return": "return_refund",
    "refund": "return_refund",
    "exchange": "product_exchange",
}


# ======================================================================
# 4. SCORING / INTENT RECOGNITION
# ======================================================================

def _score_intent(cleaned_text: str, cfg: dict) -> int:
    """Compute a simple additive score for one intent against the cleaned text."""
    score = 0

    for kw in cfg.get("keywords", []):
        if re.search(rf"\b{re.escape(kw)}\b", cleaned_text):
            score += 1

    for phrase in cfg.get("phrases", []):
        if phrase in cleaned_text:
            score += 2

    for pattern in cfg.get("compiled_patterns", []):
        if pattern.search(cleaned_text):
            score += 3

    return score


def resolve_context_followup(cleaned_text: str, last_intent: str):
    """
    Very simple rule-based context resolution for short follow-up messages
    like "cancel it" or "I want to track that", when the main scoring pass
    didn't find a confident match. This is NOT machine learning — just a
    small lookup based on the previous topic and an action word.
    """
    if not last_intent:
        return None

    has_pronoun = any(p in cleaned_text for p in CONTEXT_PRONOUNS)
    if not has_pronoun and last_intent != "general_order_issue":
        return None

    for action_word, mapped_intent in FOLLOWUP_ACTION_MAP.items():
        if action_word in cleaned_text:
            return mapped_intent

    return None


def recognize_intent(user_message: str, last_intent: str = None):
    """
    Main intent recognition function.

    Steps:
      1. Preprocess the text (lowercase, strip punctuation, normalize spaces)
      2. Score every intent using keyword / phrase / regex matches
      3. Pick the highest scoring intent
      4. If no intent scores high enough, try simple context-based resolution
      5. Otherwise, return "unknown"

    Returns: (intent_name: str, score: int)
    """
    cleaned = preprocess_text(user_message)

    if not cleaned:
        return "unknown", 0

    scores = {intent: _score_intent(cleaned, cfg) for intent, cfg in INTENTS.items()}
    best_intent = max(scores, key=scores.get)
    best_score = scores[best_intent]

    if best_score >= MIN_SCORE_THRESHOLD:
        return best_intent, best_score

    # Try resolving vague follow-up messages using simple context rules
    context_intent = resolve_context_followup(cleaned, last_intent)
    if context_intent:
        return context_intent, MIN_SCORE_THRESHOLD  # treat as a confident match

    return "unknown", best_score


# ======================================================================
# 5. RESPONSE GENERATION
# ======================================================================

def get_response(intent: str) -> str:
    """Return a (randomly chosen, for variety) response for a given intent."""
    if intent == "unknown" or intent not in INTENTS:
        return random.choice(FALLBACK_RESPONSES)

    responses = INTENTS[intent].get("responses", [])
    if not responses:
        return random.choice(FALLBACK_RESPONSES)

    return random.choice(responses)


def get_bot_reply(user_message: str, last_intent: str = None):
    """
    Convenience wrapper used by the Flask app: given a raw user message and
    the previous intent (for context), returns (response_text, intent_name).
    """
    intent, _score = recognize_intent(user_message, last_intent=last_intent)
    response = get_response(intent)
    return response, intent
