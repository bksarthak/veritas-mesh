# Contributing to Veritas-Mesh

Veritas-Mesh is built in the open and welcomes contributions of any size —
typo fixes, new search backends, better forensics, more presets, anything.

## The fastest way to contribute

Open the README's [Known Gaps & Limitations](README.md#known-gaps--limitations)
table, **pick a numbered row**, and open a PR. The numbers are roughly ordered
by impact. The first three (forensics ensembling, URL fetching, better search
backends) are the highest-leverage. The last two (prompt-injection hardening,
test coverage) are the highest-trust.

If you're not sure whether your idea fits, open an issue first and we'll
talk it through.

## Ground rules

- **Keep it local-first.** Any feature that requires a cloud account must be
  optional and must degrade gracefully when the account isn't configured.
- **Don't break the security boundary.** Anything that touches
  `_sanitize_untrusted` in `veritas/judge.py`, the prompt templates, or the
  Docker hardening in `docker-compose.yml` needs a careful review and a test.
- **Be honest about limitations.** If your PR adds a feature with known
  failure modes, document them in the Known Gaps table. We'd rather ship a
  rough edge with a label than a rough edge in disguise.

## Dev setup

```bash
git clone https://github.com/<your-fork>/veritas-mesh.git
cd veritas-mesh
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python demo.py --preset benign   # smoke test
```

## PR checklist

- [ ] Code runs end-to-end via `python demo.py`
- [ ] No new secrets, API keys, or absolute paths committed
- [ ] If you added a search backend, document it in the README
- [ ] If you added a tool/feature, add or update an entry in Known Gaps
- [ ] If you touched `judge.py` or `forensics.py`, run at least one preset
      in both modes and paste the output in the PR description
