# SmartSupport — Rule-Based Customer Support Chatbot

## 1. Project Overview

SmartSupport is a **rule-based** customer support chatbot built for an e-commerce
use case. It answers common support questions — order status, cancellations,
returns, payments, delivery and more — using keyword matching, regular
expressions and a simple scoring system, without any Machine Learning, Deep
Learning, or external AI/LLM APIs.

## 2. Real-World Problem

E-commerce companies receive a large volume of repetitive support questions
("Where is my order?", "How do I get a refund?"). Routing every one of these
to a human agent is slow and expensive. Most of these questions are
predictable and can be answered by recognizing a small set of *intents* and
returning a pre-written, helpful response.

## 3. Proposed Solution

SmartSupport recognizes the customer's **intent** from free-form text using
keyword, phrase and regex rules, scores every possible intent, and returns
the best-matching predefined response — instantly, 24/7, with no AI model
required. If no intent matches confidently, it falls back to a friendly
clarifying message instead of guessing.

## 4. Features

- 18 supported support intents (10 required + 8 additional real-world use cases)
- Keyword + phrase + regex based intent recognition with additive scoring
- Multiple response variants per intent (feels less robotic/repetitive)
- Rotating fallback responses for unrecognized queries
- Simple session-based conversation memory (Flask sessions) with basic
  context resolution for short follow-up messages (e.g. "cancel **it**")
- Clean, modern, mobile-responsive chat UI
- Quick-action buttons for the most common requests
- JavaScript-only typing indicator
- Message timestamps and auto-scroll
- 40+ automated tests covering intents and edge cases

## 5. Supported Intents

| # | Intent                  | Example query                              |
|---|--------------------------|---------------------------------------------|
| 1 | `greeting`               | "hi", "good morning"                        |
| 2 | `order_status`           | "where is my order"                          |
| 3 | `order_cancellation`     | "cancel my order"                            |
| 4 | `return_refund`          | "I want a refund"                            |
| 5 | `payment`                | "payment failed"                             |
| 6 | `delivery`               | "how long does delivery take"                |
| 7 | `product_information`    | "product specifications"                     |
| 8 | `customer_support`       | "talk to an agent"                           |
| 9 | `goodbye`                | "bye"                                        |
| 10| `help`                   | "what can you do"                            |
| 11| `account_login`          | "forgot my password"                         |
| 12| `invoice_billing`        | "I need a GST invoice"                       |
| 13| `coupon_discount`        | "coupon code isn't working"                  |
| 14| `product_exchange`       | "wrong size, want to exchange"               |
| 15| `warranty_claim`         | "is this under warranty"                     |
| 16| `complaint_feedback`     | "I want to file a complaint"                 |
| 17| `order_modification`     | "change my delivery address"                 |
| 18| `international_shipping` | "do you ship internationally"                |
| — | `general_order_issue`    | "problem with my order" (triggers a clarifying follow-up, used to demo context handling) |

## 6. Technology Stack

**Backend:** Python 3, Flask, `re` (Regular Expressions), Flask sessions
**Frontend:** HTML5, CSS3, vanilla JavaScript (no frontend framework)
**Testing:** pytest (or plain `python` — both work)
**No database. No external AI API of any kind.**

## 7. System Architecture

```
User
  ↓
Web Chat UI (HTML/CSS/JS)
  ↓
Flask API (app.py)
  ↓
Text Preprocessing (chatbot.py)
  ↓
Keyword + Regex Matching
  ↓
Intent Scoring
  ↓
Intent Selection (+ simple context resolution)
  ↓
Rule-Based Response
  ↓
Chat UI
```

## 8. Intent Recognition Method

`recognize_intent(user_message, last_intent=None)` in `chatbot.py`:

1. **Preprocess** — lowercase the text, collapse repeated punctuation
   (`"???"` → `"?"`), strip punctuation (keeping apostrophes), normalize
   whitespace.
2. **Score every intent** — for each configured intent, check:
   - individual **keywords** (+1 point each)
   - specific **phrases** (+2 points each)
   - **regex patterns** (+3 points each)
3. **Select the best match** — the intent with the highest total score wins.
4. **Threshold check** — if the best score is below `MIN_SCORE_THRESHOLD`
   (2), the message is considered too ambiguous for a direct match.
5. **Context fallback** — for vague follow-ups (e.g. "cancel it"), a small
   rule-based lookup (`resolve_context_followup`) uses the *previous*
   intent plus an action word ("cancel", "track", "return"...) to infer the
   intent — no AI, just a dictionary lookup.
6. **Unknown** — if nothing matches, the intent is `"unknown"` and a
   rotating fallback response is returned.

## 9. Rule-Based Matching Logic (Scoring Example)

```
Message: "Can you tell me where my order is?"

order_status intent:
  phrase match "where is my order"-like regex   -> +3  (pattern)
  keyword "status" not present                  -> +0
  ---------------------------------------------------
  Total score: 3   (>= threshold of 2)  -> MATCH
```

This demonstrates the chatbot does more than simple `if/else` string
comparisons — it combines multiple weighted signals per message.

## 10. Project Structure

```
SmartSupport/
│
├── app.py                  # Flask server, routes, sessions
├── chatbot.py               # Preprocessing, rules, scoring, responses
├── requirements.txt
├── README.md
│
├── templates/
│   └── index.html            # Chat UI markup
│
├── static/
│   ├── style.css              # Full UI styling
│   └── script.js               # Chat behavior (send, render, typing, clear)
│
└── tests/
    └── test_chatbot.py          # 40+ automated tests
```

## 11. Installation

```bash
# 1. Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt
```

## 12. Running the Application

```bash
python app.py
```

Then open your browser at:

```
http://127.0.0.1:5000
```

## 13. Testing

```bash
# Using pytest
python -m pytest tests/test_chatbot.py -v

# Or run directly
python tests/test_chatbot.py
```

The test suite covers all 18 intents with multiple phrasing variations, plus
edge cases: empty input, whitespace-only input, uppercase/mixed-case text,
extra spaces, punctuation spam, unknown questions, special characters, very
long input, and simple conversation-context resolution.

## 14. Example Conversations

```
Bot:  Hello! 👋 Welcome to SmartSupport. How can I help you today?
User: Where's my package?
Bot:  You can track your order from the Orders section of your account.
      If you need further assistance, please contact customer support
      with your order ID.

User: I have a problem with my order.
Bot:  Sure! What would you like help with — tracking, cancellation or return?
User: I want to cancel it.
Bot:  If your order has not been shipped yet, you may be able to cancel it
      from your Orders section. Otherwise, please contact customer support.

User: WHERE IS MY ORDER???
Bot:  You can track your order from the Orders section of your account...

User: asdkjfh random text
Bot:  I'm not sure I understood that. 🤔 Could you rephrase your question?
```

## 15. Limitations

- Cannot understand queries outside the predefined intents/rules.
- Context handling is intentionally simple (one previous intent, a small
  set of pronouns/action words) — not a general conversational memory.
- No real integration with an actual order/inventory/payment system; all
  responses are generic guidance text.
- No spelling-correction; badly misspelled queries may fall back to "unknown".
- Conversation history is stored in the Flask session (server-side, in
  memory by default) and is not persisted to a database.

## 16. Future Enhancements

*(Not implemented — listed only as possible future directions)*

- Machine Learning-based intent classification
- Multilingual support
- Database integration for real conversation/ticket storage
- Real order tracking API integration
- Human-agent escalation workflow
- Sentiment analysis on customer messages
- Voice interface
- LLM-based conversational understanding

## 17. How the Chatbot Works (Short Explanation)

The chatbot never "understands" language the way an AI model would. Instead,
every message is cleaned up and compared against a table of hand-written
keywords, phrases and regex patterns for each topic (intent). Each match adds
points to that topic's score. Whichever topic scores highest — and clears a
minimum threshold — is treated as the customer's intent, and one of several
pre-written responses for that topic is shown. If nothing scores high enough,
the bot asks the user to rephrase instead of guessing.

## 18. Internship Presentation / Viva Summary

> "SmartSupport is a rule-based chatbot — meaning all of its responses come
> from predefined rules, not from a trained AI model. I built an intent
> recognition system that combines keyword matching, phrase matching and
> regular expressions with a simple point-scoring system to figure out what
> the customer is asking about, across 18 different support topics. The
> Flask backend keeps the chatbot logic (`chatbot.py`) completely separate
> from the web server and routing (`app.py`), and Flask sessions let the bot
> remember the last topic discussed so it can handle short follow-up
> messages like 'cancel it'. I also wrote 40+ automated tests to make sure
> the rules work correctly, including tricky edge cases like empty input,
> shouted text, and typos in punctuation."

---

**Why is this a RULE-BASED chatbot and not an AI chatbot?**
Every response the bot gives is one of a small number of hand-written
sentences, selected by hand-written matching rules (keywords/phrases/regex)
that a developer wrote in advance. There is no model that was trained on
data to "learn" language, and no external AI service is called at any point
— the entire decision process is deterministic and fully explainable, which
is exactly what makes it suitable for a rule-based systems assignment.
