# QAegisPralaya Roadmap

| Phase | Component | Status | Gate |
|-------|-----------|--------|------|
| 0 | Scaffold + CCPM setup | ✅ Complete | git status clean |
| 1-A | Data pipeline + synthetic gen | ✅ Complete | generate_scenario.py --all exits 0 |
| 1-B | QML engine + VQC training | ✅ Complete | VQC accuracy 82.5% > 65% |
| 1-C | PQC layer + key registry | ✅ Complete | verify_pqc.py exits 0 |
| 2 | FastAPI backend integration | ✅ Complete | all 7 API routes respond |
| 3-A | React EOC dashboard | ✅ Complete | dashboard loads, WS updates |
| 3-B | Demo scenarios + README | ✅ Complete | 3 scenarios run unattended |
| 4 | Integration + polish | 🚧 Active | quick-test.sh green |

## Post-hackathon (stretch)
- Replace synthetic data with real NDRF / state SCADA integration
- Hierarchical PKI for key distribution (ADR-0006 extension)
- IBM Quantum / AWS Braket hardware backend swap-in
- Mobile app for field responders
