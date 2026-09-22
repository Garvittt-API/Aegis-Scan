# AegisScan: 5-Minute SIH Demo

## 0:00-0:35 - PROBLEM

Application security checks are often split across tools, scopes, and output formats. That makes it difficult to prove what was tested, whether a tool was available, and where the evidence came from.

## 0:35-1:15 - AEGISSCAN SOLUTION

AegisScan is a local-first, authorization-gated workflow for registering a target, discovering its attack surface, planning scanner jobs, executing real local tools, and preserving raw evidence in one place.

## 1:15-2:00 - HOW IT WORKS

The current pipeline is Target, Discover, Attack Surface, Scan Plan, Scanner Registry, Execute, and Raw Result Storage. Each optional scanner reports its real state: completed, failed, unavailable, or cancelled.

## 2:00-3:30 - LIVE DEMO

Use the isolated `AegisScan Security Demo Lab` on `127.0.0.1:8010`. Show the authorized target, the discovered local pages and API routes, the queued custom-check job, the completed execution, and the raw JSON/log evidence. External scanners are enabled only when actually installed.

## 3:30-4:20 - INNOVATION / INTELLIGENCE LAYER

The raw result boundary is deliberately explicit. The next intelligence layer will parse scanner-specific output into normalized findings, correlate duplicates, and attach evidence consistently. Those layers are planned, not claimed as implemented in this demo.

## 4:20-5:00 - IMPACT + FUTURE

The current MVP makes authorized local assessment reproducible and auditable without paid APIs or public-target scanning. The next phase adds normalization, correlation, verification, risk scoring, remediation intelligence, and report generation.