# PingFlow TCP project context

## Why this project exists

Common network tools may report a low ICMP or TCP-handshake RTT while small
request-response exchanges inside an established TCP connection feel much
slower. PingFlow TCP provides a reproducible way to compare those two phases
without requiring a third-party runtime dependency.

The core question is:

> After a TCP connection is established, how long does one small request and
> its immediate response actually take?

PingFlow does not claim to measure raw packet loss. TCP hides loss from the
application by retransmitting, so an application-level long tail must be
correlated with TCP information or packet captures before attributing it to
loss.

## Product decisions

### Name and scope

- Public name: **PingFlow TCP**
- Repository: `lostornot/pingflow-tcp`
- Installed command: `pingflow`
- It is a latency and interaction diagnostic, not an ICMP ping replacement or
  bandwidth benchmark.
- It is complementary to iPerf3 and is not affiliated with the ESnet iPerf
  project.

### Address-family behavior

- IPv4 and IPv6 literals are detected automatically.
- Users do not need `-4` or `-6` for literal addresses.
- With a hostname, the system resolver's preferred result is used by default.
- `-4` and `-6` force hostname resolution to one family.
- `--both` compares available IPv4 and IPv6 results.

### Server behavior

- `pingflow -s` starts explicit listeners on `0.0.0.0:39001` and `[::]:39001`.
- The IPv6 socket is IPv6-only, avoiding platform-dependent dual-stack socket
  behavior and allowing both listeners to coexist.
- The server remains in the foreground and is designed for temporary
  diagnostic use.
- The foreground server handles `SIGHUP` explicitly so closing its SSH session
  stops the server and releases the listening port.
- Server startup uses an iPerf3-like ruled `Server listening` banner.

### Measurement model

- TCP connection RTT is sampled using repeated new connections.
- Established-flow RTT uses one persistent connection.
- Each measured exchange sends one fixed-size payload and waits for the full
  echo before sending the next.
- `-S/--size` is the primary single-payload option. `-l/--length` remains a
  compatibility alias, while `--sizes` runs multiple payload sizes.
- A payload size is the number of application bytes sent and echoed per
  exchange, not a guaranteed TCP segment or IP packet size.
- The default payload is 1300 bytes so the normal no-option client test uses
  the larger common packet size; 32 bytes remains available explicitly.
- Warm-up exchanges are excluded from reported statistics.
- The default enables `TCP_NODELAY`.
- Reports include min, median, p95, p99, max, slow-sample rate, failures, and
  the established-versus-connect median gap and ratio.

### Packaging and release

- The executable is a single Python file compatible with Python 3.8+.
- The installer downloads immutable GitHub Release assets and validates the
  program SHA-256 before installation.
- Passing `--run` to the installer downloads, validates, and runs PingFlow from
  a temporary directory without requiring installation or root privileges.
- A `v*` tag runs tests and publishes `pingflow`, `install.sh`, and
  `SHA256SUMS`.
- Continuous integration covers Linux and macOS with Python 3.8 and 3.12.

## Current milestone

Version `v0.1.2` includes:

- IPv4 and IPv6 literal auto-detection;
- simultaneous IPv4 and IPv6 listeners;
- Linux/macOS test matrix;
- latest-Release download URLs;
- SHA-256 validation;
- installation into a temporary directory and `pingflow --version`;
- VPS server and local client can each be downloaded, checksum-validated, and
  run with one command through `install.sh --run`;
- a default client payload of 1300 bytes instead of 32 bytes;
- an explicit `-S/--size` option for one application payload size while
  retaining `-l/--length` compatibility;
- Server mode exits cleanly on SSH hangup, reports occupied ports clearly, and
  prints an iPerf3-like listening banner.

## Possible next steps

- Add supported-platform `TCP_INFO` reporting for retransmission counters.
- Add machine-readable per-sample output for capture correlation.
- Consider a system service installer only if persistent server operation
  becomes a real use case.
- Add protocol compatibility tests before changing the on-wire version.

These are roadmap ideas, not commitments. Preserve the small, dependency-free
diagnostic core.
