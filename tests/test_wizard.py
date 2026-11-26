import unittest

from spring_init.defaults import initial_request
from spring_init.errors import AbortedError, GoBack
from spring_init.wizard import STEPS, Wizard
from tests.support import load_metadata

BACK = object()
DEPS_LABEL = "Dependencies"
CONFIRM_LABEL = "Confirm"


class ScriptedPrompter:
    """Answers by label. A list of answers is consumed one per visit; BACK raises GoBack."""

    def __init__(self, answers=None, dependencies=None, confirm=True):
        self.answers = dict(answers or {})
        self.answers.setdefault(DEPS_LABEL, dependencies or [])
        self.answers.setdefault(CONFIRM_LABEL, confirm)
        self.asked: list[str] = []
        self.offered: dict[str, list[str]] = {}

    def _answer(self, label, default):
        self.asked.append(label)
        answer = self.answers.get(label, default)
        if isinstance(answer, tuple):
            answer, *rest = answer
            self.answers[label] = tuple(rest) if rest else default
        if answer is BACK:
            raise GoBack()
        return answer

    def choose(self, label, field, current):
        self.offered[label] = field.ids()
        return self._answer(label, current)

    def text(self, label, default):
        return self._answer(label, default)

    def dependencies(self, available, chosen):
        self.offered[DEPS_LABEL] = [dep.id for dep in available]
        return self._answer(DEPS_LABEL, chosen)

    def confirm(self, summary):
        return self._answer(CONFIRM_LABEL, True)


class WizardTest(unittest.TestCase):
    def setUp(self):
        self.metadata = load_metadata()

    def _run(self, prompter, overrides=None):
        overrides = overrides or {}
        request = initial_request(self.metadata, overrides)
        wizard = Wizard(prompter, self.metadata, lambda current: "summary")
        return wizard.run(request, fixed=set(overrides))

    def test_asks_every_web_form_option_in_order(self):
        prompter = ScriptedPrompter()
        self._run(prompter)
        expected = [step.label for step in STEPS] + [DEPS_LABEL, CONFIRM_LABEL]
        self.assertEqual(prompter.asked, expected)

    def test_offers_only_full_project_types(self):
        prompter = ScriptedPrompter()
        self._run(prompter)
        self.assertIn("maven-project", prompter.offered["Project"])
        self.assertNotIn("maven-build", prompter.offered["Project"])

    def test_flags_are_not_asked_again(self):
        prompter = ScriptedPrompter()
        self._run(prompter, {"java_version": "21", "dependencies": ["web"]})
        self.assertNotIn("Java", prompter.asked)
        self.assertNotIn(DEPS_LABEL, prompter.asked)

    def test_new_artifact_updates_name_and_package_defaults(self):
        answers = {"Group": "io.acme", "Artifact": "order-service"}
        request = self._run(ScriptedPrompter(answers, ["web"]))
        self.assertEqual((request.name, request.package_name),
                         ("order-service", "io.acme.orderservice"))
        self.assertEqual(request.dependencies, ["web"])

    def test_dependencies_follow_chosen_boot_version(self):
        prompter = ScriptedPrompter({"Spring Boot": "4.2.0"})
        self._run(prompter)
        self.assertNotIn("legacy", prompter.offered[DEPS_LABEL])

    def test_back_reasks_previous_prompt_and_keeps_new_answer(self):
        answers = {"Group": ("io.first", "io.second"), "Artifact": (BACK, "shop")}
        prompter = ScriptedPrompter(answers)
        request = self._run(prompter)
        self.assertEqual(prompter.asked[3:6], ["Group", "Artifact", "Group"])
        self.assertEqual(request.package_name, "io.second.shop")

    def test_back_on_first_prompt_stays_there(self):
        prompter = ScriptedPrompter({"Project": (BACK, "maven-project")})
        request = self._run(prompter)
        self.assertEqual(prompter.asked[:2], ["Project", "Project"])
        self.assertEqual(request.type, "maven-project")

    def test_back_skips_prompts_fixed_by_flags(self):
        prompter = ScriptedPrompter({DEPS_LABEL: (BACK, ["web"])})
        self._run(prompter, {"java_version": "21", "configuration_file_format": "yaml"})
        self.assertEqual(prompter.asked[-4:], [DEPS_LABEL, "Packaging", DEPS_LABEL, CONFIRM_LABEL])

    def test_back_from_confirmation_returns_to_dependencies(self):
        prompter = ScriptedPrompter({CONFIRM_LABEL: (BACK, True)}, ["web"])
        self._run(prompter)
        self.assertEqual(prompter.asked[-3:], [CONFIRM_LABEL, DEPS_LABEL, CONFIRM_LABEL])

    def test_back_from_dependencies_keeps_marked_ones(self):
        class KeepingPrompter(ScriptedPrompter):
            visits = 0

            def dependencies(self, available, chosen):
                self.visits += 1
                self.asked.append(DEPS_LABEL)
                if self.visits == 1:
                    raise GoBack(["web"])
                self.offered["chosen"] = chosen
                return chosen

        prompter = KeepingPrompter()
        request = self._run(prompter)
        self.assertEqual(prompter.offered["chosen"], ["web"])
        self.assertEqual(request.dependencies, ["web"])

    def test_declined_confirmation_aborts(self):
        with self.assertRaises(AbortedError):
            self._run(ScriptedPrompter(confirm=False))


if __name__ == "__main__":
    unittest.main()
