import json
import os
import socket
import subprocess
import sys
import time
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PINGFLOW = os.path.join(PROJECT_ROOT, "pingflow")


def unused_port(family, host):
    sock = socket.socket(family, socket.SOCK_STREAM)
    try:
        sock.bind((host, 0))
        return sock.getsockname()[1]
    finally:
        sock.close()


def wait_for_port(family, host, port, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        sock = socket.socket(family, socket.SOCK_STREAM)
        sock.settimeout(0.1)
        try:
            sock.connect((host, port))
            return
        except OSError:
            time.sleep(0.05)
        finally:
            sock.close()
    raise RuntimeError("server did not start")


class ServerProcess:
    def __init__(self, family_flag, host, port):
        self.family_flag = family_flag
        self.host = host
        self.port = port
        self.process = None

    def __enter__(self):
        command = [
            sys.executable,
            PINGFLOW,
            "-s",
            self.family_flag,
            "-p",
            str(self.port),
        ]
        if self.family_flag == "--both":
            command.extend(["--bind4", "127.0.0.1", "--bind6", "::1"])
        else:
            bind_flag = "--bind6" if self.family_flag == "-6" else "--bind4"
            command.extend([bind_flag, self.host])
        self.process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            if self.family_flag == "--both":
                wait_for_port(socket.AF_INET, "127.0.0.1", self.port)
                wait_for_port(socket.AF_INET6, "::1", self.port)
            else:
                family = (
                    socket.AF_INET6 if self.family_flag == "-6" else socket.AF_INET
                )
                wait_for_port(family, self.host, self.port)
        except BaseException:
            self.stop()
            raise
        return self

    def stop(self):
        if self.process is None:
            return
        self.process.terminate()
        try:
            self.process.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.communicate(timeout=3)

    def __exit__(self, exc_type, exc, traceback):
        self.stop()


class PingFlowIntegrationTests(unittest.TestCase):
    def run_client(self, host, port, family_flag=None, expected_results=2):
        command = [
            sys.executable,
            PINGFLOW,
            "-c",
            host,
        ]
        if family_flag is not None:
            command.append(family_flag)
        command.extend(
            [
                "-p",
                str(port),
                "-n",
                "8",
                "--connect-count",
                "3",
                "--warmup",
                "1",
                "-i",
                "0",
                "--sizes",
                "32,1300",
                "-J",
            ]
        )
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        document = json.loads(completed.stdout)
        self.assertEqual(document["tool"], "pingflow")
        self.assertEqual(document["failures"], [])
        self.assertEqual(len(document["results"]), expected_results)
        for result in document["results"]:
            self.assertEqual(result["completed_samples"], 8)
            self.assertEqual(result["flow"]["timeouts"], 0)
            self.assertEqual(result["flow"]["errors"], 0)
            self.assertGreaterEqual(result["flow"]["persistent_connections"], 1)
            self.assertGreaterEqual(result["flow"]["rtt_ms"]["median"], 0)

    def test_ipv4_client_server(self):
        port = unused_port(socket.AF_INET, "127.0.0.1")
        with ServerProcess("-4", "127.0.0.1", port):
            self.run_client("127.0.0.1", port)

    @unittest.skipUnless(socket.has_ipv6, "IPv6 is unavailable")
    def test_ipv6_client_server(self):
        try:
            port = unused_port(socket.AF_INET6, "::1")
        except OSError:
            self.skipTest("IPv6 loopback is unavailable")
        with ServerProcess("-6", "::1", port):
            self.run_client("::1", port)

    @unittest.skipUnless(socket.has_ipv6, "IPv6 is unavailable")
    def test_dual_stack_server(self):
        try:
            port = unused_port(socket.AF_INET6, "::1")
        except OSError:
            self.skipTest("IPv6 loopback is unavailable")
        with ServerProcess("--both", "localhost", port):
            self.run_client("localhost", port, "--both", expected_results=4)

    def test_invalid_payload_length(self):
        completed = subprocess.run(
            [sys.executable, PINGFLOW, "-c", "127.0.0.1", "-l", "0"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("length must be between", completed.stderr)

    def test_version(self):
        completed = subprocess.run(
            [sys.executable, PINGFLOW, "--version"],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.stdout.strip(), "PingFlow 0.1.0")


if __name__ == "__main__":
    unittest.main()
