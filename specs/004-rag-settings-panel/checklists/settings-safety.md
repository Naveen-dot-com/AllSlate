# Settings Safety & Isolation Checklist: RAG Settings Panel

**Purpose**: Validate that requirements for disabling web search completely, scoping settings
correctly per conversation/user/project, and rejecting invalid setting values are complete,
unambiguous, and testable — before/alongside implementation planning.
**Created**: 2026-08-17
**Feature**: [spec.md](../spec.md) | [plan.md](../plan.md)

**Focus Areas**: Web search hard-disable guarantee, settings scoping/isolation, invalid-value
rejection (no silent clamping).
**Depth**: Standard (release-gate level; ties directly to constitution Principles I and VII).
**Audience**: Reviewer (spec/plan review prior to task breakdown).

## Web Search Hard-Disable Guarantee

- [ ] CHK001 - Is it explicitly required that no outbound web search request is made at all
      when `web_search_enabled` is false, as distinct from "the result is simply not shown to
      the user"? [Clarity, Spec §FR-006]
- [ ] CHK002 - Are requirements defined for verifying the absence of outbound calls (e.g., an
      auditable/observable signal that no web search attempt occurred), or is this left
      unverifiable by design? [Gap, Spec §FR-006, Plan Principle III]
- [ ] CHK003 - Is the default state of `web_search_enabled` for a brand-new conversation
      explicitly specified as "off," so that no web calls occur before a user ever opens the
      settings panel? [Completeness, Spec §Assumptions]
- [ ] CHK004 - Are requirements defined for what happens if a setting change disabling web
      search arrives while a web-search-dependent generation is already in flight (does the
      in-flight call still complete, and is that explicitly acceptable per FR-013)? [Consistency,
      Spec §FR-013, Edge Cases]
- [ ] CHK005 - Is there a requirement that disabling web search takes effect for literally the
      very next question with zero possibility of a stale "enabled" state being read (e.g., a
      caching layer that could serve an outdated settings value)? [Ambiguity, Spec §FR-012]
- [ ] CHK006 - Are requirements defined for confirming that the web-search routing decision is
      made strictly from the persisted setting, and not from any other implicit signal (e.g.,
      conversation content, question wording) that could enable web search unexpectedly?
      [Gap, Plan §Research Decision 3]
- [ ] CHK007 - Is it specified whether toggling web search off must also prevent any partially
      retrieved web results from a prior in-flight call from being used once web search is
      turned off mid-generation? [Edge Case, Gap]

## Settings Scoping & Isolation

- [ ] CHK008 - Are requirements defined that a settings read or write for one conversation
      thread can never affect or be visible in a different thread, including threads within
      the same project? [Completeness, Spec §Assumptions - per-conversation scope]
- [ ] CHK009 - Is it explicitly required that a settings request is rejected (not merely
      defaulted or partially served) when the authenticated user does not own the project
      containing the target conversation? [Clarity, Spec §FR-017]
- [ ] CHK010 - Are requirements defined for the exact error behavior (e.g., generic not-found
      response) when a user attempts to read or write settings for a conversation they do not
      own, consistent with the existing no-existence-disclosure pattern used elsewhere in the
      product? [Consistency, Spec §FR-017]
- [ ] CHK011 - Is there a requirement verifying that two different users' conversations in
      different projects can have completely independent settings values with zero leakage in
      either direction, including under concurrent updates? [Coverage, Spec §FR-017]
- [ ] CHK012 - Are requirements defined for what happens to a conversation's settings when the
      conversation itself is deleted or made inaccessible (e.g., does the settings row's
      lifecycle explicitly follow the conversation's)? [Gap]
- [ ] CHK013 - Is it specified whether settings for a given conversation are visible to any
      other actor (e.g., another project the same document might theoretically be shared
      with, if any sharing existed) — explicitly ruling out any such exposure? [Ambiguity,
      Spec §Assumptions - single-owner model]
- [ ] CHK014 - Are requirements defined for ensuring that the settings snapshot recorded
      against a specific answer message cannot be altered retroactively by a later settings
      change to the same conversation? [Consistency, Spec §FR-014, Plan Data Model]

## Invalid Setting Value Rejection

- [ ] CHK015 - Is it explicitly required that an out-of-range value (e.g., a numeric
      creativity/temperature value outside allowed bounds) is rejected with an error, rather
      than silently clamped to the nearest valid value? [Clarity, Gap — not explicit in current
      FRs]
- [ ] CHK016 - Are the valid value sets/ranges for every adjustable setting (creativity level,
      number of source chunks, document type selection) explicitly and completely enumerated,
      so "invalid" is unambiguous for each field? [Completeness, Spec §FR-007, FR-009, FR-010]
- [ ] CHK017 - Is it specified whether submitting an unrecognized/unsupported value for a
      setting (e.g., a creativity level string that isn't one of the defined plain-language
      options) results in outright rejection, as opposed to silently falling back to a
      default? [Ambiguity, Gap]
- [ ] CHK018 - Are requirements defined for the user-facing behavior when a setting change is
      rejected (e.g., must the UI clearly communicate why the change did not take effect,
      consistent with the plain-language/non-technical-user requirement)? [Gap, Spec §FR-003]
- [ ] CHK019 - Is it required that a rejected setting change leaves the previously persisted,
      valid value fully intact and in effect, rather than partially applying the invalid
      change? [Completeness, Gap]
- [ ] CHK020 - Is the "at least one document type must remain selected" rule (FR-011)
      specified as a hard rejection of the write, consistently with how other invalid values
      are expected to be handled, rather than as a different (e.g., silently-corrected)
      behavior? [Consistency, Spec §FR-011]
- [ ] CHK021 - Are requirements defined for validating the number-of-source-chunks setting
      against a sane bound (e.g., a minimum of at least one, and a defined maximum), with
      out-of-bounds values explicitly rejected? [Gap, Spec §FR-009]

## Cross-Cutting Consistency & Traceability

- [ ] CHK022 - Do the web-search-disable guarantee, the scoping/isolation rules, and the
      invalid-value rejection rules apply consistently regardless of which specific setting is
      being changed, or do any requirements implicitly treat one setting differently without
      explicit justification? [Consistency]
- [ ] CHK023 - Is a requirement/acceptance-criteria ID scheme consistently applied across all
      three focus areas so each checklist concern can be traced back to a specific FR, or
      flagged as a currently-unaddressed [Gap]? [Traceability]
