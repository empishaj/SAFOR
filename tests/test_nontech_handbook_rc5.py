import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class NonTechHandbookRc5Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        cls.text = (ROOT / "START-HIER.md").read_text(encoding="utf-8")

    def test_handbook_is_short_and_stepwise(self):
        words = re.findall(r"\\b[\\wÄÖÜäöüß-]+\\b", self.text, flags=re.UNICODE)
        self.assertLessEqual(len(words), 650)
        numbered = [line for line in self.text.splitlines() if re.match(r"^## \\d+\\.", line)]
        self.assertEqual(7, len(numbered))
        self.assertIn("## Kurzfassung", self.text)

    def test_handbook_avoids_internal_jargon(self):
        for term in (
            "identityRevision", "dispatchRevision", "blobSha", "schemaVersion",
            "compare-and-swap", "providerReadback", "chatBindingId", "sessionId",
            "predicate", "digest",
        ):
            with self.subTest(term=term):
                self.assertNotIn(term.lower(), self.text.lower())

    def test_handbook_sentence_length_is_nontechnical(self):
        prose = "\\n".join(
            line for line in self.text.splitlines()
            if line.strip()
            and not line.startswith("#")
            and not line.startswith("|")
            and not line.startswith("```")
            and not line.startswith("-")
            and not re.match(r"^\\d+\\.", line.strip())
        )
        sentences = [s.strip() for s in re.split(r"[.!?]+", prose) if s.strip()]
        counts = [len(re.findall(r"\\b[\\wÄÖÜäöüß-]+\\b", s, flags=re.UNICODE)) for s in sentences]
        self.assertTrue(counts)
        self.assertLessEqual(sum(counts) / len(counts), 15)
        self.assertLessEqual(max(counts), 32)

    def test_handbook_gives_exact_file_choices(self):
        for filename in (
            "SAFOR-FRAMEWORK-WEBSITE.json",
            "SAFOR-FRAMEWORK-SAAS.json",
            "SAFOR-TEST-ACCESS-SAAS.json",
            "SAFOR-FRAMEWORK-BOOK-CREATION.json",
            "SAFOR-TEST-ACCESS-BOOK-CREATION.json",
        ):
            with self.subTest(filename=filename):
                self.assertIn(filename, self.text)

    def test_handbook_explains_master_and_agent_handoff(self):
        self.assertIn("Der **MASTER** ist dein Hauptchat", self.text)
        self.assertIn("Hilfs-Chat, einen sogenannten Subagenten", self.text)
        self.assertIn(
            "MASTER schreibt den Job in die INBOX. Du schreibst nur GO. Der Agent holt den Job selbst ab.",
            self.text,
        )
        self.assertIn("Du musst den Job nicht zwischen Chats kopieren.", self.text)

    def test_handbook_uses_current_version(self):
        self.assertIn(self.version, self.text)


if __name__ == "__main__":
    unittest.main()
