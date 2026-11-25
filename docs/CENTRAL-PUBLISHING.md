# Maven Central publishing for Evoleq ToolKit

This is a **separate** publication path from JitPack and the old local
`org.evoleq` development coordinates. The Maven Central namespace is
`org.evoleq.toolkit`; release artifacts have the same project names as the
compatibility manifest and **one shared SemVer**. For example:

```kotlin
implementation("org.evoleq.toolkit:toolkit-core:0.2.0")
implementation("org.evoleq.toolkit:toolkit-actions:0.2.0")
```

These are illustrative coordinates until Central actually validates and
publishes an artifact. `toolkit-serialization-ksp-fixture` is test-only.

## Automated releases

The SemVer workflow calls Central publishing directly after creating a new CI-verified tag and GitHub release. The Portal uses AUTOMATIC mode. The deployment receipt is attached to the GitHub release before polling; a separate publication record is attached after PUBLISHED and a remote-only Gradle consumer check. No new release means no upload. Configure the maven-central environment without required reviewers if fully unattended publishing is desired.

For recovery, dispatch Central publishing with the existing tag and, if needed, its Portal deployment UUID. A recorded deployment is reused; already-visible versions are not uploaded again. If the upload succeeded but its receipt could not be attached, recover the UUID from the workflow log or Portal before retrying. Never blindly retry an ambiguous upload. The automated path requires tags containing the new scripts and smoke configuration; historical tags require the original workflow or a separately reviewed recovery procedure.

## Release gates

1. Verify the DNS ownership challenge for `evoleq.org` with Sonatype and
   confirm `org.evoleq.toolkit` is in the verified Portal namespace.
2. **Decide the public distribution license.** This repository does not yet
   contain a license declaration. Do not invent a license in a POM.
   Set repository Actions variables `CENTRAL_LICENSE_NAME` and
   `CENTRAL_LICENSE_URL` (HTTPS, with the real chosen license).
3. Create a Sonatype Central Portal publishing token and configure GitHub
   **environment** `maven-central` (recommended: required reviewers).
   Store `CENTRAL_USERNAME` and `CENTRAL_PASSWORD` as environment secrets
   (the Portal token username and password, **not** GitHub credentials).
4. Create a PGP signing key, register its public key with a discoverable
   key server and store `CENTRAL_SIGNING_KEY` (ASCII armored *private* key)
   and `CENTRAL_SIGNING_PASSWORD` as environment secrets. Never commit keys.
5. Merge only after full existing CI, compatibility, Central metadata,
   signatures, and independent-consumer smoke tests pass.
6. Wait for a new annotated `vX.Y.Z` tag created by the existing
   `.github/workflows/semver-tags.yml` after the exact master CI passes.
   Do not use old JitPack-style versions beginning with `v` in Central.
7. The SemVer job calls `Maven Central publishing` with that tag. It verifies the tag's reachability from master and the successful
   **push CI for its exact commit** before any credentialed build starts.

The release workflow builds KMP root/JVM/JS/Wasm/Android/Linux variants on
Linux, iOS/macOS variants on macOS, and MinGW on Windows. It signs each
publication, combines all platform artifacts, checks full manifest coverage,
checks transitive internal POM coordinates, checks signatures and required
POM fields, adds required checksums, and uploads **one ZIP** to Sonatype's
Central Publisher Portal API.

The deployment uses `AUTOMATIC` mode: Sonatype validates and publishes it. An upload response is not proof that it is live. No credentialed release runs on PRs; only the trusted release chain or explicit recovery can invoke publishing.

## Local smoke

JDK 17, Gradle 9.2.1, an Android SDK (for Android staging) and a temporary
PGP key are needed for complete Linux staging. For a JVM-only smoke, choose
the root+JVM publication tasks instead of all Linux tasks.

```bash
python3 -m unittest discover -s scripts/tests -v
python3 scripts/release.py validate
# Set CENTRAL_SIGNING_KEY and CENTRAL_SIGNING_PASSWORD, and real license metadata:
export CENTRAL_PUBLISHING=true
export RELEASE_VERSION=0.2.0
export CENTRAL_LICENSE_NAME="your chosen license"
export CENTRAL_LICENSE_URL="https://example.org/your-chosen-license"
gradle --no-daemon $(python3 scripts/central_publication_tasks.py linux)
python3 scripts/central_bundle.py verify --version 0.2.0 --scope linux
```

`bundle` refuses a partial host release. It is only run after collecting
the three platform artifacts:

```bash
python3 scripts/central_bundle.py bundle --version 0.2.0
```

## Existing compatibility contract

`compatibility/modules.json` is authoritative for publishable modules and
their `same-release` dependencies. The existing planner and CI gate retain
the source-version policy; this change does **not** introduce per-module
versions, automatic ABI/behavior/wire compatibility proofs, or GitHub/JitPack
runtime dependency requirements.

Gradle Module Metadata in the KMP root references published target variants;
**all configured platform artifacts must ship together.** The CI smoke checks
only the independent JVM consumer; actual Central availability and consumer
resolution for Android/Native are a separate post-deployment verification.
The existing targeted JetBrains Kotlin stdlib dependency-resolution workaround
also applies to release builds pending a verified upstream fix.

The root `ReadMe.md` is currently packaged in placeholder Javadoc JARs.
Replace this with generated API documentation when the documentation pipeline
is available. No existing development or JitPack workflow is removed.
