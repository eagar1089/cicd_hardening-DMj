# CI/CD Hardening — Digital Memory Jar

[![CI Pipeline](https://github.com/eagar1089/memoryjar-cicd-hardening/actions/workflows/ci.yml/badge.svg)]
[![Security Scan](https://github.com/eagar1089/memoryjar-cicd-hardening/actions/workflows/ci.yml/badge.svg)]

A production-grade CI/CD pipeline built on top of the [Digital Memory Jar](https://github.com/eagar1089/Digital-MemoryJar) FastAPI backend. 
Implements automated security scanning, dependency auditing, Docker image scanning, and semantic versioning — all on GitHub

CI: ✅ Lint → Test → Docker Build → Trivy Scan → Release
Security: Bandit SAST + Safety dependency audit + Trivy CVE scan
Branch protection: all merges to main require passing CI + PR review
Versioning: automated semantic tags via GitHub Actions
