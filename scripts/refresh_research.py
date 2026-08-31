"""Member 8 work file: controlled quarterly research refresh.

Follow the TODOs below in order. Never overwrite ``data/companies.csv``
implicitly.

Goal: provide a controlled refresh process and expose evidence/status in the application.

1. Create a command-line refresh script with `--dry-run`, explicit input/output paths, date metadata, and a reviewable change report.
2. The script must stage proposed research updates; it must not overwrite the canonical CSV without an explicit approved write action.
3. Update the report output to include research date, analysis status, confidence when available, and evidence items while preserving existing frontend keys.
4. Update the company-profile popup to display evidence/status in the existing design system, including an understandable fallback/review label.
5. Add a short operator runbook in the README: quarterly steps, review criteria, backup/rollback process, and required tests.
6. Test dry-run, no-change refresh, proposed-change report, report serialization, and popup rendering for verified, fallback, and needs-review states.
"""


def refresh_research() -> None:
    """Prepare the quarterly research refresh process."""
    # TODO(1): Add explicit input/output paths and a --dry-run command option.
    # TODO(2): Request candidate evidence using services.research_sources.
    # TODO(3): Generate a dated, reviewable change report before writing data.
    # TODO(4): Require an explicit approved-write option for canonical updates.
    # TODO(5): Create a backup and document rollback before every write.
    # TODO(6): Test dry run, no changes, proposed changes, and approved writes.
    pass
