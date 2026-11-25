#!/usr/bin/env bash
# Snapshot remote Git and GitHub metadata without mutating source refs.
set -euo pipefail
umask 077
[[ $# == 2 && "$1" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ && "$2" == /* ]] || { echo "Usage: bash scripts/archive-history.sh OWNER/REPO /absolute/new-archive" >&2; exit 2; }
repo=$1
out=$2
for cmd in git gh python3; do command -v "$cmd" >/dev/null; done
mkdir -- "$out" # refuse overwrite
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT
url="https://github.com/$repo.git"
# Use existing Git credentials; gh auth setup-git may be necessary.
git ls-remote --refs "$url" | sort > "$out/remote-refs-before.tsv"
git clone --mirror "$url" "$work/source.git"
git -C "$work/source.git" for-each-ref --format='%(objectname)%09%(refname)' | sort > "$out/refs.tsv"
# Explicitly fetch available PR heads even when not advertised by mirror clone.
gh api --paginate --slurp "repos/$repo/pulls?state=all&per_page=100" > "$out/pull-requests.json"
python3 - "$out/pull-requests.json" <<'PY' > "$work/prs"
import json, sys
for page in json.load(open(sys.argv[1])):
    for pr in page:
        print(pr["number"])
PY
mkdir "$out/prs"
: > "$out/missing-evidence.txt"
capture() {
    local endpoint=$1 dest=$2
    if ! gh api --paginate --slurp "$endpoint" > "$dest"; then
        rm -f "$dest"
        printf '%s\n' "$endpoint" >> "$out/missing-evidence.txt"
    fi
}
while read -r n; do
    mkdir "$out/prs/$n"
    if ! git -C "$work/source.git" fetch --no-tags origin "refs/pull/$n/head:refs/archive/pull/$n/head"; then
        printf 'PR head %s unavailable\n' "$n" >> "$out/missing-evidence.txt"
    fi
    for kind in commits reviews comments; do
        capture "repos/$repo/pulls/$n/$kind?per_page=100" "$out/prs/$n/$kind.json"
    done
    capture "repos/$repo/issues/$n/comments?per_page=100" "$out/prs/$n/discussion.json"
    capture "repos/$repo/issues/$n/timeline?per_page=100" "$out/prs/$n/timeline.json"
done < "$work/prs"
capture "repos/$repo/issues?state=all&per_page=100" "$out/issues.json"
mkdir "$out/issues"
if [[ -f "$out/issues.json" ]]; then
    python3 - "$out/issues.json" <<'PY' > "$work/issues"
import json, sys
for page in json.load(open(sys.argv[1])):
    for issue in page:
        if "pull_request" not in issue:
            print(issue["number"])
PY
    while read -r n; do
        capture "repos/$repo/issues/$n/comments?per_page=100" "$out/issues/$n-comments.json"
        capture "repos/$repo/issues/$n/timeline?per_page=100" "$out/issues/$n-timeline.json"
    done < "$work/issues"
fi
capture "repos/$repo/actions/runs?per_page=100" "$out/ci-runs.json"
capture "repos/$repo/releases?per_page=100" "$out/releases.json"
git ls-remote --refs "$url" | sort > "$out/remote-refs-after.tsv"
cmp "$out/remote-refs-before.tsv" "$out/remote-refs-after.tsv" || { echo "Remote refs changed during capture; archive again" >&2; exit 1; }
git -C "$work/source.git" for-each-ref --format='%(objectname)%09%(refname)' | sort > "$out/refs.tsv"
python3 - "$out" <<'PY'
import pathlib, sys
p=pathlib.Path(sys.argv[1])
refs=set((p/"refs.tsv").read_text().splitlines())
remote=set((p/"remote-refs-before.tsv").read_text().splitlines())
if not remote.issubset(refs):
    raise SystemExit("Missing advertised refs in mirror")
PY
git -C "$work/source.git" log --all --format='%H %P' > "$out/commit-parents.txt"
git -C "$work/source.git" bundle create "$out/repository.bundle" --all
git -C "$work/source.git" bundle verify "$out/repository.bundle"
git clone --mirror "$out/repository.bundle" "$work/restore.git"
git -C "$work/restore.git" fsck --full
git -C "$work/restore.git" for-each-ref --format='%(objectname)%09%(refname)' | sort > "$work/restore-refs"
cmp "$out/refs.tsv" "$work/restore-refs"
python3 - "$out" "$repo" <<'PY'
import datetime, hashlib, json, pathlib, sys
p=pathlib.Path(sys.argv[1])
manifest={"schema":1,"repository":sys.argv[2],"capturedAt":datetime.datetime.now(datetime.timezone.utc).isoformat(),"gitRestoreVerified":True,"metadataFailures":(p/"missing-evidence.txt").read_text().splitlines(),"scopeLimits":["Remote advertised refs and available PR heads only; no local reflogs or uncommitted work","CI run metadata only; job logs and artifacts require separate capture","No atomic GitHub metadata snapshot; original pre-rebase refs may already be missing","LFS objects and submodule repositories require separate archival","Durable storage and pre-mutation ref recheck require operator verification"]}
(p/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
with (p/"checksums.sha256").open("w") as f:
    for file in sorted(p.rglob("*")):
        if file.is_file() and file.name!="checksums.sha256":
            f.write(hashlib.sha256(file.read_bytes()).hexdigest()+"  "+file.relative_to(p).as_posix()+"\n")
PY
echo "Bundle restored and refs verified. Review manifest gaps, verify checksums and durable storage before cleanup."
[[ ! -s "$out/missing-evidence.txt" ]] || exit 3
