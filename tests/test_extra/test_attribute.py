"""Test attribute selectors."""
import soupsieve as sv
from .. import util
import os
import subprocess
import sys
import textwrap

# Compile the selector read from `stdin` and exit successfully only if it fails with a syntax error.
COMPILE_SCRIPT = textwrap.dedent(
    """
    import sys
    import soupsieve as sv
    try:
        sv.compile(sys.stdin.read())
    except sv.SelectorSyntaxError:
        sys.exit(0)
    sys.exit('SelectorSyntaxError was not raised')
    """
)


class TestAttribute(util.TestCase):
    """Test attribute selectors."""

    MARKUP = """
    <div id="div">
    <p id="0">Some text <span id="1"> in a paragraph</span>.</p>
    <a id="2" href="http://google.com">Link</a>
    <span id="3">Direct child</span>
    <pre id="pre">
    <span id="4">Child 1</span>
    <span id="5">Child 2</span>
    <span id="6">Child 3</span>
    </pre>
    </div>
    """

    def test_attribute_not_equal_no_quotes(self):
        """Test attribute with value that does not equal specified value (no quotes)."""

        # No quotes
        self.assert_selector(
            self.MARKUP,
            'body [id!=\\35]',
            ["div", "0", "1", "2", "3", "pre", "4", "6"],
            flags=util.HTML5
        )

    def test_attribute_not_equal_quotes(self):
        """Test attribute with value that does not equal specified value (quotes)."""

        # Quotes
        self.assert_selector(
            self.MARKUP,
            "body [id!='5']",
            ["div", "0", "1", "2", "3", "pre", "4", "6"],
            flags=util.HTML5
        )

    def test_attribute_not_equal_double_quotes(self):
        """Test attribute with value that does not equal specified value (double quotes)."""

        # Double quotes
        self.assert_selector(
            self.MARKUP,
            'body [id!="5"]',
            ["div", "0", "1", "2", "3", "pre", "4", "6"],
            flags=util.HTML5
        )

    def assert_syntax_error_not_timeout(self, pattern, timeout=10):
        """
        Assert that the pattern fails for a syntax error, not timeout error.

        The pattern is first compiled in a separate process that is killed if it
        exceeds the timeout, so catastrophic backtracking cannot hang the test run.
        This works on all platforms, unlike `signal.alarm`, which is not available on Windows.
        """

        # Run from the directory `soupsieve` was imported from so the child tests the same code.
        cwd = os.path.dirname(os.path.dirname(os.path.abspath(sv.__file__)))

        passed = False
        try:
            result = subprocess.run(
                [sys.executable, '-c', COMPILE_SCRIPT],
                input=pattern,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                cwd=cwd,
                timeout=timeout
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            passed = True
        except subprocess.TimeoutExpired:
            pass
        self.assertTrue(passed, 'Compiling the pattern timed out after {} seconds'.format(timeout))

        # Now that it is known to fail quickly, verify the syntax error in this process as well.
        with self.assertRaises(sv.SelectorSyntaxError):
            sv.compile(pattern)

    def test_bad_attribute_unclused(self):
        """Test bad attribute fails for syntax error, not timeout error."""

        self.assert_syntax_error_not_timeout('[a="' + ('x' * 300))

    def test_bad_attribute_unclosed_single_quote(self):
        """Test bad attribute with an unclosed single quoted value fails for syntax error, not timeout error."""

        self.assert_syntax_error_not_timeout("[a='" + ('x' * 300))

    def test_bad_contains_unclosed(self):
        """Test bad `:-soup-contains()` with an unclosed quoted value fails for syntax error, not timeout error."""

        self.assert_syntax_error_not_timeout(':-soup-contains("' + ('x' * 300))
        self.assert_syntax_error_not_timeout(":-soup-contains('" + ('x' * 300))

    def test_bad_lang_unclosed(self):
        """Test bad `:lang()` with an unclosed quoted value fails for syntax error, not timeout error."""

        self.assert_syntax_error_not_timeout(':lang("' + ('x' * 300))
        self.assert_syntax_error_not_timeout(":lang('" + ('x' * 300))

    def test_long_quoted_attribute_value(self):
        """Test that long, properly closed quoted attribute values, including escapes, still match."""

        markup = '<div><p id="1" title="{0}"></p><p id="2" title="{0}&quot;{0}"></p></div>'.format('x' * 300)

        self.assert_selector(markup, 'p[title="' + ('x' * 300) + '"]', ['1'], flags=util.HTML)
        self.assert_selector(markup, "p[title='" + ('x' * 300) + "']", ['1'], flags=util.HTML)
        self.assert_selector(
            markup,
            'p[title="' + ('x' * 300) + '\\"' + ('x' * 300) + '"]',
            ['2'],
            flags=util.HTML
        )
