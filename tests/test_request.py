import unittest

from spring_init.defaults import initial_request
from spring_init.errors import ValidationError
from spring_init.naming import package_name
from spring_init.request import action_path, is_project_archive, validate
from tests.support import load_metadata


class PackageNameTest(unittest.TestCase):
    def test_matches_web_form(self):
        self.assertEqual(package_name("com.example", "demo-app"), "com.example.demoapp")

    def test_drops_invalid_chars_and_lowercases(self):
        self.assertEqual(package_name("Com.Acme", "My App!"), "com.acme.myapp")

    def test_segment_starting_with_digit_is_prefixed(self):
        self.assertEqual(package_name("com.acme", "3d-viewer"), "com.acme._3dviewer")


class DefaultsTest(unittest.TestCase):
    def setUp(self):
        self.metadata = load_metadata()

    def test_service_defaults_are_used(self):
        request = initial_request(self.metadata, {})
        self.assertEqual(request.type, self.metadata.selects["type"].default)
        self.assertEqual((request.name, request.package_name), ("demo", "com.example.demo"))

    def test_overrides_flow_into_derived_fields(self):
        request = initial_request(self.metadata, {"group_id": "io.x", "artifact_id": "shop"})
        self.assertEqual((request.name, request.package_name), ("shop", "io.x.shop"))

    def test_explicit_package_is_kept(self):
        request = initial_request(self.metadata, {"artifact_id": "shop", "package_name": "a.b"})
        self.assertEqual(request.package_name, "a.b")


class ValidateTest(unittest.TestCase):
    def setUp(self):
        self.metadata = load_metadata()

    def _request(self, **overrides):
        return initial_request(self.metadata, overrides)

    def test_valid_request_passes(self):
        validate(self._request(dependencies=["web", "data-jpa"]), self.metadata)

    def test_unknown_select_value_fails(self):
        with self.assertRaisesRegex(ValidationError, "javaVersion"):
            validate(self._request(java_version="8"), self.metadata)

    def test_unknown_dependency_fails(self):
        with self.assertRaisesRegex(ValidationError, "nope"):
            validate(self._request(dependencies=["nope"]), self.metadata)

    def test_incompatible_dependency_fails(self):
        with self.assertRaisesRegex(ValidationError, "legacy"):
            validate(self._request(dependencies=["legacy"]), self.metadata)

    def test_incompatible_dependency_is_not_offered(self):
        ids = [d.id for d in self.metadata.dependencies_for("4.2.0")]
        self.assertNotIn("legacy", ids)
        self.assertIn("modulith", ids)

    def test_params_omit_empty_text_and_join_dependencies(self):
        params = self._request(description="", dependencies=["web", "lombok"]).to_params("")
        self.assertNotIn("description", params)
        self.assertEqual(params["dependencies"], "web,lombok")
        self.assertEqual(params["baseDir"], "")

    def test_build_only_types_are_not_archives(self):
        pom = self._request(type="maven-build")
        self.assertFalse(is_project_archive(pom, self.metadata))
        self.assertEqual(action_path(pom, self.metadata), "/pom.xml")
        self.assertTrue(is_project_archive(self._request(type="maven-project"), self.metadata))


if __name__ == "__main__":
    unittest.main()
