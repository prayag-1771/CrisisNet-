"""Synthetic seed data for CrisisNet demo.

All data is obviously synthetic and fictional — never sourced from real
crisis-line transcripts, real forum posts, or any real person's crisis.

Each message has a known expected severity for testing purposes.
"""

SYNTHETIC_MESSAGES = [
    # ── LOW Severity ──
    {
        "text": "I've been feeling a bit stressed about my upcoming exams. Any study tips?",
        "expected_severity": "LOW",
        "description": "General academic stress, no risk indicators",
    },
    {
        "text": "My name is Alex Thompson and I've been having trouble sleeping lately. My email is alex.t@fakemail.com. Just wondering if there are any relaxation techniques.",
        "expected_severity": "LOW",
        "description": "Mild sleep issues with PII (name + email) for testing PII scrubber",
    },
    {
        "text": "I had a disagreement with my roommate about cleaning duties. It's frustrating but we'll work it out.",
        "expected_severity": "LOW",
        "description": "Minor interpersonal conflict, resilient tone",
    },
    {
        "text": "I'm looking for some self-help books on managing anxiety. Can you recommend any?",
        "expected_severity": "LOW",
        "description": "Proactive help-seeking, no distress indicators",
    },

    # ── MEDIUM Severity ──
    {
        "text": "I've been feeling really overwhelmed at work for weeks now. I can't seem to focus on anything and I'm constantly exhausted. My phone is 555-0123 if anyone can talk.",
        "expected_severity": "MEDIUM",
        "description": "Moderate distress, burnout symptoms, PII (phone number)",
    },
    {
        "text": "My partner and I just broke up after 3 years. I feel empty inside and don't know how to cope. I live at 42 Fictional Lane, Imaginary City.",
        "expected_severity": "MEDIUM",
        "description": "Emotional distress from relationship loss, PII (address)",
    },
    {
        "text": "I've been crying every day for the past two weeks. I don't enjoy anything anymore. Everything feels pointless.",
        "expected_severity": "MEDIUM",
        "description": "Signs of depression, anhedonia, but no self-harm ideation",
    },
    {
        "text": "I lost my job last month and I'm running out of savings. The anxiety is making it hard to even apply for new positions.",
        "expected_severity": "MEDIUM",
        "description": "Financial stress compounding anxiety",
    },

    # ── HIGH Severity ──
    {
        "text": "I keep thinking about whether anyone would even notice if I disappeared. I feel like such a burden to everyone around me.",
        "expected_severity": "HIGH",
        "description": "Passive suicidal ideation, feelings of burdensomeness",
    },
    {
        "text": "My name is Jordan Rivera and I've been cutting myself to cope with the pain. I know it's not healthy but I can't stop. Please help me. My number is 555-9876.",
        "expected_severity": "HIGH",
        "description": "Active self-harm behavior, PII (name + phone), help-seeking",
    },
    {
        "text": "I can't take this anymore. The voices in my head are getting louder and they're telling me to do terrible things.",
        "expected_severity": "HIGH",
        "description": "Possible psychotic symptoms, command hallucinations",
    },
    {
        "text": "I haven't eaten in three days. I've been drinking heavily and I don't care what happens to me anymore.",
        "expected_severity": "HIGH",
        "description": "Self-neglect, substance misuse, reckless indifference to safety",
    },

    # ── CRITICAL Severity ──
    {
        "text": "I have a plan to end my life tonight. I've written letters to my family and I've gathered everything I need. My name is Casey Morgan, 123 Test Street.",
        "expected_severity": "CRITICAL",
        "description": "Immediate suicide plan with preparation, PII (name + address)",
    },
    {
        "text": "I'm standing on the bridge right now. Please send someone. I'm at the corner of Fictional Ave and Imaginary Blvd. My phone is 555-0000.",
        "expected_severity": "CRITICAL",
        "description": "Active emergency in progress, PII (phone + location)",
    },
    {
        "text": "I just took a whole bottle of pills. I'm starting to feel dizzy. I don't know if I want to die but I can't undo it now.",
        "expected_severity": "CRITICAL",
        "description": "Active overdose in progress, ambivalent but immediate medical emergency",
    },
    {
        "text": "My roommate just told me they're going to hurt themselves. They have a weapon and they locked themselves in the bathroom. Please help immediately.",
        "expected_severity": "CRITICAL",
        "description": "Third-party report of imminent danger, weapon involved",
    },
]
