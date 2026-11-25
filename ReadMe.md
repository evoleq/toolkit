# Evoleq ToolKit

<p align="center">
  <img src="assets/toolkit-original-stokes.png" alt="ToolKit – Original Stokes: cat mascot, turquoise lambda and Stokes formula" width="360" />
</p>


**The Art of Dynamic Composition.**

Mathematically grounded, compositional software tools for Kotlin Multiplatform.

> Formerly MathCat. The main repository is now [`evoleq/toolkit`](https://github.com/evoleq/toolkit). Gradle modules use `toolkit-*` and Kotlin packages use `evoleq.toolkit.*`. See the [migration guide](docs/TOOLKIT-MIGRATION.md).

ToolKit is being reworked as a **small, law-aware foundation** for compositional software. The first step is a research prototype for **algebraic type operations**, not a claim that the Kotlin language already supports higher-kinded type parameters.

## Maven Central release path

The **Maven Central publishing workflow** follows each new CI-verified SemVer release, produces signed, platform-complete distributions under `org.evoleq.toolkit:toolkit-*:VERSION` and submits them to Sonatype for automatic validation and publication. Remote consumer evidence is recorded separately.
The source release alone does not establish that these artifacts are live.
See [Central publishing](docs/CENTRAL-PUBLISHING.md) for requirements,
release provenance, the operator checklist and post-release verification.
JitPack remains a separate legacy compatibility path.

## Current module integration (draft)

The [integration branch](https://github.com/evoleq/toolkit/pull/18) combines
the original Ktor-independent API DSL, portable Result, composable serializer
registry and optional KSP, Ktor client/server adapters, JVM Contextual and pure
transforms. Compatibility tracking and JitPack smoke testing cover the
expanded module graph. This remains a **draft until CI has passed**.
The deliberately deferred API/Boundary/Environment DX work is tracked in
[issue #17](https://github.com/evoleq/toolkit/issues/17).
See [integration decisions](docs/INTEGRATION-2026-11-19.md).

## ToolKit Core (new draft module)

The experimental [`toolkit-core`](toolkit-core) module introduces small, nominal, lambda-friendly `Reader` and `Writer` types; **lawful** `Lens` contracts; composable but **not necessarily lawful** `Selection`; and a pure, non-`suspend` State monad.

The central composition patterns are `Lens * Lens`, `Lens * Selection`, `Lens * Reader`, `Lens * Writer`, and `Writer.contraMap`. Keyed collection Writers `updateAllBy` and `upsertAllBy` illustrate the same production-proven idea from Solyton's frontend Actions without copying the old library's ambiguous duplicate-handling semantics.

The **mathematical origins are part of the API design**: [Mathematical foundations](docs/MATHEMATICAL-FOUNDATIONS.md) explains function composition, Writer contravariance, Lens/Selection laws, State's monad multiplication and Kleisli arrows. In particular, the capitalized top-level `Update` constructor produces a `KlState` that changes state while preserving the carried value.

The public DSL now follows a simple rule: **constructors** `Return`, `Update`, `IdReader`, `IdLens`, `FilterBy`, `Append`, `AppendAll`, `UpdateAllBy` and `UpsertAllBy` are capitalized and can be used directly; **operations** `map`, `multiply`, `bind`, `get`, `set` and `contraMap` stay lowercase. Future monads may reuse the name `Return` in their own packages; Kotlin's `import ... as ...` syntax disambiguates call sites without changing mathematical vocabulary. A [commonTest import-alias smoke test](toolkit-core/src/commonTest/kotlin/evoleq/toolkit/consumer/ConstructorImportsTest.kt) verifies the public core's alias ergonomics.

In particular, **`Get(lens)` and `Set(lens)`** turn an optic into the corresponding `Reader` and `Writer`; `Get<S>()` constructs a pure state-read computation. Map readers use `evoleq.toolkit.core.reader.maps.Get(key)` / `GetForSure(key)`; explicit imports or import aliases keep these meanings clear. A `State` is directly callable (`state(s)`) without importing a separate invocation extension. Packages now keep the standalone constructors unambiguous: `core.state`, `core.reader`, `core.writer`, `core.optics`, `core.collections` and `core.reader.maps`.

### Storage and Memory

`Source<T> = Reader<Unit,T>` is restored from legacy Evoleq. The `storage` package now provides a synchronous `Storage<T>` interface with **read()/write()**, a derived `storage.source(): Source<T>`, plus a plain `Memory(initial)` backend. One Storage may combine several separate Memories via its read/write callbacks, including backends with different Compose observation policies. `Storage * Reader` yields a live Source, while `Storage * Lens` and `Storage * Selection` yield focused Storage handles. The reconciled legacy PR #3 also adds `Dispatcher<A> = Writer<Unit,A>`, `Storage * Writer -> Dispatcher`, `Read(storage)` and `Dispatch(storage)`. Unlike the suspending `ActionDispatcher<S>` in `toolkit-actions`, this `Dispatcher<A>` executes a synchronous Writer over `Unit`. See [Storage command algebra](docs/STORAGE-COMMANDS.md).

**Memory is not Compose-observable.** A future Compose adapter can back the **same** Storage interface with `MutableState<T>`, allowing the caller to decide which data should participate in snapshot-driven recomposition. The core intentionally has **no Compose dependency**. See [Storage, Memory and Compose boundaries](docs/STORAGE-AND-MEMORY.md) and the [composition research note](docs/STORAGE-COMPOSITION.md) on products, sums, and using existing storage handles. The latter is **design-only**; no generic sum, product or absorb operator is exposed yet. The Storage review includes a **read-only** review of Solyton's existing mixed observable/non-observable frontend Storage. The concrete frontend implementation is **not ported** in this draft.

**Action dispatch is a separate, composable capability.** The [action-dispatcher architecture note](docs/ACTION-DISPATCH-AND-STORAGE.md) explores pairing `Storage<S>` with `ActionDispatcher<S>` as an application Store, transporting both through the same Lens, and routing a **tagged sum of commands** over product storage. This is research, not an implemented API; the existing Solyton frontend is unchanged.

See [Core architecture, laws and tests](docs/CORE-ARCHITECTURE.md). This is still a **draft proposal**: there is no stable API, release, or publishing decision.

## ToolKit 2.0 (research prototype)

The repository also contains an experimental `toolkit-type-algebra` Kotlin Multiplatform module, sharing the targets described in [Multiplatform support](docs/MULTIPLATFORM.md):

- a value-level **AST** for unary type constructors, identity, composition and pointwise sum/product;
- tagged `Sum2<A,B>` and `Product2<A,B>`, with explicit distributivity/factorization isomorphisms;
- common tests used by independently configured JVM, JS, Native and WebAssembly targets; Android and Apple cross-compilation are checked separately.

**Important:** These are normal Kotlin types and transformations. They are *not* built-in sum/product syntax, an HKT system, a compiler plugin or a proof of the laws.

See [Architecture and research notes](docs/ARCHITECTURE.md) for the mathematical definitions, limits, next steps and the relationship to [fp-axioms](https://github.com/evoleq/fp-axioms).

### Build and test locally

With JDK 17+ and Gradle 9.2.1 available:

```sh
gradle :toolkit-type-algebra:jvmTest :toolkit-type-algebra:jsNodeTest \
       :toolkit-core:jvmTest :toolkit-core:jsNodeTest
```

For the JS tests, Kotlin/Gradle downloads the required Node.js environment when necessary. Gradle is pinned in CI; a Gradle wrapper can be added after the initial build has been verified.

**Platform targets:** Both modules declare JVM, JavaScript/Node.js, WebAssembly/Node.js, Android, Linux, Windows, iOS and macOS. The [platform matrix](docs/MULTIPLATFORM.md) specifies exact architectures, host requirements and what CI really verifies. **CI validates all integrated modules and publishes no artifacts to Maven Central.** Experimental JitPack publication of tagged source is available on demand, but remote JitPack and cross-platform artifact verification are still pending. The final license remains open.

## Runtime-composable plugins (new research slice)

The independently published [`toolkit-plugins`](toolkit-plugins) MPP module
offers **pure deterministic dependency planning** followed by a Kleisli
composition of effectful discovery, loading and activation. Platform adapters
are located in `jvmMain` (local JAR + SHA-256 + ServiceLoader) and `jsMain`
(ES-module `import()` + fresh HTTP manifest). Other targets can plan/validate
but do not claim a dynamic executable loader. No security sandbox or automatic
version-skew compatibility is implied.

See [Runtime Plugin Architecture](docs/PLUGIN-COMPOSITION.md). The new
[optional Action and Navigation bridge](toolkit-plugins-actions) binds
host-owned typed Actions to allowlisted plugin commands. A pure **Prism**
selects already-loaded plugin slots; only misses trigger loading.

## Earlier MathCat experiments

The earlier MathCat libraries remain separate and are **not** implied dependencies of the new module. They are useful historical references; their API quality and contracts are being reassessed before any potential migration.

- [mathcat-core](https://github.com/evoleq/mathcat-core), [mathcat-morphism](https://github.com/evoleq/mathcat-morphism), [mathcat-continuation](https://github.com/evoleq/mathcat-continuation)
- [mathcat-reader](https://github.com/evoleq/mathcat-reader), [mathcat-state](https://github.com/evoleq/mathcat-state), [mathcat-store](https://github.com/evoleq/mathcat-store)
- [mathcat-lens](https://github.com/evoleq/mathcat-lens), [mathcat-prism](https://github.com/evoleq/mathcat-prism), [mathcat-profunctor-optics](https://github.com/evoleq/mathcat-profunctor-optics)
- [mathcat-result](https://github.com/evoleq/mathcat-result), [mathcat-structure](https://github.com/evoleq/mathcat-structure), [mathcat-yoneda](https://github.com/evoleq/mathcat-yoneda)

These repositories have **not** been archived or made private. Existing consumers and references should be evaluated before changing their visibility.

## Design principles

- Prefer explicit mathematical contracts over attractive but unverified names.
- Separate the laws an operation promises from whether it can be composed.
- Keep pure operations apart from suspendable execution and platform effects.
- Preserve useful real-world composition patterns such as `Lens * Writer` and `Writer.contraMap`.
- Keep experimental language/tooling research separate from the usable library.

The public API, licensing and release policy for ToolKit 2.0 are still under review.

## External dependency versions

The build uses [Gradle Version Catalog](gradle/libs.versions.toml) for external
Kotlin, Android, KSP, Ktor, kotlinx and JUnit versions. See the
[dependency versioning guide](docs/GRADLE-VERSION-CATALOG.md) for the
separation from ToolKit's shared release SemVer and compatibility manifest.
