import os
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MUSCHEL = ROOT / "pakete" / "anschnur-muschel" / "muschel"


def run_muschel(input_text, env_path=None):
    env = os.environ.copy()
    if env_path is not None:
        env["PATH"] = env_path
    return subprocess.run(
        ["/bin/bash", str(MUSCHEL)],
        input=input_text,
        text=True,
        capture_output=True,
        env=env,
        cwd=ROOT,
        check=False,
    )


class MuschelTests(unittest.TestCase):
    def test_blocked_existing_command_reports_it_exists(self):
        result = run_muschel("git\n")

        self.assertEqual(result.returncode, 0)
        self.assertIn("nicht erlaubt", result.stdout)
        self.assertIn("git", result.stdout)
        self.assertIn("ist im System vorhanden", result.stdout)
        self.assertIn("dienstlich noch nicht freigegeben", result.stdout)

    def test_blocked_missing_command_reports_it_does_not_exist(self):
        result = run_muschel("gibtesnicht\n", env_path="/definitiv/nicht/vorhanden")

        self.assertEqual(result.returncode, 0)
        self.assertIn("nicht erlaubt", result.stdout)
        self.assertIn("gibtesnicht", result.stdout)
        self.assertIn("konnte im System nicht festgestellt werden", result.stdout)

    def test_allowed_help_command_lists_allowed_commands(self):
        result = run_muschel("hilfe\n")

        self.assertEqual(result.returncode, 0)
        self.assertIn("Zugelassene Amtsbefehle", result.stdout)
        self.assertIn("hilfe", result.stdout)
        self.assertIn("verlassen", result.stdout)
        self.assertNotIn("abmelden", result.stdout)
        self.assertNotIn("ende", result.stdout)

    def test_removed_exit_aliases_are_blocked(self):
        result = run_muschel("abmelden\nende\n")

        self.assertEqual(result.returncode, 0)
        self.assertIn('Befehl "abmelden" ist nicht erlaubt', result.stdout)
        self.assertIn('Befehl "ende" ist nicht erlaubt', result.stdout)

    def test_exit_command_terminates_successfully(self):
        result = run_muschel("verlassen\n")

        self.assertEqual(result.returncode, 0)
        self.assertIn("Muschel wird ordnungsgemäß geschlossen", result.stdout)


if __name__ == "__main__":
    unittest.main()
