# Preserve History Before Consolidation

**No destructive consolidation without verified historical preservation.**

The development history is a research artifact, distinct from the release history and current software. Before rebase, squash, force push, branch deletion or consolidation, preserve original refs and relevant contextual evidence. This is a collaboration contract, not a server-side enforcement mechanism.

## Procedure

1. Coordinate a short maintenance window; preserve local-only commits, reflogs and uncommitted work separately. Do not expose secrets.
2. With Git, Python 3 and authenticated GitHub CLI installed, run:
   ```sh
   bash scripts/archive-history.sh evoleq/toolkit /absolute/private/archive/toolkit-before-consolidation
   ```
   Use a new directory outside the checkout. Git authentication must also work (if necessary, configure gh auth setup-git).
3. Inspect manifest.json and missing-evidence.txt. The script compares remote refs before/after, makes a full bundle, restores it into a fresh mirror, checks object integrity and exact ref equality. Exit 3 means missing metadata; any nonzero exit blocks routine cleanup pending review.
4. Verify checksums (from archive directory: sha256sum -c checksums.sha256), copy archive into access-controlled durable storage with a second backup, and verify the copied archive. Do not commit bundles, private discussions or logs to the public repository.
5. Separately capture relevant CI job logs/artifacts before retention expires, PR head/base versions already lost to rebase where recoverable, architecture decisions and chat/ai-command records. Document unavailable evidence. Git alone cannot recover these. LFS content and submodules require separate backups.
6. Record storage locator, manifest digest, verification results and unresolved gaps in the consolidation issue. Immediately before each destructive operation compare affected current refs with their archived values. If changed, snapshot again. Require explicit review of any missing evidence; never delete refs merely because a PR is closed.

The script does not take an atomic GitHub metadata snapshot, enforce branch protection, upload to storage or delete anything. The remote ref comparison detects many concurrent changes, not all transient changes. Use a maintenance window. Archive contents may be sensitive even if the repository is public.

## Reconstruction

Use commit-parents.txt and refs.tsv to render exact Git DAG edges; PR metadata and patch-equivalence links must be represented separately from commit parent edges. See #36 for book figures and research questions. Preserve raw inputs and reproducible plotting scripts. Avoid interpreting clean rebased history as the original development process.

This contract should also be transferred to ai-command when access is available.
