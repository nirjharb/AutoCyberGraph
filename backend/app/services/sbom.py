"""
SBOM parsing — one interface, two formats.

- CycloneDX JSON 1.4/1.5: robust (components, versions, purls, hashes, licenses)
- SPDX JSON 2.x: document + package level

Both normalize into `SbomDocument` / `SbomEntry`. Format auto-detection from
content when not explicitly provided. See DECISIONS.md ADR-008.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field


class SbomParseError(ValueError):
    pass


@dataclass
class SbomEntry:
    name: str
    version: str = ""
    purl: str = ""
    license: str = ""
    hash: str = ""
    component_type: str = ""


@dataclass
class SbomDocument:
    format: str  # CycloneDX | SPDX
    version: str = ""
    entries: list[SbomEntry] = field(default_factory=list)


MAX_COMPONENTS = 5000
MAX_BYTES = 10 * 1024 * 1024


def detect_format(content: dict) -> str:
    if "bomFormat" in content and str(content.get("bomFormat", "")).lower() == "cyclonedx":
        return "CycloneDX"
    if "spdxVersion" in content or content.get("SPDXID", "").startswith("SPDXRef-Document"):
        return "SPDX"
    raise SbomParseError("Unrecognized SBOM format: expected CycloneDX or SPDX JSON")


def parse_sbom(text: str, fmt: str = "auto") -> SbomDocument:
    if len(text.encode("utf-8")) > MAX_BYTES:
        raise SbomParseError("SBOM exceeds maximum size")
    try:
        content = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SbomParseError(f"Invalid JSON: {exc}") from exc
    if not isinstance(content, dict):
        raise SbomParseError("SBOM root must be a JSON object")

    detected = detect_format(content)
    if fmt not in ("auto", "", detected):
        raise SbomParseError(f"Declared format {fmt} does not match content ({detected})")

    if detected == "CycloneDX":
        return _parse_cyclonedx(content)
    return _parse_spdx(content)


def _hash_of(comp: dict) -> str:
    hashes = comp.get("hashes") or []
    if hashes and isinstance(hashes, list):
        h = hashes[0]
        return f"{h.get('alg', '')}:{h.get('content', '')}"
    return ""


def _parse_cyclonedx(content: dict) -> SbomDocument:
    doc = SbomDocument(format="CycloneDX", version=str(content.get("specVersion", "")))
    components = content.get("components") or []
    if not isinstance(components, list):
        raise SbomParseError("CycloneDX 'components' must be a list")
    for comp in components[:MAX_COMPONENTS]:
        if not isinstance(comp, dict) or not comp.get("name"):
            continue
        doc.entries.append(SbomEntry(
            name=str(comp.get("name"))[:300],
            version=str(comp.get("version", ""))[:120],
            purl=str(comp.get("purl", ""))[:500],
            license=_license_of(comp),
            hash=_hash_of(comp)[:255],
            component_type=str(comp.get("type", ""))[:80],
        ))
    return doc


def _license_of(comp: dict) -> str:
    licenses = comp.get("licenses") or []
    if isinstance(licenses, list) and licenses:
        first = licenses[0]
        if isinstance(first, dict):
            lic = first.get("license") or {}
            if isinstance(lic, dict):
                return str(lic.get("id") or lic.get("name") or "")[:120]
            return str(first.get("expression", ""))[:120]
    return ""


def _parse_spdx(content: dict) -> SbomDocument:
    doc = SbomDocument(format="SPDX", version=str(content.get("spdxVersion", "")))
    packages = content.get("packages") or []
    if not isinstance(packages, list):
        raise SbomParseError("SPDX 'packages' must be a list")
    for pkg in packages[:MAX_COMPONENTS]:
        if not isinstance(pkg, dict) or not pkg.get("name"):
            continue
        checksums = pkg.get("checksums") or []
        hash_value = ""
        if checksums and isinstance(checksums, list):
            c = checksums[0]
            hash_value = f"{c.get('algorithm', '')}:{c.get('checksumValue', '')}"[:255]
        license_value = str(pkg.get("licenseConcluded") or pkg.get("licenseDeclared") or "")[:120]
        version = str(pkg.get("versionInfo", ""))[:120]
        purl = ""
        for ref in pkg.get("externalRefs") or []:
            if isinstance(ref, dict) and ref.get("referenceType") == "purl":
                purl = str(ref.get("referenceLocator", ""))[:500]
                break
        doc.entries.append(SbomEntry(
            name=str(pkg.get("name"))[:300],
            version=version,
            purl=purl,
            license=license_value,
            hash=hash_value,
            component_type="package",
        ))
    return doc
