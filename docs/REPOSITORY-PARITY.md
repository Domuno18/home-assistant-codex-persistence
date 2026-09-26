# Public and private product parity

From beta.5 onward, both repository lines advance together: the same product
version, executable code, tests, shared documentation and release behavior.
The private line preserves additional project origin and publication history.
Neither matching version numbers nor different Git commit IDs alone establish
product parity.

The read-only checker compares file inventories, executable status and content.
It includes non-ignored new files during development. Only these existing
provenance fields may differ:

- `project-definition.json`: repository identity, visibility and publication
  approval metadata; requirements and product scope still compare exactly.
- `docs/BACKLOG.md`: the single historical BL-008 project-origin line.
- `docs/BETA-4-ACCEPTANCE.md`: the historical commit, archive checksum and
  line-specific release link; all behavioral evidence still compares exactly.

There are no whole-file or runtime-code exclusions. Neutral repository
administration scripts are present in both lines. Their private-repository
guards remain in force; use the release procedure for public publication.
Private provenance is reviewed before transfer and never merged wholesale into
public history. Additional exceptions need a documented, reviewed policy
change, not a skipped check.

```sh
python3 scripts/check_repository_parity.py \
  --private /path/to/private-checkout --public /path/to/public-checkout
```

`./release.sh` requires `HACP_PEER_REPO` and checks both clean committed trees
before building or tagging. The same comparison must be run again after any
release-related edits and before pushing. Each repository also runs its own
complete validation and security scan. Git commit IDs and archive checksums
can differ because approved provenance differs; compare product contents.

REQ-Q-005 / AC-020: zero unexplained product or version differences.
DOM-R-022: only explicitly listed provenance fields may differ.
TC-032 tests positive comparison, code/version/docs drift, extra files,
incorrect line identity, dirty release candidates and symlink rejection.

The release gate is mandatory for maintainers of these two lines. A downstream
single-repository fork must deliberately adapt its own publication policy;
ordinary installation from a source archive does not require either checkout.
