# Third-Party Notices — code-security-audit

This skill incorporates material from the project listed below.

---

## OWASP Application Security Verification Standard (ASVS) 5.0.0

- **Upstream project:** [`OWASP/ASVS`](https://github.com/OWASP/ASVS)
- **Source material:** [`5.0/docs_en/OWASP_Application_Security_Verification_Standard_5.0.0_en.json`](https://github.com/OWASP/ASVS/blob/v5.0.0_release/5.0/docs_en/OWASP_Application_Security_Verification_Standard_5.0.0_en.json) at tag [`v5.0.0_release`](https://github.com/OWASP/ASVS/tree/v5.0.0_release)
- **Creator:** The OWASP Foundation (ASVS project leads and contributors are listed in the standard's [Frontispiece](https://github.com/OWASP/ASVS/blob/v5.0.0_release/5.0/en/0x01-Frontispiece.md))
- **Copyright:** Copyright © 2008-2025 The OWASP Foundation
- **License:** [Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)](https://creativecommons.org/licenses/by-sa/4.0/)
- **Adapted in:** `references/security_domains.md`

### Modifications

- Requirement descriptions are copied from the JSON with the leading "Verify that" or "Verify" removed.
- Each requirement is reformatted as a YAML list item with its ID and level (`[L1]`, `[L2]`, `[L3]`).
- The 31 documentation requirements (sections V2.1, V3.1, V5.1, V6.1, V7.1, V8.1, V11.1, V13.1, V14.1, V15.1, V16.1) are replaced by comments that give only the section name and requirement count.
- Per-domain summaries (requirement counts and section names) and the cross-source mapping tables are added by this skill. The mappings to API Security Top 10 2023, the CheatSheet Series, and WSTG v4.2 are not part of ASVS.

The ASVS-derived text in `references/security_domains.md` is distributed under CC BY-SA 4.0.
