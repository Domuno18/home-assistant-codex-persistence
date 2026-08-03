# Contributing

Thanks for helping improve this community beta. Bug reports, tested hardware
reports, documentation fixes, and pull requests are welcome.

## Before opening an issue

- Do not include tokens, `auth.json`, `hosts.yml`, session files, databases,
  chat text, a populated `MEMORY.md`, Supervisor tokens, or diagnostic output
  that may contain private paths or account data.
- Run the read-only audit and include only the `OK`/`BLOCK` check names and
  short redacted messages that are needed to reproduce the problem.
- State the Home Assistant OS version, Studio Code Server add-on version,
  hardware architecture, and whether this was an initial install, restart,
  host reboot, or add-on update.

## Pull requests

1. Create a focused branch and keep unrelated changes out of the pull request.
2. Preserve the fail-closed behavior and the separation between the private
   runtime, persistent workspace, and Git repository.
3. Add or update tests for changed behavior.
4. Run:

   ```sh
   ./scripts/validate.sh
   ```

5. Explain the user-visible change, test evidence, and any migration impact.

By submitting a contribution, you agree that it may be distributed under the
repository's MIT License.

