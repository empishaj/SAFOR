import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class WorkspaceInitializationV014Tests(unittest.TestCase):
    def load(self, path):
        return json.loads((ROOT / path).read_text(encoding="utf-8"))

    def test_workspace_branches_are_mutually_exclusive(self):
        model = self.load("v0.14.0/initialization-model.json")
        contract = model["workspaceBranchContract"]
        self.assertEqual("PROJECT_WORKSPACE_TYPE", contract["discriminator"])
        self.assertTrue(contract["mutuallyExclusive"])
        self.assertTrue(contract["REMOTE_GIT"]["remoteMemoryRequired"])
        self.assertFalse(contract["LOCAL_GIT"]["remoteMemoryRequired"])
        self.assertEqual(".safor/", contract["LOCAL_GIT"]["controlWorkspace"])

    def test_master_has_no_unscoped_remote_memory_instruction(self):
        master = self.load("v0.14.0/SAFOR-MASTER.json")
        behaviors = master["humanCommunication"]["requiredBehavior"]
        unscoped = [
            text for text in behaviors
            if "safor-memory" in text.lower()
            and "REMOTE_GIT" not in text
            and "LOCAL_GIT" not in text
        ]
        self.assertEqual([], unscoped)

    def test_interaction_messages_are_workspace_scoped(self):
        model = self.load("v0.14.0/interaction-model.json")
        patterns = model["humanCommunication"]["messagePatterns"]
        self.assertEqual(
            "PROJECT_WORKSPACE_TYPE == REMOTE_GIT",
            patterns["safMemoryStop"]["appliesWhen"],
        )
        self.assertEqual(
            "PROJECT_WORKSPACE_TYPE == LOCAL_GIT",
            patterns["localControlWorkspaceStop"]["appliesWhen"],
        )

if __name__ == "__main__":
    unittest.main()
