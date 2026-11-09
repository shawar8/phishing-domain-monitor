# Phishing Domain Monitor

A live system that scores newly certified domains for phishing risk every day.

- **Ingest:** new domains from Certificate Transparency logs (CertStream)
- **Model:** XGBoost on domain features (lookalike brands, entropy, TLD, certificate issuer), tracked in MLflow
- **Labels:** attached later from URLhaus and OpenPhish, to measure real precision and recall
- **Monitoring:** daily drift (PSI), volume and null checks in DuckDB
- **Agent:** an LLM agent that investigates monitoring alerts and writes incident reports

Status: Week 1, ingestion in progress.# phishing-domain-monitor
