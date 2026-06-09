# RICEP Toy Demonstrator

This repository contains a minimal, dependency-free Python demonstrator for the
Record-in-Context Evidence Package (RICEP) model described in the paper draft
"Beyond Document Hashes: A Record-in-Context Evidence Architecture for Digital
Record Authenticity."

The script creates five record-in-context evidence packages from the same mock
university appointment-letter representation. It then computes:

- `DocumentRoot`
- `ContextRoot`
- `PreservationRoot`
- `ValidationRoot`
- `RecordInContextRoot`

It also simulates a baseline state plus five change scenarios for the finance-file package:

- baseline state
- silent bitstream alteration
- legitimate preservation migration
- contextual metadata update
- suspicious context change
- validation procedure update

The demonstrator is intentionally small. It is not a production archival
system, a preservation repository, or a full RiC-O/PREMIS implementation. Its
purpose is to make the paper's core claim reproducible: identical document
fixity can coexist with different record identities, and contextual changes must
be interpreted jointly with preservation-event evidence.

## Requirements

Python 3.10 or later. No external dependencies are required.

## Run

```bash
python ricep_demo.py
```

The script writes `ricep_demo_results.json` and prints a compact summary of
record roots and change-scenario responses.

## Expected Result

All five appointment-letter instances share the same `DocumentRoot`, but they
produce different `ContextRoot` and `RecordInContextRoot` values. The finance
package simulations show that:

- bitstream alteration changes the document-root path and is reported as a
  fixity failure;
- legitimate migration adds preservation and revalidation events;
- contextual update changes both `ContextRoot` and `PreservationRoot`;
- suspicious context change changes `ContextRoot` without a matching
  preservation event;
- procedure update changes `ValidationRoot` and requires revalidation.

## License

MIT License.
