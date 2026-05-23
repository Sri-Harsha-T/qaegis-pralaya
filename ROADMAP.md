# QAegisPralaya Roadmap

| Phase | Component | Status | Gate |
|-------|-----------|--------|------|
| 0 | Scaffold + CCPM setup | ✅ Complete | git status clean |
| 1-A | Data pipeline + synthetic gen | 🚧 Active | generate_scenario.py --all exits 0 |
| 1-B | QML engine + VQC training | 🚧 Active | VQC accuracy > 65% |
| 1-C | PQC layer + key registry | 🚧 Active | verify_pqc.py exits 0 |
| 2 | FastAPI backend integration | ⏳ Queued | all 7 API routes respond |
| 3-A | React EOC dashboard | ⏳ Queued | dashboard loads, WS updates |
| 3-B | Demo scenarios + README | ⏳ Queued | 3 scenarios run unattended |
| 4 | Integration + polish | ⏳ Queued | quick-test.sh green |

## Post-hackathon (stretch)
- Replace synthetic data with real NDRF / state SCADA integration
- Hierarchical PKI for key distribution (ADR-0006 extension)
- IBM Quantum / AWS Braket hardware backend swap-in
- Mobile app for field responders
