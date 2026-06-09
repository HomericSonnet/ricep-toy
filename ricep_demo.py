"""Minimal RICEP demonstrator for the short paper.

The script creates five record-in-context evidence packages from the same
appointment-letter document representation, computes root hashes, and simulates
common change scenarios.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path


def canon(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def h(value):
    return hashlib.sha256(canon(value).encode("utf-8")).hexdigest()


DOCUMENT = {
    "representation_id": "doc:appointment-letter:pdf-v1",
    "format": "application/pdf",
    "size": 48211,
    "content_sha256": hashlib.sha256(
        b"Mock University appointment letter for Dr. A, 2027-08-15"
    ).hexdigest(),
}

VALIDATION = {
    "procedure_id": "RICEP-file-membership-validation",
    "version": "2027.1",
    "required_relations": ["record-file", "file-series", "record-creator", "record-action"],
}

INSTANCES = [
    ("president", "President hiring file", "formal appointment authority"),
    ("dean", "Dean personnel file", "faculty allocation"),
    ("department", "Department workload file", "teaching/workload responsibility"),
    ("finance", "Finance salary file", "salary activation"),
    ("employee", "Employee personal file", "personal employment status"),
]


def package(instance_id, file_title, role):
    record_id = f"rec:appointment-letter:{instance_id}"
    series_id = f"series:{instance_id}:appointments"
    context = {
        "record_id": record_id,
        "creator": "Mock University HR Office",
        "action": "faculty appointment",
        "file": file_title,
        "series": series_id,
        "record_role": role,
    }
    bond = {
        "nodes": [
            record_id,
            DOCUMENT["representation_id"],
            file_title,
            series_id,
            context["creator"],
            context["action"],
        ],
        "edges": [
            [record_id, "hasRepresentation", DOCUMENT["representation_id"]],
            [record_id, "isPartOfFile", file_title],
            [file_title, "isPartOfSeries", series_id],
            [record_id, "wasCreatedBy", context["creator"]],
            [record_id, "documentsAction", context["action"]],
        ],
    }
    events = [
        {
            "event_id": f"event:ingest:{instance_id}:2027-08-16",
            "type": "ingest",
            "agent": "University records system",
            "date": "2027-08-16",
            "outcome": "success",
        },
        {
            "event_id": f"event:fixity:{instance_id}:2027-08-17",
            "type": "fixity-check",
            "agent": "Preservation service",
            "date": "2027-08-17",
            "outcome": "match",
        },
    ]
    return {
        "D": copy.deepcopy(DOCUMENT),
        "C": context,
        "B": bond,
        "P": [{"agent": "Mock University Archives", "custody": "institutional"}],
        "E": events,
        "V": copy.deepcopy(VALIDATION),
        "K": [{"signature": f"mock-signature-{instance_id}", "key_id": "key:archives:2027"}],
        "M": [],
        "A": [],
    }


def compute_roots(pkg):
    event_types = [event["type"] for event in pkg["E"]]
    has_migration = "format-migration" in event_types
    has_revalidation = "revalidation" in event_types
    validation_outputs = {
        "required_relations_present": True,
        "fixity_checked": True,
        "migration_event_count": event_types.count("format-migration"),
        "revalidated_after_migration": (has_revalidation if has_migration else "not_required"),
        "procedure": pkg["V"]["procedure_id"],
        "version": pkg["V"]["version"],
    }
    roots = {
        "DocumentRoot": h(pkg["D"]),
        "ContextRoot": h({"B": pkg["B"], "C": pkg["C"]}),
        "PreservationRoot": h({"E": pkg["E"], "P": pkg["P"]}),
        "ValidationRoot": h({"V": pkg["V"], "outputs": validation_outputs}),
    }
    roots["RecordInContextRoot"] = h(
        [
            roots["DocumentRoot"],
            roots["ContextRoot"],
            roots["PreservationRoot"],
            roots["ValidationRoot"],
        ]
    )
    proof_cache = {
        "proof_type": "file-membership-proof",
        "record_id": pkg["C"]["record_id"],
        "file": pkg["C"]["file"],
        "series": pkg["C"]["series"],
        "graph_version_hash": roots["ContextRoot"],
        "validation_procedure": f"{pkg['V']['procedure_id']}@{pkg['V']['version']}",
        "status": "current",
    }
    pkg["M"] = [proof_cache]
    pkg["A"] = [
        {
            "substrate": "mock-ledger",
            "commitment": roots["RecordInContextRoot"],
            "timestamp": "2027-08-18T00:00:00Z",
        }
    ]
    return roots


def scenario_roots(base_pkg):
    scenarios = {}
    baseline = compute_roots(copy.deepcopy(base_pkg))
    scenarios["baseline"] = {"roots": baseline, "response": "current valid evidence state"}

    changed = copy.deepcopy(base_pkg)
    changed["D"]["content_sha256"] = hashlib.sha256(b"silently edited file").hexdigest()
    scenarios["bitstream_alteration"] = {
        "roots": compute_roots(changed),
        "response": "fixity failure",
    }

    migrated = copy.deepcopy(base_pkg)
    migrated["D"]["format"] = "application/pdfa"
    migrated["E"].append(
        {
            "event_id": "event:migration:finance:2028-01-04",
            "type": "format-migration",
            "agent": "Preservation service",
            "date": "2028-01-04",
            "outcome": "success",
        }
    )
    migrated["E"].append(
        {
            "event_id": "event:revalidation:finance:2028-01-04",
            "type": "revalidation",
            "agent": "Preservation service",
            "date": "2028-01-04",
            "procedure": f"{migrated['V']['procedure_id']}@{migrated['V']['version']}",
            "outcome": "success",
        }
    )
    scenarios["legitimate_migration"] = {
        "roots": compute_roots(migrated),
        "response": "new preservation and revalidation events",
    }

    contextual = copy.deepcopy(base_pkg)
    contextual["C"]["file"] = "Finance salary and audit file"
    contextual["B"]["edges"][1] = [
        contextual["C"]["record_id"],
        "isPartOfFile",
        contextual["C"]["file"],
    ]
    contextual["E"].append(
        {
            "event_id": "event:context-update:finance:2028-03-12",
            "type": "metadata-correction",
            "agent": "Archivist",
            "date": "2028-03-12",
            "outcome": "superseded-context",
        }
    )
    scenarios["contextual_update"] = {
        "roots": compute_roots(contextual),
        "response": "new context graph version + superseding root",
    }

    suspicious = copy.deepcopy(base_pkg)
    suspicious["C"]["file"] = "Unrecorded finance file"
    suspicious["B"]["edges"][1] = [
        suspicious["C"]["record_id"],
        "isPartOfFile",
        suspicious["C"]["file"],
    ]
    scenarios["suspicious_context_change"] = {
        "roots": compute_roots(suspicious),
        "response": "contextual integrity warning",
    }

    procedure = copy.deepcopy(base_pkg)
    procedure["V"]["version"] = "2027.2"
    procedure["V"]["required_relations"].append("record-rights")
    scenarios["procedure_update"] = {
        "roots": compute_roots(procedure),
        "response": "new procedure version + revalidation",
    }
    return scenarios


def main():
    packages = {
        instance_id: package(instance_id, file_title, role)
        for instance_id, file_title, role in INSTANCES
    }
    package_roots = {
        instance_id: compute_roots(copy.deepcopy(pkg))
        for instance_id, pkg in packages.items()
    }
    scenarios = scenario_roots(packages["finance"])
    output = {
        "packages": packages,
        "package_roots": package_roots,
        "finance_scenarios": scenarios,
    }
    out_path = Path(__file__).with_name("ricep_demo_results.json")
    out_path.write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {out_path}")
    print("instance,DocumentRoot,ContextRoot,RecordInContextRoot")
    for instance_id, roots in package_roots.items():
        print(
            f"{instance_id},{roots['DocumentRoot'][:12]},"
            f"{roots['ContextRoot'][:12]},{roots['RecordInContextRoot'][:12]}"
        )
    print("scenario,response,RecordInContextRoot")
    for name, data in scenarios.items():
        print(f"{name},{data['response']},{data['roots']['RecordInContextRoot'][:12]}")


if __name__ == "__main__":
    main()
