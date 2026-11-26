import unittest

from spring_init.defaults import initial_request
from spring_init.wizard import STEPS, Wizard
from tests.support import load_metadata


class ScriptedPrompter:
    """Answers prompts from a dict keyed by label; records what was asked."""

    def __init__(self, answers: dict[str, str], dependencies: list[str]):
        self.answers = answers
        self.picked = dependencies
        self.asked: list[str] = []
        self.choices_offered: dict[str, list[str]] = {}
        self.dependencies_offered: list[str] = []

    def choose(self, label, field, current):
        self.asked.append(label)
        self.choices_offered[label] = field.ids()
        return self.answers.get(label, current)

    def text(self, label, default):
        self.asked.append(label)
        return self.answers.get(label, default)

    def dependencies(self, available, chosen):
        self.dependencies_offered = [dep.id for dep in available]
        return self.picked


class WizardTest(unittest.TestCase):
    def setUp(self):
        self.metadata = load_metadata()

    def _run(self, prompter, overrides=None):
        overrides = overrides or {}
        request = initial_request(self.metadata, overrides)
        return Wizard(prompter, self.metadata).run(request, fixed=set(overrides))

    def test_asks_every_web_form_option_in_order(self):
        prompter = ScriptedPrompter({}, [])
        self._run(prompter)
        self.assertEqual(prompter.asked, [step.label for step in STEPS])

    def test_offers_only_full_project_types(self):
        prompter = ScriptedPrompter({}, [])
        self._run(prompter)
        offered = prompter.choices_offered["Project"]
        self.assertIn("maven-project", offered)
        self.assertNotIn("maven-build", offered)

    def test_flags_are_not_asked_again(self):
        prompter = ScriptedPrompter({}, [])
        self._run(prompter, {"java_version": "21", "dependencies": ["web"]})
        self.assertNotIn("Java", prompter.asked)
        self.assertEqual(prompter.dependencies_offered, [])

    def test_new_artifact_updates_name_and_package_defaults(self):
        answers = {"Group": "io.acme", "Artifact": "order-service"}
        request = self._run(ScriptedPrompter(answers, ["web"]))
        self.assertEqual(request.name, "order-service")
        self.assertEqual(request.package_name, "io.acme.orderservice")
        self.assertEqual(request.dependencies, ["web"])

    def test_dependencies_follow_chosen_boot_version(self):
        prompter = ScriptedPrompter({"Spring Boot": "4.2.0"}, [])
        self._run(prompter)
        self.assertNotIn("legacy", prompter.dependencies_offered)


if __name__ == "__main__":
    unittest.main()
