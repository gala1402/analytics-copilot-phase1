# Analytics Copilot Phase 1 — Interactive Guardrailed Assistant

This version upgrades the app into an **interactive analytics assistant** with:

- **Gatekeeper 2.0**: scope + ambiguity + refusal boundaries
- **Multi-intent Task Planner**: decomposes a single message into atomic tasks
- **Capability Registry**: explicit supported intents
- **Clarifier**: asks only the minimal missing questions
- **Executors**: per-intent response generation (SQL, pandas, product analytics, strategy)
- **Composer**: merges results and transparently reports unsupported parts

## Supported intents
- BUSINESS_STRATEGY
- PRODUCT_ANALYTICS
- SQL_INVESTIGATION
- PANDAS_TRANSFORM

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
