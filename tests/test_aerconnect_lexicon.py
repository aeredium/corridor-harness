"""
THE LEXICON, MIRRORED (Spec H-PATHFINDER, AAOI OP2 and AT3): the harness carries the connector's error dictionary by
mirroring it, and a test holds the copy to the connector's `packages/shared/src/errors.ts`, read in a fresh clone of
aeredium/aer-connector — named by AER_CONNECTOR_CLONE, else the sibling folder `../aer-connector`.

Until errors.ts is merged the mirror is PENDING WITH A RECORDED REASON (aerconnect_harness.LEXICON_PENDING_REASON, said in
the skip). From the day the file exists in the clone the test reads it, FAILS ON ANY DRIFT and never skips: a name in one
and not the other, or one description that differs, is a failure that names it. Once the harness records the commit it
mirrored (LEXICON_MIRRORED_AT), a clone that cannot be read is a failure too, so the read can never quietly fail.

The reader of errors.ts is proved here against shapes the file may land in (tests/fixtures/aerconnect-errors-shapes.ts) and
against the harness's own copy written out as TypeScript, so the first read of the real file is not its first test.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import aerconnect_harness as P  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLONE_ENV = "AER_CONNECTOR_CLONE"
SHAPES = os.path.join(ROOT, "tests", "fixtures", "aerconnect-errors-shapes.ts")
# The words the spec names, each to be in the harness's copy (Spec H-PATHFINDER, "One error lexicon, mirrored").
SPEC_WORDS = ("invalid_credential", "group_not_assigned", "legacy_limit_zero", "PolicyDenied", "agent_pact_not_composed",
              "DUPLICATE_UNACKNOWLEDGED", "insufficient_gas", "ROLE_NOT_GRANTED", "NOT_AUTHENTICATED")
# The GP1 prefixes as the gateway's own list states them (api_bis3 cmd/api-gateway/refusal_prefix.go, refusalPrefixes, 345be29).
GATEWAY_PREFIXES = ("PolicyDenied", "PolicyHeld", "Held", "SigningFailed", "PolicyEnvelopeRefused", "PolicyEvaluationFailed",
                    "PermissionDenied", "Unauthenticated", "Replayed", "RateLimitExceeded", "KeyNotHomed", "PolicyDeniedOnResume",
                    "HeldConsumeFailed", "KeyTypeRefused", "PolicyAuthorizationFailed", "MultisigRequired", "PolicyMisconfigured",
                    "RESOURCE_EXHAUSTED")


def candidates():
    out = []
    if os.environ.get(CLONE_ENV):
        out.append(os.path.abspath(os.path.expanduser(os.environ[CLONE_ENV])))
    out.append(os.path.join(os.path.dirname(ROOT), "aer-connector"))
    return out


def find_clone():
    """The first candidate that is a checkout of the connector: it carries packages/shared/src."""
    for path in candidates():
        if os.path.isdir(os.path.join(path, "packages", "shared", "src")):
            return path
    return None


def head_of(path):
    try:
        done = subprocess.run(["git", "-C", path, "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True)
        return done.stdout.strip() or "unknown"
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def read(path):
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def as_typescript_map(copy):
    """The harness's copy written as the plain map shape, each sentence broken across `+` where it is long."""
    lines = ["// written by the test from the harness's copy", "export const ERROR_DESCRIPTIONS = Object.freeze({"]
    for name, sentence in copy.items():
        escaped = sentence.replace("\\", "\\\\").replace("'", "\\'")
        if len(escaped) > 60:
            head, tail = escaped[:40], escaped[40:]
            lines.append("  '%s':\n    '%s' +\n    '%s'," % (name, head, tail))
        else:
            lines.append("  %s: '%s'," % (name, escaped))
    lines.append("});")
    return "\n".join(lines) + "\n"


def as_typescript_objects(copy):
    lines = ["export const ERROR_DICTIONARY: Readonly<Record<string, ErrorEntry>> = {"]
    for name, sentence in copy.items():
        lines.append('  "%s": { status: 400, description: "%s", owner: "x" },' % (name, sentence.replace("\\", "\\\\").replace('"', '\\"')))
    lines.append("};")
    return "\n".join(lines) + "\n"


class TheMirror(unittest.TestCase):
    def test_the_harness_mirrors_errors_ts_or_records_why_it_is_pending(self):
        """Pending with the recorded reason while errors.ts is not in the clone; a hard failure on any drift once it is; never a silent skip."""
        clone = find_clone()
        errors_ts = os.path.join(clone, *P.LEXICON_SOURCE.split("/")) if clone else None
        if errors_ts and os.path.exists(errors_ts):
            theirs = P.lexicon_of_typescript(read(errors_ts))
            self.assertTrue(theirs, "%s exists in the clone at %s (HEAD %s), and the harness read no entry from it: the reader "
                                    "(aerconnect_harness.lexicon_of_typescript) must be taught its shape; this is never a skip" % (
                                        P.LEXICON_SOURCE, clone, head_of(clone)))
            drift = P.lexicon_drift(theirs)
            self.assertEqual(drift, [], "the harness's lexicon has drifted from %s in the clone at %s (HEAD %s):\n  %s" % (
                P.LEXICON_SOURCE, clone, head_of(clone), "\n  ".join(drift)))
            self.assertIsNone(P.LEXICON_PENDING_REASON, "%s has landed (clone at %s, HEAD %s) and the harness still records its mirror as pending: "
                                                        "clear LEXICON_PENDING_REASON and set LEXICON_MIRRORED_AT to the commit" % (P.LEXICON_SOURCE, clone, head_of(clone)))
            self.assertTrue(P.LEXICON_MIRRORED_AT, "the copy matches %s; record the commit it was mirrored from in LEXICON_MIRRORED_AT" % P.LEXICON_SOURCE)
            return
        where = ("read in the clone at %s (HEAD %s), which carries no %s" % (clone, head_of(clone), P.LEXICON_SOURCE) if clone else
                 "no aer-connector clone was found to read (looked at %s; name a fresh one with %s)" % (", ".join(candidates()), CLONE_ENV))
        if P.LEXICON_MIRRORED_AT:
            self.fail("the harness says its lexicon is mirrored from %s at %s, and the mirror could not be held to it: %s" % (
                P.LEXICON_SOURCE, P.LEXICON_MIRRORED_AT, where))
        self.skipTest("%s — %s" % (P.LEXICON_PENDING_REASON, where))

    def test_the_pending_state_is_recorded_and_consistent(self):
        """While pending the reason is recorded and names the file and the commit read; once mirrored, the reason is gone and the commit stands."""
        if P.LEXICON_MIRRORED_AT is None:
            self.assertIsInstance(P.LEXICON_PENDING_REASON, str)
            self.assertTrue(P.LEXICON_PENDING_REASON.startswith("pending: "))
            self.assertIn(P.LEXICON_SOURCE, P.LEXICON_PENDING_REASON)
            self.assertIn("9e20d6c", P.LEXICON_PENDING_REASON)
            self.assertIn("fails on any drift and never skips", P.LEXICON_PENDING_REASON)
        else:
            self.assertIsNone(P.LEXICON_PENDING_REASON)


class TheMirrorNeverSkipsOnceTheFileExists(unittest.TestCase):
    """The mirror test above, run against a clone made here, so each of its roads is proved and the hard failure cannot rot into a skip."""

    def run_mirror(self, errors_ts=None, mirrored_at=None):
        tmp = tempfile.mkdtemp()
        os.makedirs(os.path.join(tmp, "packages", "shared", "src"))
        if errors_ts is not None:
            with open(os.path.join(tmp, *P.LEXICON_SOURCE.split("/")), "w", encoding="utf-8") as handle:
                handle.write(errors_ts)
        saved = (os.environ.get(CLONE_ENV), P.LEXICON_MIRRORED_AT, P.LEXICON_PENDING_REASON)
        os.environ[CLONE_ENV] = tmp
        if mirrored_at:
            P.LEXICON_MIRRORED_AT, P.LEXICON_PENDING_REASON = mirrored_at, None
        try:
            result = unittest.TestResult()
            TheMirror("test_the_harness_mirrors_errors_ts_or_records_why_it_is_pending").run(result)
        finally:
            if saved[0] is None:
                os.environ.pop(CLONE_ENV, None)
            else:
                os.environ[CLONE_ENV] = saved[0]
            P.LEXICON_MIRRORED_AT, P.LEXICON_PENDING_REASON = saved[1], saved[2]
            shutil.rmtree(tmp, ignore_errors=True)
        return result

    def test_a_dictionary_that_drifts_fails_naming_the_entry(self):
        copy = P.lexicon_copy()
        copy["group_not_assigned"] = "a sentence the harness does not carry"
        result = self.run_mirror(as_typescript_map(copy))
        self.assertEqual((len(result.failures), len(result.skipped)), (1, 0))
        self.assertIn("group_not_assigned reads 'a sentence the harness does not carry'", result.failures[0][1])

    def test_a_dictionary_the_reader_cannot_read_fails(self):
        result = self.run_mirror("export const NOTHING_HERE = 1;\n")
        self.assertEqual((len(result.failures), len(result.skipped)), (1, 0))
        self.assertIn("the harness read no entry from it", result.failures[0][1])

    def test_a_dictionary_that_matches_still_fails_while_the_harness_says_pending(self):
        result = self.run_mirror(as_typescript_map(P.lexicon_copy()))
        self.assertEqual((len(result.failures), len(result.skipped)), (1, 0))
        self.assertIn("still records its mirror as pending", result.failures[0][1])

    def test_a_dictionary_that_matches_passes_once_the_mirror_is_recorded(self):
        result = self.run_mirror(as_typescript_map(P.lexicon_copy()), mirrored_at="0123abc")
        self.assertTrue(result.wasSuccessful())
        self.assertEqual((len(result.failures), len(result.errors), len(result.skipped)), (0, 0, 0))

    def test_a_clone_without_the_file_is_pending_with_the_recorded_reason(self):
        result = self.run_mirror(None)
        self.assertEqual(len(result.skipped), 1)
        self.assertIn(P.LEXICON_PENDING_REASON, result.skipped[0][1])
        self.assertIn("which carries no %s" % P.LEXICON_SOURCE, result.skipped[0][1])

    def test_once_mirrored_a_clone_without_the_file_fails(self):
        result = self.run_mirror(None, mirrored_at="0123abc")
        self.assertEqual((len(result.failures), len(result.skipped)), (1, 0))
        self.assertIn("could not be held to it", result.failures[0][1])


class TheCopy(unittest.TestCase):
    def test_it_names_every_word_the_spec_names(self):
        for word in SPEC_WORDS:
            self.assertIn(word, P.LEXICON, word)

    def test_the_platforms_word_is_invalid_credential_not_unknown_credential(self):
        self.assertIn("invalid_credential", P.LEXICON)
        self.assertNotIn("unknown_credential", P.LEXICON)
        self.assertIn("the platform's own word, not unknown_credential", P.LEXICON["invalid_credential"]["source"])

    def test_it_carries_the_gateways_whole_list_of_gp1_prefixes(self):
        self.assertEqual(P.GP1_PREFIXES, GATEWAY_PREFIXES)
        for prefix in GATEWAY_PREFIXES:
            self.assertIn(prefix, P.LEXICON, prefix)
            self.assertEqual(P.LEXICON[prefix]["owner"], "the gateway")

    def test_every_entry_is_one_line_with_its_owner_and_its_source(self):
        for name, entry in P.LEXICON.items():
            self.assertTrue(entry["description"].strip(), name)
            self.assertNotIn("\n", entry["description"], name)
            self.assertTrue(entry["owner"], name)
            self.assertTrue(entry["source"], name)
        self.assertEqual(P.lexicon_copy(), {name: entry["description"] for name, entry in P.LEXICON.items()})

    def test_the_descriptions_are_the_owners_own_sentences(self):
        """Read from the services' own source, word for word where the source states the sentence whole."""
        self.assertEqual(P.LEXICON["invalid_credential"]["description"],
                         "the credential presented is not a credential this platform knows: no active credential matched it, so nothing was "
                         "judged; the answer is the same on retry")  # aegiskey-access-platform authenticateDenialSentence
        self.assertEqual(P.LEXICON["NOT_AUTHENTICATED"]["description"], "You are not signed in. Sign in with your passkey and try again.")
        self.assertEqual(P.LEXICON["DUPLICATE_UNACKNOWLEDGED"]["description"],
                         "This looks like a payment that has already been made recently. Confirm it is intentional to continue.")
        self.assertEqual(P.LEXICON["RESOURCE_EXHAUSTED"]["description"], "On the stream road: the orchestrator pipeline is saturated.")
        # AERAccounts refusals.ts writes the apostrophe curly, and the copy is held to it character for character
        self.assertEqual(P.LEXICON["ROLE_NOT_GRANTED"]["description"], "Your credential does not carry this permission. Permissions come from "
                                                                       "your organisation’s policy, not from this application.")
        self.assertEqual(P.LEXICON["legacy_limit_zero"]["description"], "<policy>'s <limit> limit has not been set to more than zero. Set it to a "
                                                                        "figure above zero for the payment to be approved.")
        self.assertTrue(P.LEXICON["insufficient_gas"]["description"].startswith("Your gas account holds <available>. This <payment or trade> needs at most"))


class TheReader(unittest.TestCase):
    def test_it_reads_the_shapes_the_dictionary_may_land_in_and_leaves_the_rest_alone(self):
        found = P.lexicon_of_typescript(read(SHAPES))
        self.assertEqual(found, {
            "group_not_assigned": "the signing group is not assigned to the account",
            "PolicyDenied": "A refusal of policy, the same on retry.",
            "RESOURCE_EXHAUSTED": "On the stream road: the orchestrator pipeline is saturated.",
            "invalid_credential": "the credential presented is not a credential this platform knows: no active credential matched it",
            "NOT_AUTHENTICATED": "You are not signed in.",
        })
        self.assertNotIn("Held", found, "an interpolated template is no sentence, and a list is no entry")

    def test_the_harnesss_copy_written_as_typescript_reads_back_whole_in_both_shapes(self):
        copy = P.lexicon_copy()
        self.assertEqual(P.lexicon_of_typescript(as_typescript_map(copy)), copy)
        self.assertEqual(P.lexicon_of_typescript(as_typescript_objects(copy)), copy)
        self.assertEqual(P.lexicon_drift(P.lexicon_of_typescript(as_typescript_map(copy))), [])

    def test_it_reads_escapes_and_skips_comments_that_look_like_entries(self):
        text = ("// fake: 'not an entry'\n/* also: 'not' */\nexport const E = {\n  a: 'it\\'s \\\\ done', // trailing: 'no'\n"
                "  b: \"line\\ttab\",\n  c: `plain template`,\n};\n")
        self.assertEqual(P.lexicon_of_typescript(text), {"a": "it's \\ done", "b": "line\ttab", "c": "plain template"})


class TheDrift(unittest.TestCase):
    def test_one_description_that_differs_is_named(self):
        theirs = P.lexicon_copy()
        theirs["group_not_assigned"] = "a different sentence"
        drift = P.lexicon_drift(theirs)
        self.assertEqual(len(drift), 1)
        self.assertTrue(drift[0].startswith("group_not_assigned reads 'a different sentence' in %s" % P.LEXICON_SOURCE))

    def test_a_name_missing_from_either_side_is_named(self):
        theirs = P.lexicon_copy()
        del theirs["Replayed"]
        theirs["not_authorized"] = "the platform's collapsed word"
        drift = P.lexicon_drift(theirs)
        self.assertIn("Replayed is in the harness's copy and not in %s" % P.LEXICON_SOURCE, drift)
        self.assertIn("not_authorized is in %s and not in the harness's copy" % P.LEXICON_SOURCE, drift)
        self.assertEqual(len(drift), 2)

    def test_the_same_dictionary_is_no_drift(self):
        self.assertEqual(P.lexicon_drift(P.lexicon_copy()), [])


class TheNaming(unittest.TestCase):
    def test_the_servers_sentence_comes_first_then_the_dictionarys_description(self):
        sentence = ("PolicyDenied: denied (cause: legacy_limit_zero; the per-payment limit has not been set to more than zero. Set it to a figure "
                    "above zero for the payment to be approved.)")
        said = P.named(sentence)
        self.assertTrue(said.startswith(sentence + " ["), said)
        self.assertIn("PolicyDenied: %s" % P.LEXICON["PolicyDenied"]["description"], said)
        self.assertIn("legacy_limit_zero: %s" % P.LEXICON["legacy_limit_zero"]["description"], said)
        self.assertLess(said.index("PolicyDenied: A refusal"), said.index("legacy_limit_zero: "), "in the order they appear")

    def test_an_unrecognised_cause_is_quoted_verbatim_and_marked_unclassified(self):
        self.assertEqual(P.named("the venue's quote moved"), "the venue's quote moved [unclassified]")

    def test_a_refusal_code_names_its_entry(self):
        said = P.named("NOT_AUTHENTICATED (401): You are not signed in. Sign in with your passkey and try again.", "NOT_AUTHENTICATED")
        self.assertIn("[NOT_AUTHENTICATED: You are not signed in.", said)

    def test_a_prefix_is_matched_whole_and_never_inside_a_longer_word(self):
        self.assertEqual(P.lexicon_names_in("PolicyHeld: the platform could not record the hold"), ["PolicyHeld"])
        self.assertEqual(P.lexicon_names_in("PolicyDeniedOnResume: the cluster refused"), ["PolicyDeniedOnResume"])
        self.assertEqual(P.lexicon_names_in("MCP Police REFUSED this call. It said: “PermissionDenied: not_authorized”"), ["PermissionDenied"])
        self.assertEqual(P.lexicon_names_in("a held request"), [])
        self.assertEqual(P.lexicon_names_in("deny_cause group_not_assigned_x"), [], "a cause word is matched whole")


if __name__ == "__main__":
    unittest.main()
