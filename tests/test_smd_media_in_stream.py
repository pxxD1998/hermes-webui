    """Drive the actual vendored smd parser through split MEDIA chunks."""

    @classmethod
    def setUpClass(cls):
        cls.cases = _run_real_smd_media_cases()

    def test_real_smd_parser_buffers_every_media_prefix_split(self):
        for split, modes in self.cases["prefixSplits"].items():
            for mode, result in modes.items():
                with self.subTest(split=split, mode=mode):
                    self.assertIn('class="media-node"', result["html"])
                    self.assertIn('data-ref="C:/tmp/live.png"', result["html"])
                    self.assertNotIn("MEDIA:", result["text"])

    def test_real_smd_parser_buffers_partial_ref_until_complete(self):
        for mode, result in self.cases["refSplit"].items():
            with self.subTest(mode=mode):
                self.assertIn('class="media-node"', result["html"])
                self.assertIn('data-ref="C:/tmp/live.png"', result["html"])
                self.assertNotIn("MEDIA:", result["text"])
                self.assertNotIn("C:/tmp/li", result["text"])

    def test_real_smd_parser_flushes_final_extensionless_url(self):
        for mode, result in self.cases["finalExtensionless"].items():
            with self.subTest(mode=mode):
                self.assertIn('class="media-node"', result["html"])
                self.assertIn('data-ref="https://fal.media/generated"', result["html"])
                self.assertNotIn("MEDIA:", result["text"])

    def test_real_smd_parser_live_pdf_placeholder_is_hydrated(self):
        for mode, result in self.cases["pdf"].items():
            with self.subTest(mode=mode):
                self.assertIn('class="pdf-preview-load"', result["html"])
                self.assertIn('data-path="C:/tmp/report.pdf"', result["html"])
                self.assertGreaterEqual(result["postProcessCalls"], 1)
                self.assertGreaterEqual(result["playbackCalls"], 1)

    def test_real_smd_parser_false_prefix_plain_prose_keeps_fade(self):
        result = self.cases["falsePrefix"]["fade"]
        self.assertEqual(result["text"], "Maybe plain prose ")
        self.assertEqual(result["fadeWords"], ["Maybe", "plain", "prose"])
        self.assertIn('class="stream-fade-word is-new"', result["html"])

    def test_real_smd_parser_refuses_cross_parent_tail_concat(self):
        for mode, result in self.cases["crossParent"].items():
            with self.subTest(mode=mode):
                self.assertEqual(result["liTexts"], ["ME", "ow"])
                if mode == "fade":
                    self.assertTrue(result["fadeWords"])
                    self.assertEqual("".join(result["fadeWords"]), "MEow")

    def test_real_smd_parser_keeps_suffixes_outside_media_refs(self):
        for case_name in ("bold", "boldSplit", "trailingPeriod", "trailingPeriodEnd"):
            for mode, result in self.cases["boundaries"][case_name].items():
                with self.subTest(case=case_name, mode=mode):
                    self.assertIn('data-ref="/tmp/report.xlsx"', result["html"])
                    self.assertNotIn('data-ref="/tmp/report.xlsx**"', result["html"])
                    self.assertNotIn('data-ref="/tmp/report.xlsx."', result["html"])

        for punctuation, modes in self.cases["punctuation"].items():
            for mode, result in modes.items():
                with self.subTest(punctuation=punctuation, mode=mode):
                    self.assertIn('data-ref="/tmp/report.xlsx"', result["html"])
                    self.assertIn(punctuation, result["text"])

    def test_real_smd_parser_preserves_unmatched_delimiter_in_ref(self):
        for mode, result in self.cases["boundaries"]["unmatchedDelimiter"].items():
            with self.subTest(mode=mode):
                self.assertIn('data-ref="/tmp/report.xlsx*"', result["html"])

    def test_real_smd_parser_detaches_balanced_quotes_in_safe_fade_split_and_tail_paths(self):
        for case_name in (
            "quotedDouble",
            "quotedSingleSplit",
            "entityQuotedDoubleSplit",
            "entityQuotedSingleEnd",
            "entityQuotedDoubleOpenerSplit",
        ):
            for mode, result in self.cases["boundaries"][case_name].items():
                with self.subTest(case=case_name, mode=mode):
                    self.assertIn('data-ref="/tmp/report.xlsx"', result["html"])
                    self.assertNotIn('data-ref="/tmp/report.xlsx%22"', result["html"])
                    self.assertNotIn("data-ref=\"/tmp/report.xlsx'\"", result["html"])
                    expected_quote = "'" if case_name in ("quotedSingleSplit", "entityQuotedSingleEnd") else '"'
                    self.assertTrue(
                        result["text"].rstrip().endswith(f"{expected_quote}."),
                        result["text"],
                    )

    def test_real_smd_parser_preserves_quoted_remote_query_and_fragment_values(self):
        expected = {
            "quotedRemoteQuery": "https://example.com/a.png?signature=value!",
            "quotedRemoteFragment": "https://example.com/a.png#preview!",
        }
        for case_name, ref in expected.items():
            for mode, result in self.cases["boundaries"][case_name].items():
                with self.subTest(case=case_name, mode=mode):
                    self.assertIn(f'data-ref="{ref}"', result["html"])
                    self.assertIn(".", result["text"])

    def test_real_smd_parser_preserves_remote_query_and_fragment_punctuation(self):
        for suffix_kind, punctuation_cases in self.cases["remoteSuffixPunctuation"].items():
            separator = "?signature=value" if suffix_kind == "query" else "#section"
            for punctuation, modes in punctuation_cases.items():
                expected = f"https://example.com/a.png{separator}{punctuation}"
                for mode, result in modes.items():
                    with self.subTest(
                        suffix_kind=suffix_kind,
                        punctuation=punctuation,
                        mode=mode,
                    ):
                        self.assertIn(f'data-ref="{expected}"', result["html"])

        wrapped_ref = "https://example.com/a.png?signature=value."
        for mode, result in self.cases["boundaries"]["wrappedRemoteQueryPunctuation"].items():
            with self.subTest(suffix_kind="wrapped_query", mode=mode):
                self.assertIn(f'data-ref="{wrapped_ref}"', result["html"])
                self.assertIn(".", result["text"])

    def test_real_smd_parser_preserves_other_requested_token_shapes(self):
        for mode, result in self.cases["boundaries"]["bareMarker"].items():
            with self.subTest(case="bareMarker", mode=mode):
                self.assertIn("MEDIA:", result["text"])
                self.assertNotIn('class="media-node"', result["html"])

        expected = {
            "queryFragment": "https://example.com/a.png?size=1#preview",
            "windowsPath": r"C:\Temp\report.xlsx",
        }
        for case_name, ref in expected.items():
            for mode, result in self.cases["boundaries"][case_name].items():
                with self.subTest(case=case_name, mode=mode):
                    self.assertIn(f'data-ref="{ref}"', result["html"])

        for mode, result in self.cases["boundaries"]["multiple"].items():
            with self.subTest(case="multiple", mode=mode):
                self.assertIn('data-ref="/tmp/one.png"', result["html"])
                self.assertIn('data-path="/tmp/two.pdf"', result["html"])
                self.assertIn("then", result["text"])
                self.assertIn("after", result["text"])


if __name__ == "__main__":
    import unittest
    unittest.main()
