# Judge Answers

**What is AegisScan?** A local-first platform that plans and runs authorized application security assessments across discovery and multiple scanner engines.

**What problem does it solve?** It gives an operator one controlled workflow for target authorization, attack-surface discovery, scanner execution, availability tracking, and raw evidence collection.

**Why multiple scanners?** DAST, template scanning, SAST, dependency analysis, and custom checks observe different evidence surfaces.

**Why local testing?** The demo is reproducible and safe, and it avoids scanning public systems or handling real credentials.

**Is this just a ZAP dashboard?** No. ZAP is one optional adapter in a registry alongside Nuclei, Semgrep, Dependency-Check, and native checks.

**What is implemented now?** Target and assessment management, discovery, attack-surface inventory, scan planning, real local adapter execution, unavailable-tool handling, timeouts, and raw result storage.

**What is planned next?** Parsing raw outputs into normalized findings, correlation, verification, risk prioritization, remediation intelligence, and report generation.

**Can it guarantee every vulnerability?** No. Scanner coverage is limited by tool behavior, scope, configuration, and environment.

**Are you attacking World Monitor?** The live demo uses only the isolated localhost lab. Any World Monitor assessment requires an explicitly authorized controlled copy.

**Does it require paid APIs?** No. The core workflow uses local tools and local HTTP APIs.

**How are false positives handled?** The current phase preserves raw evidence; verification and correlation are future layers, so findings are not presented as verified today.
