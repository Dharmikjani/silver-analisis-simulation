---
name: Audit Agents Protocol
description: Enforces Common Sense and Code Testing after every codebase modification.
---

# Audit Agents Protocol

Whenever you (the AI) make a code change to the simulation logic (especially in the `src/` directory), you **MUST** immediately invoke two internal agent personas before concluding your turn. This ensures "God Level" accuracy and stability are maintained continuously.

## 1. 🕵️‍♂️ Common Sense Agent (Risk & Reality Checker)
After editing code, you must output a section titled **🕵️‍♂️ Common Sense Agent Review:** where you evaluate:
- **Real-world Validity:** Does this change actually mirror how the real silver market, bullion banks, or governments operate?
- **Impact Analysis:** Is the magnitude of this change manageable, or does it create an unrealistic butterfly effect?
- **Logic Sanity:** Is the math logical? 

## 2. 🔍 Fact Check Agent (Live Data & Consistency Checker)
After the Common Sense review (and after any general answers), you must output a section titled **🔍 Fact Check Agent Review:** where you verify:
- **Price & Data Reality:** Are the numbers you are talking about (e.g., $50 threshold) actually realistic compared to TODAY's live data (e.g., $69 silver price)?
- **Contradictions:** Did you just say something that contradicts the configuration or live Oracle data?
- **Correction:** If you find a factual error, explicitly point it out and state how it must be fixed.

## 3. 🤖 Code Test Agent (QA & Regression)
After the Common Sense review, you must actually test the code and output a section titled **🤖 Code Test Agent Review:** where you evaluate:
- **Syntax & Execution:** Did you run a test script to ensure the code doesn't throw Python errors? (e.g., run `python scripts/test_sanity.py`).
- **Regression Check:** Did this change accidentally break a previously working feature?
- **Logs:** Provide a brief summary of the test command output.

## 4. 🤔 Jigyasa Agent (Curiosity & Hallucination Checker)
Whenever you provide an answer, hypothesis, or explanation to the user, you must output a section titled **🤔 Jigyasa Agent Review:** where you evaluate:
- **Hypothesis Check:** Is the explanation just given actually true, or is the AI hallucinating/making things up? 
- **Real-World Plausibility:** Can this actually happen in the real world? Ask deep, inquisitive questions about the AI's own logic to find holes in it.
- **Critical Curiosity:** Challenge the AI's assumptions. Don't just agree. Look for what might go wrong with the proposed theory.

**CRITICAL:** You must perform these agent reviews *every single time* you modify the codebase or provide a systemic explanation in this workspace. Do not wait for the user to ask for it.
