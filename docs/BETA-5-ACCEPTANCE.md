# Beta.5 verification and remaining limits

Date: 2026-09-26. Scope: native remote compatibility, bounded status reporting,
documented smartphone voice startup and synchronized repository delivery.
The operator explicitly requested both repository releases and local deployment.
Repository visibility and the original OpenAI CLI remain unchanged.

## Verification record

| Check | Evidence and boundary |
|---|---|
| Automated regression | 108 tests passed in each repository line, including TC-029/030 socket/home cases and TC-032 parity failure cases; 37 remote tests also passed as an unprivileged user |
| Independent review | Independent code/documentation review passed; seven separate synthetic socket/home experiments passed, including real Unix-socket protocol and file-preservation checks |
| Product parity | All 71 source files passed the product comparison; only documented historical provenance and publication metadata differ. The release gate repeats this against clean committed trees |
| Local installation | Verified public source archive installed on the reference system; both installed HACP scripts byte-match both release archives; native tools, configuration and Supervisor options preserved |
| Native runtime | Original CLI 0.157.1; authenticated persistence and add-on audits passed without warnings; beta.5 status reports running/connected on Studio Code Server 7.1.1 |
| Smartphone voice | Operator-confirmed existing-chat voice and complete new-chat-in-explicit-folder-to-voice route; automatic home detection still fails |
| Artifacts/publication | Both archives passed commit/version/checksum verification and 108 tests per clean extraction; both release-commit CI runs passed; both prereleases and downloaded assets verified |

## Quality review scope

The product boundary is the HACP launcher and persistence scripts on Linux in
Studio Code Server. The smartphone client and OpenAI service are external.
The quality owner is the delivery agent (R19); a separate reviewing agent (R39)
checks implementation and evidence without authoring these changes. The
reference-system operator remains the operational acceptor. Automated review
does not replace that acceptance or establish regulatory conformity.

The internal review uses the edition references
[ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html),
[ISO/IEC 25030:2019](https://www.iso.org/standard/72116.html) and
[ISO/IEC 25040:2024](https://www.iso.org/standard/83467.html).
Official catalogue metadata was checked on the date above. Licensed normative
texts were not supplied or evaluated; this is a project-owned quality checklist,
not a standards conformity assessment. No standard text is reproduced.

All nine product-quality areas have an explicit scope decision below. Measures
are project-defined, with zero tolerance unless specified. R19 owns each
required measure; R39 independently reviews the linked evidence.

| Quality area | Decision | Requirement, measure, target and evaluation |
|---|---|---|
| Functional suitability | Required | REQ-I-006/007: zero unexpected results across direct/alias socket and home-selection cases; TC-029/030 |
| Performance efficiency | Required | REQ-O-006: retain the 45-second native-start subprocess timeout and 8-second socket-read deadline; inspect bounded code and run timeout regressions; no throughput benchmark claimed |
| Compatibility | Required | REQ-F-007, REQ-I-006/007: zero CLI/model overrides or persistent-home changes; TC-024/029/030 and separate live status check |
| Interaction capability | Required | REQ-O-007: the complete smartphone startup sequence documented, with explicit folder selection and unresolved automatic detection; TC-031 operator report plus documentation review |
| Reliability | Required | REQ-Q-003, REQ-O-006: zero status mutations and zero replacement starts when endpoint state is unknown; TC-015/029/030, timeout and boot-warning regressions |
| Security | Required | REQ-S-001, REQ-Q-003: zero accepted unsafe synthetic endpoints and zero repository/history scan findings; TC-SEC-001/029 and independent socket review |
| Maintainability | Required | REQ-Q-005: zero unexplained differences across both product trees, tests and shared docs; TC-032 and clean parity gate |
| Flexibility | Required within the supported Linux boundary | REQ-O-003, REQ-I-007: zero unexpected results for supported runtime roots and matching/missing/dangling/wrong default aliases; TC-001/030; other host platforms are outside this release evidence |
| Safety | Not applicable as a functional-safety product | HACP does not command physical devices or provide a safety function. Preservation and refusal behavior are evaluated under reliability/security; no safety integrity claim |

Quality in use is relevant to the narrow smartphone workaround;
[ISO/IEC 25019:2023](https://www.iso.org/standard/78177.html) is the edition
reference. TC-031 records a specific operator-observed route, not a broad
usability study. ISO/IEC 25012 is not activated: this change contains no domain
data product or data-quality evaluation. ISO/IEC 25023 measures are not used;
the measures above are local acceptance criteria.

## Open boundaries

- OPEN-REMOTE-001: automatic remote-home recognition still fails in the
  reported iOS client. A client-side issue is plausible, but neither iOS-only
  causation nor a server-side cause has been established.
- Use [the explicit-folder voice procedure](REMOTE-STARTUP.md#smartphone-voice-startup-with-an-explicit-folder)
  for the confirmed workaround. Other smartphone clients are unverified.
- No new whole-add-on restart, container replacement or Home Assistant host
  reboot is claimed for beta.5. Stale temporary-socket behavior is covered by
  isolated tests; older lifecycle evidence remains attributed to its own release.
- A separate fresh installation on another host, broad platform coverage,
  native memory generation/retrieval and interactive client approval behavior
  remain outside this maintenance-release evidence.
- Native package updates remain under OpenAI control. Future CLI transport
  changes require fresh compatibility testing, not a permanent version pin.

The release pages and their checksum manifests are authoritative for published
commit IDs and artifact hashes. Different provenance produces different archive
hashes; the [parity policy](REPOSITORY-PARITY.md) defines the identical product
content required in both lines.

## Publication and local installation completed

Both repository lines published `v0.9.0-beta.5` on 2026-09-26. Their source
archives and checksum manifests were downloaded again and matched the verified
local builds. The public source archive was installed and audited successfully.
The original CLI and native service were not restarted by that installation.
A separate fresh public clone passed the naming/privacy review of all 412
reachable Git objects at the release tag, 71 current source files, all archive
files and release text. The internal template name is absent from public content.

This is a post-publication documentation addendum. The tagged source snapshot
necessarily precedes artifact installation/publication and records those gates
as pending; this addendum and the
[published release record](https://github.com/Domuno18/home-assistant-codex-persistence/releases/tag/v0.9.0-beta.5)
record the completed checks. Published archives and tags are not rebuilt or
replaced by this documentation update. OPEN-REMOTE-001 remains open.
