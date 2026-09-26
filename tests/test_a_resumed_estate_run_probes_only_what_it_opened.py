"""
Spec T22 §3 and §4 (27 September 2026): a resumed estate run probes only what it opened, and a malformed request is a
finding, not a traceback. From the estate harness's `--from S5` of 26 September (report `aer360-harness-2026-09-26-215034.md`):
S11 built the viewer's answers probe from the --dry printer's placeholder, `/v1/onboarding/interviews/<policy interview>/answers`,
http.client refused the URL — `InvalidURL: URL can't contain control characters` — and, `http.client.InvalidURL` being an
`HTTPException` and not one of the kinds `urllib_transport` caught, the traceback lost every later station. Each test here
was red on main.

The doubles are the existing injection points: the estate double (tests/test_aer360_double.py) behind a transport that
writes down every `request.full_url` before it answers, and `urllib_transport` itself with `urlopen` standing in for http.client.
"""
import http.client
import os
import re
import sys
import tempfile
import unittest
import unittest.mock
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import aer360_harness as H  # noqa: E402
import aer360_passkey as PK  # noqa: E402
from tests.test_aer360_double import EstateDouble, runner_on  # noqa: E402

PLACEHOLDER_PATH = "/v1/onboarding/interviews/<policy interview>/answers"
# http.client's own sentence for the path the resumed run of 26 September sent (http/client.py, _validate_path)
INVALID_URL_SAID = "URL can't contain control characters. %r (found at least ' ')" % PLACEHOLDER_PATH


class RecordingTransport:
    """The estate double behind a transport that writes down every request's full URL before the double answers it."""

    def __init__(self, double):
        self.double = double
        self.urls = []

    def __call__(self, request):
        self.urls.append(request.full_url)
        return self.double(request)


class HttpClientRefusesOneRoad:
    """
    The estate double for every road but one. On that road the request goes to `urllib_transport` itself, with `urlopen`
    standing in for http.client as it answered the resumed run of 26 September — `InvalidURL`, its sentence verbatim — so the
    exception is the one the live run met, raised where the live run met it, on a road S11 walks first.
    """

    def __init__(self, double, method, path):
        self.double = double
        self.road = (method, path)
        self.refused = []

    def __call__(self, request):
        if (request.get_method(), urllib.parse.urlparse(request.full_url).path) == self.road:
            self.refused.append(request.full_url)

            def as_http_client_did(req, timeout=None):
                raise http.client.InvalidURL(INVALID_URL_SAID)
            with unittest.mock.patch.object(urllib.request, "urlopen", as_http_client_did):
                return H.urllib_transport(request)
        return self.double(request)


@unittest.skipUnless(PK.openssl_available(), "the Mac's /usr/bin/openssl is not on this machine")
class AResumedRunProbesOnlyWhatItOpened(unittest.TestCase):
    """One full run first, so the passkeys are stored and the estate holds a charter; then runs resumed at S11, as `--from` resumes them."""

    @classmethod
    def setUpClass(cls):
        cls.double = EstateDouble()
        cls.tmp = tempfile.mkdtemp()
        first = runner_on(cls.double, cls.tmp, invite=cls.double.mint_founder_link())
        cls.first = {o.station: o for o in first.run()}

    def resumed(self, transport):
        said = []
        runner = H.Runner(self.double.base, os.path.join(self.tmp, "store"), None, False, "S11", os.path.join(self.tmp, "out"),
                          transport=transport, say=said.append, sleep=lambda s: None)
        return runner, said

    def test_the_first_run_made_every_probe(self):
        self.assertEqual(self.first["S11"].line, "the attacker: 17 probe(s), 0 not made, 1 finding(s)")
        self.assertEqual(self.first["S11"].outcome, H.FAIL, "the wrong-checksum probe is accepted by the estate, as it is by the double")

    def test_a_run_resumed_at_s11_builds_no_path_from_the_placeholder_and_names_the_probes_it_could_not_make(self):
        transport = RecordingTransport(self.double)
        runner, said = self.resumed(transport)
        outcomes = {o.station: o for o in runner.run()}
        self.assertEqual(runner.facts["interview"], {}, "S3 did not run in this run, so it holds no policy interview id")
        # no path was built from the placeholder: not one URL carries an angle bracket, and none the placeholder's words
        for url in transport.urls:
            self.assertNotIn("<", url, url)
            self.assertNotIn("policy interview", url, url)
        # the viewer's answers probe was not sent (the answers roads S11 did walk are the founder's own probe drafts, by their ids)
        self.assertFalse(any(str(s.get("probe", "")).startswith("a viewer's session at an author route: POST /v1/onboarding/interviews/") for s in runner.evidence["S11"]))
        self.assertTrue(all("/v1/onboarding/interviews/iv-" in c.route for c in runner.calls if c.station == "S11" and "/answers" in c.route), "every answers road walked names an id the estate handed back")
        line = outcomes["S11"].line
        self.assertRegex(line, r"^the attacker: \d+ probe\(s\), \d+ not made, \d+ finding\(s\)$")
        self.assertIn("not made", line)
        found = len([f for f in runner.findings if f.station == "S11"])
        self.assertTrue(line.endswith("%d finding(s)" % found))
        self.assertEqual(outcomes["S11"].outcome, H.PASS if found == 0 else H.FAIL, "pass on zero findings, with the not-made count in the words")
        # the probes this run could not make, each counted and named: the viewer's answers road among them, with the printer's spelling in the note only
        not_made = int(re.search(r"(\d+) not made", line).group(1))
        notes = runner.notes["S11"]
        self.assertIn("probe not made (a viewer's session at an author route: POST %s): no policy interview id in this run" % PLACEHOLDER_PATH, notes)
        self.assertIn("probe not made: no policy interview id in this run", notes)
        self.assertIn("probe not made (a second confirm of an already confirmed interview (the policy interview)): no policy interview id in this run", notes)
        self.assertEqual(not_made, len([n for n in notes if "not made" in n]), "every probe not made is counted, and only those")
        self.assertEqual(line, "the attacker: 17 probe(s), %d not made, %d finding(s)" % (not_made, found))
        self.assertGreaterEqual(not_made, 3)
        # the run went on to the end
        self.assertEqual(outcomes["S12"].outcome, H.PASS, outcomes["S12"].line)
        self.assertIn("S14", outcomes)
        self.assertNotIn("Traceback", "\n".join(said))

    def test_a_request_http_client_refuses_to_send_is_a_recorded_failure_in_its_words_and_the_run_goes_on(self):
        transport = HttpClientRefusesOneRoad(self.double, "POST", "/v1/workspace/display-currency")  # S11's first probe road
        runner, said = self.resumed(transport)
        outcomes = {o.station: o for o in runner.run()}  # on main: http.client.InvalidURL escaped here, and S12 and S14 were lost
        self.assertEqual(len(transport.refused), 1)
        s11 = outcomes["S11"]
        self.assertEqual(s11.outcome, H.FAIL)
        self.assertEqual(s11.line, "the attacker: the estate could not be reached, so nothing was judged: POST %s/v1/workspace/display-currency could not be reached: %s"
                         % (self.double.base, INVALID_URL_SAID))
        self.assertTrue(any(line.startswith("S11 — fail — the attacker: the estate could not be reached, so nothing was judged: ") for line in said))
        self.assertEqual(outcomes["S12"].outcome, H.PASS, outcomes["S12"].line)
        self.assertNotEqual(outcomes["S14"].outcome, H.NOT_RUN)
        self.assertEqual(len(outcomes), len(H.STATION_IDS), "every station has an outcome")
        self.assertNotIn("Traceback", "\n".join(said))
        self.assertTrue(any(line.startswith("S14 — ") for line in said))
        # the report carries the failure as a station's line, the transport's words in it
        report = runner.write_report()
        with open(report, encoding="utf-8") as handle:
            text = handle.read()
        self.assertIn(INVALID_URL_SAID, text)


class TheTransportTellsHttpClientsRefusalInItsOwnWords(unittest.TestCase):
    def request(self, path=PLACEHOLDER_PATH):
        return urllib.request.Request("https://estate.test" + path, data=b"{}", method="POST", headers={"Content-Type": "application/json"})

    def test_an_invalid_url_is_the_transports_failure_with_http_clients_sentence_the_method_and_the_url(self):
        def as_http_client_does(req, timeout=None):
            raise http.client.InvalidURL(INVALID_URL_SAID)
        with unittest.mock.patch.object(urllib.request, "urlopen", as_http_client_does):
            with self.assertRaises(H.Unreachable) as raised:
                H.urllib_transport(self.request())
        self.assertEqual(str(raised.exception), "POST https://estate.test%s could not be reached: %s" % (PLACEHOLDER_PATH, INVALID_URL_SAID))

    def test_every_http_exception_is_caught_and_the_kinds_caught_before_still_are(self):
        for err in (http.client.BadStatusLine("HTTP/1.1 "), http.client.IncompleteRead(b""), http.client.LineTooLong("status line"),
                    http.client.RemoteDisconnected("Remote end closed connection without response"),
                    urllib.error.URLError("[Errno 8] nodename nor servname provided, or not known"), ConnectionRefusedError(61, "Connection refused"),
                    TimeoutError("timed out")):
            def raises(req, timeout=None, err=err):
                raise err
            with unittest.mock.patch.object(urllib.request, "urlopen", raises):
                with self.assertRaises(H.Unreachable, msg=repr(err)) as raised:
                    H.urllib_transport(self.request("/v1/journey"))
            self.assertTrue(str(raised.exception).startswith("POST https://estate.test/v1/journey could not be reached: "), str(raised.exception))
            self.assertIn(str(getattr(err, "reason", err)), str(raised.exception))

    def test_an_http_error_is_still_an_answer_and_not_a_failure(self):
        def answers_404(req, timeout=None):
            raise urllib.error.HTTPError(req.full_url, 404, "Not Found", {"Content-Type": "application/json"}, None)
        with unittest.mock.patch.object(urllib.request, "urlopen", answers_404):
            status, headers, text = H.urllib_transport(self.request("/v1/nowhere"))
        self.assertEqual((status, text), (404, ""))

    def test_the_dry_printer_keeps_its_spelling(self):
        lines = H.dry_lines()
        self.assertTrue(any("POST %s" % PLACEHOLDER_PATH in line for line in lines), "the placeholder is the printer's spelling of a road it does not walk")


if __name__ == "__main__":
    unittest.main()
