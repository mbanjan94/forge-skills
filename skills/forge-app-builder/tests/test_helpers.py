import json
import unittest
from unittest.mock import MagicMock, patch

from scripts import create_forge_app as create
from scripts.forge_env import forge_env

DEV_SPACE_ID = "12345678-1234-1234-1234-123456789abc"


class TestForgeEnv(unittest.TestCase):
    def test_stamps_skill_name_and_preserves_base(self):
        env = forge_env(base={"PATH": "/bin"})
        self.assertEqual(env["PATH"], "/bin")
        self.assertEqual(env["ATL_FORGE_ATTRIBUTION_SKILL_NAME"], "forge-app-builder")

    def test_drops_invalid_extra_value(self):
        env = forge_env(extra={"RUN_ID": "contains spaces"}, base={})
        self.assertNotIn("ATL_FORGE_ATTRIBUTION_RUN_ID", env)

    def test_extra_cannot_override_skill_name(self):
        env = forge_env(extra={"SKILL_NAME": "other-skill"}, base={})
        self.assertEqual(env["ATL_FORGE_ATTRIBUTION_SKILL_NAME"], "forge-app-builder")


class TestCreateApp(unittest.TestCase):
    @patch("scripts.create_forge_app.subprocess.run")
    def test_dev_space_discovery(self, run):
        run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps([{"id": "space-1", "name": "One"}]),
            stderr="",
        )
        self.assertEqual(create.discover_dev_spaces(), [{"id": "space-1", "name": "One"}])

    @patch("scripts.create_forge_app.subprocess.run")
    @patch("scripts.create_forge_app.validate_prerequisites", return_value=True)
    def test_template_branch_uses_safe_argument_array_and_attribution(self, prereqs, run):
        run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        with patch("scripts.create_forge_app.Path.is_dir", return_value=True), patch(
            "scripts.create_forge_app.Path.exists", return_value=False
        ):
            result = create.create_app(
                "my-app",
                DEV_SPACE_ID,
                template="jira-issue-panel-ui-kit",
                output_dir="/tmp",
                accept_terms=True,
            )
        self.assertEqual(result.returncode, 0)
        command = run.call_args.args[0]
        self.assertEqual(command[0:2], ["forge", "create"])
        self.assertIn("jira-issue-panel-ui-kit", command)
        self.assertIn("--developer-space-id", command)
        self.assertEqual(command[command.index("--directory") + 1], "my-app")
        self.assertIn("--accept-terms", command)
        self.assertFalse(run.call_args.kwargs.get("shell", False))
        self.assertEqual(
            run.call_args.kwargs["env"]["ATL_FORGE_ATTRIBUTION_SKILL_NAME"],
            "forge-app-builder",
        )

    @patch("scripts.create_forge_app.subprocess.run")
    @patch("scripts.create_forge_app.validate_prerequisites", return_value=True)
    def test_blank_branch_uses_blank_template(self, prereqs, run):
        run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        with patch("scripts.create_forge_app.Path.is_dir", return_value=True), patch(
            "scripts.create_forge_app.Path.exists", return_value=False
        ):
            create.create_app(
                "my-app", DEV_SPACE_ID, blank=True, output_dir="/tmp", accept_terms=True
            )
        self.assertIn("blank", run.call_args.args[0])

    @patch("scripts.create_forge_app.subprocess.run")
    @patch("scripts.create_forge_app.validate_prerequisites", return_value=True)
    def test_explicit_directory_preserves_app_name(self, prereqs, run):
        run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        with patch("scripts.create_forge_app.Path.is_dir", return_value=True), patch(
            "scripts.create_forge_app.Path.exists", return_value=False
        ):
            create.create_app(
                "My App",
                DEV_SPACE_ID,
                blank=True,
                output_dir="/tmp",
                accept_terms=True,
            )
        command = run.call_args.args[0]
        self.assertEqual(command[command.index("--directory") + 1], "My App")

    @patch("scripts.create_forge_app.validate_prerequisites", return_value=True)
    def test_requires_exactly_one_scaffold_branch(self, prereqs):
        with self.assertRaisesRegex(RuntimeError, "exactly one"):
            create.create_app(
                "my-app", DEV_SPACE_ID, output_dir="/tmp", accept_terms=True
            )
        with self.assertRaisesRegex(RuntimeError, "exactly one"):
            create.create_app(
                "my-app",
                DEV_SPACE_ID,
                template="jira-issue-panel-ui-kit",
                blank=True,
                output_dir="/tmp",
                accept_terms=True,
            )

    @patch("scripts.create_forge_app.validate_prerequisites", return_value=True)
    def test_rejects_existing_target(self, prereqs):
        with patch("scripts.create_forge_app.Path.is_dir", return_value=True), patch(
            "scripts.create_forge_app.Path.exists", return_value=True
        ):
            with self.assertRaisesRegex(RuntimeError, "Target already exists"):
                create.create_app(
                    "my-app", DEV_SPACE_ID, blank=True, output_dir="/tmp", accept_terms=True
                )

    @patch("scripts.create_forge_app.validate_prerequisites", return_value=True)
    def test_requires_explicit_terms_authorization(self, prereqs):
        with self.assertRaisesRegex(RuntimeError, "Explicit authorization"):
            create.create_app("my-app", DEV_SPACE_ID, blank=True, output_dir="/tmp")

    @patch("scripts.create_forge_app.validate_prerequisites", return_value=True)
    def test_rejects_unsafe_app_names(self, prereqs):
        for app_name in ("", "../escape", "/absolute", "-option", " trailing "):
            with self.subTest(app_name=app_name):
                with self.assertRaises(RuntimeError):
                    create.create_app(
                        app_name,
                        DEV_SPACE_ID,
                        blank=True,
                        output_dir="/tmp",
                        accept_terms=True,
                    )

    @patch("scripts.create_forge_app.validate_prerequisites", return_value=True)
    def test_rejects_invalid_developer_space_id(self, prereqs):
        with self.assertRaisesRegex(RuntimeError, "must be a UUID"):
            create.create_app(
                "my-app",
                "space-1",
                blank=True,
                output_dir="/tmp",
                accept_terms=True,
            )

    @patch("scripts.create_forge_app.subprocess.run")
    def test_dev_space_discovery_rejects_scalar_json(self, run):
        run.return_value = MagicMock(returncode=0, stdout='"unexpected"', stderr="")
        with self.assertRaisesRegex(RuntimeError, "unexpected Developer Space schema"):
            create.discover_dev_spaces()


if __name__ == "__main__":
    unittest.main()
