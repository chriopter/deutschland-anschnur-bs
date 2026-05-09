import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MUSCHEL = ROOT / "pakete" / "anschnur-muschel" / "muschel"
HAPSMANN = ROOT / "pakete" / "anschnur-muschel" / "hapsmann"


def run_muschel(input_text, env_path=None, extra_env=None):
    env = os.environ.copy()
    if env_path is not None:
        env["PATH"] = env_path
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        ["/bin/bash", str(MUSCHEL)],
        input=input_text,
        text=True,
        capture_output=True,
        env=env,
        cwd=ROOT,
        check=False,
    )


def run_hapsmann(*args, pacman_path=None):
    env = os.environ.copy()
    if pacman_path is not None:
        env["PACMAN_BEFEHL"] = str(pacman_path)
    return subprocess.run(
        ["/bin/bash", str(HAPSMANN), *args],
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
        self.assertIn("hapsmann", result.stdout)
        self.assertIn("verzeichnis", result.stdout)
        self.assertIn("datei", result.stdout)
        self.assertIn("netz", result.stdout)
        self.assertIn("dienst", result.stdout)
        self.assertIn("system", result.stdout)
        self.assertIn("verlassen", result.stdout)
        self.assertNotIn("abmelden", result.stdout)
        self.assertNotRegex(result.stdout, r"(?m)^  ende\\b")

    def test_removed_exit_aliases_are_blocked(self):
        result = run_muschel("abmelden\nende\n")

        self.assertEqual(result.returncode, 0)
        self.assertIn('Befehl "abmelden" ist nicht erlaubt', result.stdout)
        self.assertIn('Befehl "ende" ist nicht erlaubt', result.stdout)

    def test_exit_command_terminates_successfully(self):
        result = run_muschel("verlassen\n")

        self.assertEqual(result.returncode, 0)
        self.assertIn("Muschel wird ordnungsgemäß geschlossen", result.stdout)

    def test_hapsmann_translates_update_inside_muschel(self):
        with tempfile.TemporaryDirectory() as directory:
            fake_pacman = Path(directory) / "pacman"
            fake_pacman.write_text("#!/bin/sh\nprintf '%s\\n' \"$*\"\n")
            fake_pacman.chmod(0o755)

            result = run_muschel(
                "hapsmann erneuern\n",
                extra_env={"PACMAN_BEFEHL": str(fake_pacman)},
            )

        self.assertEqual(result.returncode, 0)
        self.assertIn("-Syu", result.stdout)

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

    def test_system_identity_command_reads_os_release(self):
        result = run_muschel("system kennung\n")

        self.assertEqual(result.returncode, 0)
        self.assertIn("NAME=", result.stdout)


class HapsmannTests(unittest.TestCase):
    def test_translates_package_operations(self):
        with tempfile.TemporaryDirectory() as directory:
            fake_pacman = Path(directory) / "pacman"
            fake_pacman.write_text("#!/bin/sh\nprintf '%s\\n' \"$*\"\n")
            fake_pacman.chmod(0o755)

            cases = {
                ("erneuern",): "-Syu",
                ("suchen", "muschel"): "-Ss muschel",
                ("zeigen", "anschnur-muschel"): "-Qi anschnur-muschel",
                ("fernzeigen", "anschnur-muschel"): "-Si anschnur-muschel",
                ("installieren", "anschnur-muschel"): "-S anschnur-muschel",
                ("entfernen", "vim"): "-Rns vim",
                ("bestand",): "-Q",
                ("aufraeumen",): "-Sc",
            }

            for eingabe, erwartung in cases.items():
                with self.subTest(eingabe=eingabe):
                    result = run_hapsmann(*eingabe, pacman_path=fake_pacman)
                    self.assertEqual(result.returncode, 0)
                    self.assertEqual(result.stdout.strip(), erwartung)

    def test_rejects_unknown_hapsmann_operation(self):
        result = run_hapsmann("vollzerstoerung")

        self.assertEqual(result.returncode, 2)
        self.assertIn("nicht zugelassen", result.stderr)


if __name__ == "__main__":
    unittest.main()
