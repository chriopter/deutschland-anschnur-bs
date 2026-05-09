import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MUSCHEL = ROOT / "muschel"
PRUEFER = ROOT / "anschnur-pruefen"
BEFEHLE = ROOT / "befehle.d"


def run_muschel(input_text=None, *args, env_path=None, befehle=None):
    env = os.environ.copy()
    env["ANSCHNUR_BEFEHLE"] = str(befehle or BEFEHLE)
    if env_path is not None:
        env["PATH"] = env_path
    return subprocess.run(
        [sys.executable, str(MUSCHEL), *args],
        input=input_text,
        text=True,
        capture_output=True,
        env=env,
        cwd=ROOT,
        check=False,
    )


class MuschelTests(unittest.TestCase):
    def test_help_lists_catalog_commands(self):
        result = run_muschel("hilfe\n")

        self.assertEqual(result.returncode, 0)
        self.assertIn("Zugelassene Amtsbefehle", result.stdout)
        self.assertIn("verzeichnis liste", result.stdout)
        self.assertIn("hapsmann erneuern", result.stdout)
        self.assertIn("hafener zusammensetz hoch", result.stdout)

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

    def test_exit_command_terminates_successfully(self):
        result = run_muschel("verlassen\n")

        self.assertEqual(result.returncode, 0)
        self.assertIn("Muschel wird ordnungsgemäß geschlossen", result.stdout)

    def test_directory_commands_keep_changed_place(self):
        with tempfile.TemporaryDirectory() as directory:
            result = run_muschel(f"verzeichnis wechsel {directory}\nverzeichnis ort\n")

        self.assertEqual(result.returncode, 0)
        self.assertIn(directory, result.stdout)

    def test_file_commands_read_and_show_file(self):
        with tempfile.TemporaryDirectory() as directory:
            akte = Path(directory) / "akte.txt"
            akte.write_text("Amtsinhalt\n")
            result = run_muschel(f"datei lesen {akte}\ndatei zeigen {akte}\n")

        self.assertEqual(result.returncode, 0)
        self.assertIn("Amtsinhalt", result.stdout)
        self.assertIn("akte.txt", result.stdout)

    def test_longest_match_and_option_translation(self):
        with tempfile.TemporaryDirectory() as directory:
            befehle = Path(directory)
            (befehle / "test.jsonl").write_text(
                '{"befehl":["hafener","zusammensetz","hoch"],'
                '"typ":"exec","programm":"/bin/printf","argumente":["%s\\n","docker","compose","up"],'
                '"optionen":{"--dämonisiere":"--detach"},"rest":"anhaengen",'
                '"beschreibung":"test"}\n'
            )
            result = run_muschel(
                "hafener zusammensetz hoch --dämonisiere dienst\n",
                befehle=befehle,
            )

        self.assertEqual(result.returncode, 0)
        self.assertIn("docker", result.stdout)
        self.assertIn("compose", result.stdout)
        self.assertIn("up", result.stdout)
        self.assertIn("--detach", result.stdout)
        self.assertIn("dienst", result.stdout)

    def test_catalog_checker_accepts_repo_catalog(self):
        env = os.environ.copy()
        env["ANSCHNUR_BEFEHLE"] = str(BEFEHLE)
        result = subprocess.run(
            [str(PRUEFER)],
            text=True,
            capture_output=True,
            cwd=ROOT,
            env=env,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Befehlsakten in Ordnung", result.stdout)


if __name__ == "__main__":
    unittest.main()
