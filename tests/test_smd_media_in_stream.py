    def test_real_smd_parser_detaches_balanced_quotes_in_safe_fade_split_and_tail_paths(self):
        expected_quote_by_case = {
            "quotedDouble": '"',
            "quotedSingleSplit": "'",
            "entityQuotedDoubleSplit": '"',
            "entityQuotedSingleEnd": "'",
            "entityQuotedDoubleOpenerSplit": '"',
        }
        for case_name, expected_quote in expected_quote_by_case.items():
            for mode, result in self.cases["boundaries"][case_name].items():
                with self.subTest(case=case_name, mode=mode):
                    self.assertIn('data-ref="/tmp/report.xlsx"', result["html"])
                    self.assertNotIn('data-ref="/tmp/report.xlsx%22"', result["html"])
                    self.assertNotIn("data-ref=\"/tmp/report.xlsx'\"", result["html"])
                    self.assertTrue(
                        result["text"].rstrip().endswith(f"{expected_quote}."),
                        result["text"],
                    )
