# Phase 4 — Integration & Polish Spec
**Wall time:** 25 min | **Agent:** Single (sequential, all phases done) | **Status:** TODO

## Tasks
1. Run full smoke test: `bash scripts/quick-test.sh`
2. Fix any import errors, CORS failures, missing weights
3. Verify all 3 scenario buttons work end-to-end
4. Verify PQC tamper detection demo (modify report → verify → red ✗)
5. `pip freeze > requirements.lock`
6. Final `docker-compose.yml` verified: `docker-compose up` starts both services

## Exit gate
- [ ] `bash scripts/quick-test.sh` exits 0 (all smoke tests pass)
- [ ] All 3 scenario buttons trigger visible dashboard updates
- [ ] PQC tamper demo shows red ✗ badge
- [ ] `docker-compose up` starts successfully
- [ ] No hardcoded API keys in source (check with `grep -r "OPENWEATHERMAP_API_KEY" --include="*.py"`)
