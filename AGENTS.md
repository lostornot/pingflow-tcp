# AGENTS.md

## Project goal

PingFlow TCP measures request-response RTT inside one persistent TCP
connection and compares it with repeated TCP connection RTT. It is intended to
reveal cases where TCP handshakes look fast but established-flow interaction is
slow or has a long tail.

## Current status

- Public repository: `lostornot/pingflow-tcp`
- Command: `pingflow`
- Current release: `v0.1.0`
- Implementation: one executable Python file using only the standard library
- Supported runtime: Python 3.8 or newer on Linux and macOS

## Run and test

- Start the dual-stack server: `./pingflow -s`
- Test an IPv4 or IPv6 literal: `./pingflow -c ADDRESS`
- Test both common payload sizes: `./pingflow -c ADDRESS --sizes 32,1300`
- Run all tests: `python3 -m unittest discover -s tests -v`
- Check the installer syntax: `sh -n install.sh`

Integration tests open local TCP sockets. If an execution sandbox blocks local
listeners, rerun the same tests with local socket permission rather than
treating the failure as a code defect.

## Directory guide

- `pingflow`: client, server, protocol, statistics, and CLI
- `install.sh`: latest/tagged GitHub Release installer with SHA-256 validation
- `tests/`: unit and dual-stack integration tests
- `.github/workflows/test.yml`: Linux/macOS test matrix
- `.github/workflows/release.yml`: tagged Release asset generation
- `docs/PROJECT_CONTEXT.md`: durable product decisions and roadmap

## Project-specific rules

- A literal IPv4 or IPv6 address must work without `-4` or `-6`.
- Keep `-4` and `-6` only for forcing a family when resolving a hostname.
- `--both` is for comparing available A and AAAA results.
- The default server must use explicit IPv4 and IPv6 listeners on port 39001.
- Keep IPv6 `IPV6_V6ONLY` enabled so both listeners can coexist reliably.
- Measure one request at a time on one persistent connection; do not turn the
  default measurement into a throughput or parallel-load test.
- Keep TCP connect RTT and established request-response RTT separate.
- Preserve Python-standard-library-only operation unless the user explicitly
  approves a dependency.
- Treat PingFlow as complementary to iPerf3, not affiliated with it.

## Safety and privacy

- Never commit tokens, credentials, cookies, private keys, real user IP
  addresses, packet captures, or machine-specific absolute paths.
- The server has no authentication or encryption. Documentation must recommend
  temporary firewall access and cleanup after testing.
- Keep the protocol payload limit and validate untrusted lengths before
  allocating or echoing data.
- Do not rewrite published Git history or replace Release assets without
  explicit approval.

## Known pitfalls

- ICMP, TCP connect timing, and established-flow request-response RTT are
  different measurements.
- A long-tail RTT sample alone does not prove packet loss; TCP retransmission
  counters or packet captures are needed.
- Large traceroute probes are not equivalent to data exchanged inside an
  established TCP flow.
- Do not require square brackets around an IPv6 command-line host; brackets are
  URL syntax.
- Release assets must remain named `pingflow`, `install.sh`, and
  `SHA256SUMS`, because the latest-download installer depends on those names.

## Delivery checklist

- Local test suite passes with IPv4 and IPv6 loopback where available.
- GitHub Actions passes on Linux and macOS for the supported Python matrix.
- CLI help, README examples, installer URLs, and version output agree.
- Release assets download successfully and match `SHA256SUMS`.
- No secrets, real test addresses, private paths, or unrelated files are
  included.
- README and `docs/PROJECT_CONTEXT.md` are updated when behavior changes.
