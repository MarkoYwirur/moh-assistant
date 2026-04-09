# Product Overview

## What the product is

This product is an Armenian-language healthcare guidance backend for citizen-facing channels. It helps users understand what category their question belongs to, gives a policy-safe answer when the system has grounded coverage, and asks one focused clarification question when more context is needed.

It is designed for Ministry websites, partner portals, embedded web chat, and messaging-style integrations that need structured guidance rather than open-ended chatbot behavior.

## What it does

- Answers bounded healthcare guidance questions using a curated knowledge base.
- Separates major citizen flows such as eligibility, referrals, admissions, complaints, payment disputes, and medicine coverage checks.
- Returns one of a small set of controlled actions:
  - `direct_answer`
  - `clarify`
  - `partial_answer_with_clarify`
  - `partial_answer_with_next_step`
  - `escalate_safety`
  - `escalate_true_gap`
- Maintains lightweight conversation state so follow-up questions can collect one missing field at a time.
- Handles complaint flows with separate live paths for:
  - ethics / professional-conduct complaints
  - hospital service / administrative complaints
  - hotline / contact / where-to-reach help
  - payment disputes

## What it does not do

- It does not provide medical diagnosis or treatment advice.
- It does not make final entitlement decisions for a specific person.
- It does not replace a doctor, emergency service, or case handler.
- It does not promise provider-specific outcomes.
- It does not behave like a general-purpose conversational model that improvises policy.

## Why it is safer than a general chatbot

- It routes questions into bounded policy domains instead of free-answering everything.
- It can stop and clarify when the user’s wording is underspecified.
- It escalates safety-sensitive medical wording instead of pretending to advise.
- It preserves separate ownership across sensitive complaint types instead of collapsing them into one generic answer.
- Its live answers are constrained by explicit KB content and action logic.

## How it reduces hotline load

The product reduces repeat hotline traffic by handling common first-line questions such as:

- who may qualify for free or privileged care
- when a referral may be needed
- hospitalization vs surgery admission questions
- where a complaint belongs
- whether a complaint is ethics-related, service-related, or contact-related
- next-step guidance when a user is missing one key piece of information

This is especially useful for channels that receive high volumes of repetitive policy and navigation questions before a human operator is needed.

## Deployment options

- Website chat widget
- Public or partner API integration
- Social / messaging integration where a single text message is sent to the backend and the response action is rendered in the channel

## Live boundaries to present honestly

- The product is strong at structured guidance and clarification.
- It is not a full case-management platform.
- It should be sold as a controlled healthcare guidance layer, not as autonomous medical or legal decision-making.
