"""A test module whose public function must never become a skill candidate."""


def helper_that_should_be_excluded(x):
    """If this shows up in a generated skill, test-exclusion is broken."""
    return x
