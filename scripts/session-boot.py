#!/usr/bin/env python3
"""
session-boot.py — Abraxas Session Boot Protocol

Performs a structured boot sequence at session startup:
  Phase 1: Genesis Load — verify genesis.md, count systems, report metadata
  Phase 2: Health Check — probe ArangoDB, MCP servers, filesystem state
  Phase 3: Constitution Drift Audit — hash constitutions, detect changes
  Phase 4: Mode Report — synthesize findings into status report

Usage:
  python3 scripts/session-boot.py                # default (quiet summary)
  python3 scripts/session-boot.py --verbose      # detailed output
  python3 scripts/session-boot.py --json         # machine-readable JSON
  python3 scripts/session-boot.py -v --json      # verbose JSON
  python3 scripts/session-boot.py --help         # show help

Exit codes: 0=healthy, 1=degraded (simulation mode), 2=critical failure
"""

import argparse
import hashlib
import json
import os
import platform
import shutil
import socket
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

class Paths:
    """Resolve all relevant paths relative to the project root."""
    def __init__(self, script_dir: Optional[str] = None):
        if script_dir is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.abspath(os.path.join(script_dir, ".."))
        self.constitution_dir = os.path.join(self.project_root, "constitution")
        self.genesis_path = os.path.join(self.constitution_dir, "genesis.md")
        self.index_path = os.path.join(self.constitution_dir, "constitution-index.md")
        self.manifest_path = os.path.join(self.constitution_dir, ".manifest.json")
        self.skills_dir = os.path.join(self.project_root, "skills")
        self.tests_dir = os.path.join(self.project_root, "tests")
        self.scripts_dir = os.path.join(self.project_root, "scripts")


# ---------------------------------------------------------------------------
# Phase 1: Genesis Load
# ---------------------------------------------------------------------------

class GenesisLoader:
    """Verify genesis.md, count constitution systems, extract metadata."""

    def __init__(self, paths: Paths):
        self.paths = paths
        self.results: Dict[str, Any] = {}

    def run(self) -> Dict[str, Any]:
        genesis_info = self._check_genesis()
        constitutions_info = self._scan_constitutions()
        self.results = {
            "genesis": genesis_info,
            "constitutions": constitutions_info,
        }
        self.results["version_comparison"] = self._compare_versions()
        return self.results

    def _check_genesis(self) -> Dict[str, Any]:
        """Verify genesis.md exists, is readable, and extract metadata."""
        result: Dict[str, Any] = {
            "path": self.paths.genesis_path,
            "exists": False,
            "readable": False,
            "size_bytes": 0,
            "size_human": "0 B",
            "version": None,
            "modified": None,
            "error": None,
        }

        path = Path(self.paths.genesis_path)
        if not path.exists():
            result["error"] = "genesis.md not found"
            return result

        result["exists"] = True

        if not os.access(path, os.R_OK):
            result["error"] = "genesis.md not readable"
            return result

        result["readable"] = True

        stat = path.stat()
        result["size_bytes"] = stat.st_size
        result["size_human"] = _human_size(stat.st_size)
        result["modified"] = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()

        # Extract version from first 10 lines (avoid loading entire file)
        version = self._extract_version(path)
        result["version"] = version

        return result

    def _extract_version(self, path: Path) -> Optional[str]:
        """Extract version from genesis.md metadata header without loading full file."""
        with open(path, "r", encoding="utf-8") as f:
            for _ in range(10):
                line = f.readline()
                if not line:
                    break
                if "Version:" in line:
                    # e.g. "> Version: 4.4.1"
                    parts = line.split("Version:", 1)
                    if len(parts) == 2:
                        return parts[1].strip()
        return None

    def _scan_constitutions(self) -> Dict[str, Any]:
        """Scan constitution-*.md files and count them."""
        result: Dict[str, Any] = {
            "directory": self.paths.constitution_dir,
            "total_files": 0,
            "total_commands": 0,
            "systems": [],
            "error": None,
        }

        const_dir = Path(self.paths.constitution_dir)
        if not const_dir.exists():
            result["error"] = "constitution directory not found"
            return result

        files = sorted([f for f in const_dir.glob("constitution-*.md")])

        result["total_files"] = len(files)

        for f in files:
            system_info = {
                "name": self._extract_system_name(f),
                "filename": f.name,
                "commands": self._count_commands(f),
            }
            result["systems"].append(system_info)
            result["total_commands"] += system_info["commands"]

        # Also count genesis.md and constitution-index.md
        result["has_genesis"] = self.paths.genesis_path and os.path.exists(self.paths.genesis_path)
        result["has_index"] = self.paths.index_path and os.path.exists(self.paths.index_path)

        return result

    def _extract_system_name(self, path: Path) -> str:
        """Extract the system name from the constitution file's first heading."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("# "):
                        return line[2:].strip()
                    if line.startswith("## "):
                        return line[3:].strip()
                    if len(line) > 0:
                        break
        except Exception:
            pass
        return path.stem.replace("constitution-", "").title()

    def _count_commands(self, path: Path) -> int:
        """Count the number of command definitions in a constitution file."""
        count = 0
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    # Count lines with `/command-name |` pattern
                    if line.strip().startswith("| `/") and "|" in line:
                        count += 1
        except Exception:
            pass
        return count

    def _compare_versions(self) -> Dict[str, Any]:
        """Compare genesis.md version against last recorded version in manifest."""
        result: Dict[str, Any] = {
            "current_version": self.results.get("genesis", {}).get("version"),
            "previous_version": None,
            "version_changed": False,
        }

        manifest_path = Path(self.paths.manifest_path)
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                result["previous_version"] = manifest.get("genesis_version")
                result["version_changed"] = (
                    result["current_version"] != result["previous_version"]
                )
            except (json.JSONDecodeError, OSError):
                result["previous_version"] = "<unreadable>"

        return result


# ---------------------------------------------------------------------------
# Phase 2: Health Check
# ---------------------------------------------------------------------------

class HealthChecker:
    """Check connectivity to ArangoDB, MCP servers, and filesystem state."""

    def __init__(self, paths: Paths):
        self.paths = paths

    def run(self) -> Dict[str, Any]:
        return {
            "arangodb": self._check_arangodb(),
            "mcp_health_url": self._check_mcp_health_endpoint(),
            "filesystem": self._check_filesystem(),
            "system_resources": self._check_system_resources(),
        }

    def _check_arangodb(self) -> Dict[str, Any]:
        """Check ArangoDB connectivity via environment vars and optional socket probe."""
        result: Dict[str, Any] = {
            "configured": False,
            "reachable": False,
            "url": os.environ.get("ARANGO_URL", os.environ.get("ARANGO_HOST")),
            "database": os.environ.get("ARANGO_DB", os.environ.get("ARANGO_DATABASE")),
            "has_credentials": bool(os.environ.get("ARANGO_USER") and os.environ.get("ARANGO_ROOT_PASSWORD")),
            "error": None,
        }

        if not result["url"]:
            result["error"] = "No ARANGO_URL or ARANGO_HOST set"
            return result

        result["configured"] = True

        # Try a TCP socket probe
        try:
            url = result["url"]
            host = url
            port = 8529  # default ArangoDB port

            if "://" in url:
                host = url.split("://")[1]
            if ":" in host:
                host_parts = host.split(":")
                host = host_parts[0]
                try:
                    port = int(host_parts[1])
                except ValueError:
                    pass
            host = host.rstrip("/")

            sock = socket.create_connection((host, port), timeout=2.0)
            sock.close()
            result["reachable"] = True
        except Exception as e:
            result["reachable"] = False
            result["error"] = f"cannot reach {result['url']}: {e}"

        return result

    def _check_mcp_health_endpoint(self) -> Dict[str, Any]:
        """Check MCP health URL if available."""
        result: Dict[str, Any] = {
            "configured": False,
            "reachable": False,
            "url": os.environ.get("ABRAXAS_HEALTH_URL", "http://localhost:9901/health"),
            "status": None,
            "error": None,
        }

        # Try a simple HTTP connection (no dependency on requests library)
        try:
            url = result["url"]
            host = "localhost"
            port = 9901

            if "://" in url:
                host = url.split("://")[1]
            host = host.split("/")[0]
            if ":" in host:
                host, port_str = host.split(":")
                port = int(port_str)

            sock = socket.create_connection((host, port), timeout=2.0)
            sock.close()
            result["reachable"] = True
            result["configured"] = True
        except Exception as e:
            result["reachable"] = False
            result["error"] = str(e)

        return result

    def _check_filesystem(self) -> Dict[str, Any]:
        """Check key directories exist and are writable."""
        result: Dict[str, Any] = {
            "constitution_dir": {
                "path": self.paths.constitution_dir,
                "exists": os.path.isdir(self.paths.constitution_dir),
                "readable": os.access(self.paths.constitution_dir, os.R_OK) if os.path.isdir(self.paths.constitution_dir) else False,
            },
            "skills_dir": {
                "path": self.paths.skills_dir,
                "exists": os.path.isdir(self.paths.skills_dir),
            },
            "tests_dir": {
                "path": self.paths.tests_dir,
                "exists": os.path.isdir(self.paths.tests_dir),
            },
            "scripts_dir": {
                "path": self.paths.scripts_dir,
                "exists": os.path.isdir(self.paths.scripts_dir),
            },
            "project_root": {
                "path": self.paths.project_root,
                "exists": os.path.isdir(self.paths.project_root),
                "writable": os.access(self.paths.project_root, os.W_OK) if os.path.isdir(self.paths.project_root) else False,
            },
        }
        return result

    def _check_system_resources(self) -> Dict[str, Any]:
        """Check basic system resources."""
        return {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "hostname": socket.gethostname(),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }


# ---------------------------------------------------------------------------
# Phase 3: Constitution Drift Audit
# ---------------------------------------------------------------------------

class DriftAuditor:
    """Hash each constitution file, compare against stored manifest, detect drift."""

    def __init__(self, paths: Paths):
        self.paths = paths

    def run(self) -> Dict[str, Any]:
        current_hashes = self._compute_hashes()
        stored_manifest = self._load_manifest()
        drift = self._detect_drift(current_hashes, stored_manifest)

        # Store/update the manifest
        manifest = {
            "genesis_version": self._extract_genesis_version(),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generated_by": "session-boot.py",
            "files": current_hashes,
        }
        self._save_manifest(manifest)

        return {
            "manifest_stored": self.paths.manifest_path,
            "total_files_hashed": len(current_hashes),
            "is_first_run": len(stored_manifest.get("files", {})) == 0,
            "drift": drift,
        }

    def _compute_hashes(self) -> Dict[str, Dict[str, str]]:
        """Compute SHA-256 hashes for all constitution files and genesis.md."""
        hashes: Dict[str, Dict[str, str]] = {}
        const_dir = Path(self.paths.constitution_dir)

        files_to_hash = list(const_dir.glob("constitution-*.md"))
        if const_dir.joinpath("genesis.md").exists():
            files_to_hash.append(const_dir.joinpath("genesis.md"))
        if const_dir.joinpath("constitution-index.md").exists():
            files_to_hash.append(const_dir.joinpath("constitution-index.md"))

        for f in sorted(files_to_hash):
            try:
                file_hash = self._sha256_file(f)
                mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc).isoformat()
                hashes[f.name] = {"sha256": file_hash, "modified": mtime}
            except Exception as e:
                hashes[f.name] = {"sha256": "ERROR", "modified": str(e)}

        return hashes

    def _sha256_file(self, path: Path) -> str:
        """Compute SHA-256 hash of a file."""
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()

    def _load_manifest(self) -> Dict[str, Any]:
        """Load the stored manifest, if it exists."""
        manifest_path = Path(self.paths.manifest_path)
        if not manifest_path.exists():
            return {"files": {}}
        try:
            return json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"files": {}}

    def _save_manifest(self, manifest: Dict[str, Any]) -> None:
        """Save the manifest to .manifest.json."""
        manifest_path = Path(self.paths.manifest_path)
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def _extract_genesis_version(self) -> Optional[str]:
        """Extract genesis.md version."""
        genesis_path = Path(self.paths.genesis_path)
        if not genesis_path.exists():
            return None
        try:
            with open(genesis_path, "r", encoding="utf-8") as f:
                for _ in range(10):
                    line = f.readline()
                    if "Version:" in line:
                        return line.split("Version:", 1)[1].strip()
        except Exception:
            pass
        return None

    def _detect_drift(
        self, current: Dict[str, Dict[str, str]], stored: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare current hashes against stored manifest to detect drift."""
        stored_files = stored.get("files", {})
        is_first_run = len(stored_files) == 0

        drift: Dict[str, Any] = {
            "has_drift": False,
            "severity": "none",
            "added": [],
            "removed": [],
            "modified": [],
            "unchanged": [],
            "summary": "No changes detected.",
        }

        current_names = set(current.keys())
        stored_names = set(stored_files.keys())

        # New files added
        for name in sorted(current_names - stored_names):
            drift["added"].append(name)

        # Files removed
        for name in sorted(stored_names - current_names):
            drift["removed"].append(name)

        # Modified files
        for name in sorted(current_names & stored_names):
            stored_hash = stored_files[name].get("sha256")
            current_hash = current[name].get("sha256")
            if stored_hash and current_hash != stored_hash:
                drift["modified"].append(name)
            else:
                drift["unchanged"].append(name)

        if is_first_run:
            drift["has_drift"] = False
            drift["severity"] = "info"
            drift["summary"] = "First run — manifest initialized. No prior state to compare."
        elif drift["added"] or drift["removed"] or drift["modified"]:
            drift["has_drift"] = True
            parts = []
            if drift["added"]:
                parts.append(f"{len(drift['added'])} added")
            if drift["removed"]:
                parts.append(f"{len(drift['removed'])} removed")
            if drift["modified"]:
                parts.append(f"{len(drift['modified'])} modified")

            # Severity heuristics
            if drift["removed"]:
                drift["severity"] = "critical" if len(drift["removed"]) > 3 else "high"
            elif drift["modified"]:
                drift["severity"] = "medium" if len(drift["modified"]) > 2 else "low"
            else:
                drift["severity"] = "low"

            drift["summary"] = f"Drift detected: {', '.join(parts)}."
        else:
            drift["summary"] = f"All {len(drift['unchanged'])} files unchanged."

        return drift


# ---------------------------------------------------------------------------
# Phase 4: Mode Report
# ---------------------------------------------------------------------------

class ModeReporter:
    """Synthesize findings into a status report and determine operational mode."""

    def __init__(self, genesis: Dict[str, Any], health: Dict[str, Any], drift: Dict[str, Any]):
        self.genesis = genesis
        self.health = health
        self.drift = drift

    def determine_mode(self) -> str:
        """Determine if we are in Sovereign or Simulation mode."""
        db_ok = self.health.get("arangodb", {}).get("reachable", False)
        mcp_ok = self.health.get("mcp_health_url", {}).get("reachable", False)
        fs_ok = all(
            v.get("exists", False)
            for k, v in self.health.get("filesystem", {}).items()
            if k != "tests_dir"  # tests dir not critical
        )
        gen_ok = self.genesis.get("genesis", {}).get("readable", False)

        if db_ok and mcp_ok and fs_ok and gen_ok:
            return "Sovereign"
        elif fs_ok and gen_ok:
            return "Simulation"
        else:
            return "Degraded"

    def flag_issues(self) -> List[Dict[str, str]]:
        """Flag any issues found during boot."""
        issues: List[Dict[str, str]] = []

        # Genesis issues
        gen = self.genesis.get("genesis", {})
        if gen.get("error"):
            issues.append({"phase": "genesis", "severity": "critical", "message": gen["error"]})
        elif not gen.get("exists"):
            issues.append({"phase": "genesis", "severity": "critical", "message": "genesis.md not found"})

        # DB issues
        db = self.health.get("arangodb", {})
        if db.get("configured") and not db.get("reachable"):
            issues.append({"phase": "health", "severity": "warning", "message": "ArangoDB unreachable"})
        elif not db.get("configured"):
            issues.append({"phase": "health", "severity": "info", "message": "ArangoDB not configured"})

        # MCP issues
        mcp = self.health.get("mcp_health_url", {})
        if not mcp.get("reachable"):
            issues.append({"phase": "health", "severity": "warning", "message": "MCP health endpoint unreachable"})

        # Drift issues
        drift_data = self.drift.get("drift", {})
        if drift_data.get("has_drift"):
            issues.append({
                "phase": "drift",
                "severity": drift_data.get("severity", "low"),
                "message": drift_data.get("summary", "Drift detected"),
            })

        # Version change
        vc = self.genesis.get("version_comparison", {})
        if vc.get("version_changed"):
            issues.append({
                "phase": "genesis",
                "severity": "info",
                "message": f"Genesis version changed: {vc.get('previous_version')} → {vc.get('current_version')}",
            })

        return issues

    def build_report(self) -> Dict[str, Any]:
        """Build the full mode report."""
        mode = self.determine_mode()
        issues = self.flag_issues()
        constitution = self.genesis.get("constitutions", {})

        return {
            "boot_timestamp": datetime.now(timezone.utc).isoformat(),
            "operational_mode": mode,
            "status": "healthy" if mode == "Sovereign" else "degraded",
            "genesis": {
                "version": self.genesis.get("genesis", {}).get("version"),
                "size": self.genesis.get("genesis", {}).get("size_human"),
                "readable": self.genesis.get("genesis", {}).get("readable", False),
            },
            "systems": {
                "total": constitution.get("total_files", 0),
                "total_commands": constitution.get("total_commands", 0),
                "roster": [s["name"] for s in constitution.get("systems", [])],
            },
            "connectivity": {
                "arangodb": self.health.get("arangodb", {}).get("reachable", False),
                "mcp_endpoint": self.health.get("mcp_health_url", {}).get("reachable", False),
                "filesystem_ok": all(
                    v.get("exists", False)
                    for v in self.health.get("filesystem", {}).values()
                ),
            },
            "drift": {
                "has_drift": self.drift.get("drift", {}).get("has_drift", False),
                "severity": self.drift.get("drift", {}).get("severity", "none"),
                "summary": self.drift.get("drift", {}).get("summary", ""),
            },
            "issues": issues,
            "issue_count": len(issues),
        }


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def _human_size(size_bytes: int) -> str:
    """Convert bytes to human-readable string."""
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}" if size_bytes != int(size_bytes) else f"{size_bytes} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def format_text_report(report: Dict[str, Any], verbose: bool = False) -> str:
    """Format boot report as human-readable text."""
    lines = []
    sep = "=" * 60

    mode = report["operational_mode"]
    mode_icon = "🟢" if mode == "Sovereign" else "🟡" if mode == "Simulation" else "🔴"

    lines.append(sep)
    lines.append(f"  ABRAXAS SESSION BOOT REPORT")
    lines.append(sep)
    lines.append(f"  Timestamp : {report['boot_timestamp']}")
    lines.append(f"  Mode      : {mode_icon} {mode} Mode")
    lines.append(f"  Status    : {report['status'].upper()}")
    lines.append("")

    # Genesis summary
    gen = report["genesis"]
    lines.append("─" * 40)
    lines.append(f"  GENESIS: v{gen['version']} ({gen['size']})")
    lines.append("")

    # Systems
    sys_info = report["systems"]
    lines.append(f"  Systems Loaded : {sys_info['total']}")
    lines.append(f"  Total Commands : {sys_info['total_commands']}")
    if verbose:
        roster = sys_info.get("roster", [])
        if roster:
            names = ", ".join(roster)
            lines.append(f"  Roster         : {names}")

    lines.append("")

    # Connectivity
    conn = report["connectivity"]
    lines.append("─" * 40)
    lines.append("  CONNECTIVITY:")
    db_status = "✓ connected" if conn["arangodb"] else "✗ unreachable"
    mcp_status = "✓ reachable" if conn["mcp_endpoint"] else "✗ unreachable"
    fs_status = "✓ ok" if conn["filesystem_ok"] else "✗ degraded"
    lines.append(f"    ArangoDB  : {db_status}")
    lines.append(f"    MCP API   : {mcp_status}")
    lines.append(f"    Filesystem: {fs_status}")
    lines.append("")

    # Drift
    drift = report["drift"]
    lines.append("─" * 40)
    lines.append(f"  DRIFT AUDIT: {drift['severity'].upper()} — {drift['summary']}")
    lines.append("")

    # Issues
    issues = report.get("issues", [])
    if issues:
        lines.append("─" * 40)
        lines.append(f"  ISSUES ({len(issues)}):")
        for i, issue in enumerate(issues, 1):
            sev = issue["severity"].upper()
            lines.append(f"    [{sev}] {issue['message']}")
        lines.append("")

    lines.append(sep)
    lines.append(f"  Boot complete ({report['status']}).")
    lines.append(sep)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Abraxas Session Boot Protocol — structured boot sequence",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  session-boot.py              Quiet summary output
  session-boot.py --verbose    Detailed output
  session-boot.py --json       Machine-readable JSON
  session-boot.py -v --json    Verbose JSON (includes all raw phase data)
        """,
    )
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose/detailed output")
    args = parser.parse_args()

    paths = Paths()

    # Phase 1: Genesis Load
    genesis_loader = GenesisLoader(paths)
    genesis_results = genesis_loader.run()

    # Phase 2: Health Check
    health_checker = HealthChecker(paths)
    health_results = health_checker.run()

    # Phase 3: Constitution Drift Audit
    drift_auditor = DriftAuditor(paths)
    drift_results = drift_auditor.run()

    # Phase 4: Mode Report
    reporter = ModeReporter(genesis_results, health_results, drift_results)
    report = reporter.build_report()

    if args.json:
        if args.verbose:
            # Include raw phase data
            output = {
                "report": report,
                "raw_phase_data": {
                    "phase1_genesis": genesis_results,
                    "phase2_health": health_results,
                    "phase3_drift": drift_results,
                },
            }
        else:
            output = report
        print(json.dumps(output, indent=2, sort_keys=True))
    else:
        text = format_text_report(report, verbose=args.verbose)
        print(text)

    # Exit code based on mode
    mode = report["operational_mode"]
    if mode == "Sovereign":
        sys.exit(0)
    elif mode == "Simulation":
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()
