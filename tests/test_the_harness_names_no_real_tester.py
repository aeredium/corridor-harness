"""
The harness names no real tester (Spec T5, 16 September 2026). The run file the harness seeds
on first use holds one tester entry, named `example`, and a readme that says to replace it; the
refusal for a --tester the run file does not name names the file and never the testers it holds;
and no file this public repository carries names either of the two testers the harness used to
seed. Those two names are written here in rot13, so that this test does not carry them either.
"""
import codecs
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import corridor_harness as h  # noqa: E402
import series as S  # noqa: E402
import tables as T  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE = os.path.join("tests", "fixtures", "series-1.2.md")

# The two names the harness used to seed, rot13 so this file does not carry them (Spec T5 §5).
REAL_NAMES = tuple(codecs.decode(word, "rot13") for word in ("rvgna", "ivpgbe"))

THE_REFUSAL = ("The run file at %s names no tester called %s. Add an entry for %s under `testers`; "
               "the entry named `example` shows the fields.")
THE_README_SENTENCE = "Replace `example` with your own tester name and complete each field. Add one entry per tester."
THE_README_PARAGRAPH = ("The run file is yours and stays on your machine; it names your testers and is never committed. "
                       "Never commit it, and never name a real tester in a public place.")


def tracked_files():
    """Every file the repository carries, as git lists them; a checkout without git is walked instead."""
    try:
        listed = subprocess.run(["git", "-C", ROOT, "ls-files", "-z"], check=True, capture_output=True).stdout
        return sorted(part.decode("utf-8") for part in listed.split(b"\0") if part)
    except (OSError, subprocess.CalledProcessError):
        paths = []
        for folder, dirs, files in os.walk(ROOT):
            dirs[:] = [d for d in dirs if d not in (".git", "__pycache__")]
            paths.extend(os.path.relpath(os.path.join(folder, name), ROOT) for name in files)
        return sorted(paths)


def names_in(text):
    lowered = text.lower()
    return [name for name in REAL_NAMES if name in lowered]


def read(path, mode="r"):
    with open(os.path.join(ROOT, path), mode, **({} if "b" in mode else {"encoding": "utf-8"})) as handle:
        return handle.read()


def main_says(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = h.main(argv)
    return code, out.getvalue()


def a_run_file_naming(testers):
    run_file = h.default_run_file()
    run_file["testers"] = {
        name: {"agents": {"trader": "%s-trader" % name, "payer": "%s-payer" % name, "payer_nogas": None},
               "listed_address": "", "payer_list_scope": "agent"}
        for name in testers
    }
    return run_file


class SeededRunFileTest(unittest.TestCase):
    """Spec T5 §1: the seeded run file names nobody."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.path = os.path.join(self.tmp, "store", "harness_run.json")

    def test_a_fresh_first_run_writes_a_run_file_whose_only_tester_is_example(self):
        said = []
        h.load_run_file(self.path, said.append)
        self.assertTrue(os.path.exists(self.path), "the run file is written on first use")
        self.assertEqual(len(said), 1)
        self.assertIn("Wrote %s" % self.path, said[0])
        text = read(self.path)
        written = json.loads(text)
        self.assertEqual(list(written["testers"]), ["example"], "the seeded run file names nobody but example")
        self.assertIn("_readme", written, "JSON has no comments, so the readme is a key")
        self.assertIn(THE_README_SENTENCE, written["_readme"])
        self.assertTrue(text.lstrip().startswith('{\n  "_readme"'), "the readme opens the file")

    def test_the_example_entry_holds_a_placeholder_in_every_field(self):
        example = h.default_run_file()["testers"]["example"]
        self.assertEqual(set(example), {"agents", "listed_address", "payer_list_scope"})
        self.assertEqual(example["agents"], {"trader": "example-trader", "payer": "example-payer", "payer_nogas": None})
        self.assertEqual(example["payer_list_scope"], "agent")
        # An address-shaped placeholder would be a destination the harness could send to. Empty,
        # the harness refuses to invent one, in its own sentence.
        self.assertEqual(example["listed_address"], "")

    def test_the_harness_writes_no_real_name_and_no_pinned_address_as_anybodys(self):
        self.assertEqual(names_in(json.dumps(h.default_run_file())), [])
        testers = json.dumps(h.default_run_file()["testers"]).lower()
        for key, row in T.PINNED.items():
            self.assertNotIn(row.address.lower(), testers, "the seeded run file names %s's address as a tester's" % key)

    def test_a_first_run_from_the_command_line_seeds_the_file_then_refuses_an_unknown_tester(self):
        code, out = main_says(["--tester", "bastian", "--run-file", self.path])
        self.assertEqual(code, 2)
        self.assertIn("Wrote %s for you to complete" % self.path, out)
        self.assertIn(THE_REFUSAL % (self.path, "bastian", "bastian"), out)
        self.assertEqual(list(json.loads(read(self.path))["testers"]), ["example"])


class UnknownTesterRefusalTest(unittest.TestCase):
    """Spec T5 §2: the refusal names the file, not the people."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.path = os.path.join(self.tmp, "harness_run.json")
        with open(self.path, "w", encoding="utf-8") as handle:
            json.dump(a_run_file_naming(["alice", "bob"]), handle, indent=2)
        self.before = read(self.path, "rb")

    def test_bastian_is_refused_in_the_new_sentence_and_the_testers_are_not_named(self):
        code, out = main_says(["--tester", "bastian", "--run-file", self.path])
        self.assertEqual(code, 2)
        self.assertEqual(out.strip(), THE_REFUSAL % (self.path, "bastian", "bastian"), "the refusal is the whole of what is printed")
        self.assertNotIn("alice", out)
        self.assertNotIn("bob", out)
        self.assertNotIn("the testers are", out)

    def test_the_sentence_is_the_harnesss_own(self):
        self.assertEqual(h.unknown_tester_sentence(self.path, "bastian"), THE_REFUSAL % (self.path, "bastian", "bastian"))

    def test_the_run_file_is_left_as_it_was(self):
        main_says(["--tester", "bastian", "--run-file", self.path])
        self.assertEqual(read(self.path, "rb"), self.before)


class NoRealTesterInTheRepositoryTest(unittest.TestCase):
    """Spec T5 §3, §4, §5: the repository tells nobody who tests for AEREDIUM."""

    def test_no_file_in_the_repository_names_a_real_tester(self):
        carriers = {}
        for path in tracked_files():
            found = names_in(path) + names_in(read(path, "rb").decode("utf-8", "replace"))
            if found:
                carriers[path] = sorted(set(found))
        self.assertEqual(carriers, {}, "a file in the repository names a real tester (REAL_NAMES, rot13)")

    def test_the_series_names_its_two_testers_by_role(self):
        """The Series document's own words: version 1.2 of 17 September 2026 took Spec T5's wording into the document
        itself, so the fixture carries no amendment line for it (Spec T6); series.py speaks with the document."""
        document = read(FIXTURE)
        self.assertIn("Version 1.2 amends version 1.1 in wording only, so that the document names no tester", document)
        self.assertNotIn("**Amended 17 September 2026", document)
        self.assertIn("Two testers run the series independently, each with one Trader and one Payer", document)
        self.assertIn("(one tester's listed destination `%s`, and the other tester's equivalent)" % T.address("TESTER_LISTED"), S.BY_ID["B4"].text)
        self.assertIn("One owner's account page shows no agent of the other's, and Claude connected as that owner's Trader "
                      "cannot name the other owner's wallet.", S.BY_ID["H4"].text)

    def test_the_readme_uses_invented_names_and_says_the_run_file_stays_home(self):
        text = read("README.md")
        self.assertEqual(names_in(text), [])
        self.assertIn("--tester alice", text)
        self.assertIn("Consent link for alice-trader:", text)
        self.assertIn(THE_README_PARAGRAPH, text)
        run_file_section = text.split("## The run file", 1)[1].split("\n## ", 1)[0]
        self.assertIn(THE_README_PARAGRAPH, run_file_section, "the sentence is under the run-file section")

    def test_gitignore_covers_a_run_file_copied_into_the_checkout(self):
        lines = [line.strip() for line in read(".gitignore").splitlines() if line.strip() and not line.startswith("#")]
        for pattern in ("harness_run.json", "*-trader.json", "*-payer.json", "*-payer_nogas.json"):
            self.assertIn(pattern, lines)

    def test_git_itself_refuses_a_run_file_or_a_token_file_anywhere_in_the_checkout(self):
        def ignored(name):
            try:
                return subprocess.run(["git", "-C", ROOT, "check-ignore", "-q", name], capture_output=True).returncode == 0
            except OSError:
                self.skipTest("git is not on this machine")
        for name in ("harness_run.json", os.path.join("tests", "harness_run.json"), "alice-trader.json",
                     "bob-payer.json", "bob-payer_nogas.json", os.path.join("tests", "fixtures", "bob-trader.json")):
            self.assertTrue(ignored(name), "%s could be committed" % name)
        self.assertFalse(ignored(os.path.join("tests", "fixtures", "tools-list-slippage.json")), "the fixtures are still tracked")


if __name__ == "__main__":
    unittest.main()
