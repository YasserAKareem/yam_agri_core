## Summary
<!-- One-sentence description of what this PR does and why. -->


## Type of change
<!-- Check all that apply. -->
- [ ] 🐛 Bug fix (non-breaking change that fixes an issue)
- [ ] ✨ New feature (non-breaking change that adds functionality)
- [ ] 💥 Breaking change (fix or feature that changes existing behaviour)
- [ ] 🏗️ Infrastructure / DevOps
- [ ] 📝 Documentation only
- [ ] 🔒 Security fix

## Related issues
<!-- Link issues with "Closes #N" or "Refs #N". -->
Closes #

---

## Checklist — author

### General
- [ ] My branch is up-to-date with `main` (no merge conflicts)
- [ ] The PR title follows the format: `<type>(<scope>): <short description>` (e.g. `feat(lot): add split workflow`)
- [ ] I have added or updated documentation where necessary

### Security & secrets
- [ ] No `.env` files with real passwords/tokens are committed
- [ ] No API keys, credentials, or secrets are hard-coded in any file
- [ ] Environment variables use `.env.example` as a template only

### Infrastructure changes (if applicable)
- [ ] Docker Compose files are valid (`docker compose config` passes)
- [ ] Environment variable changes are reflected in `.env.example`
- [ ] `run.sh` commands (`up`, `down`, `logs`, `shell`, `init`, `reset`) still work

### Production changes (if applicable)
- [ ] Change has been tested in **dev** and **staging** first
- [ ] A rollback plan exists and is documented in this PR
- [ ] QA Manager approval has been obtained (high-risk changes only)

---

## Testing done
<!-- Describe what you tested and how. List the acceptance scenarios from the playbook that apply. -->


## Screenshots / evidence
<!-- For UI or observable behaviour changes, add screenshots or log snippets. -->
