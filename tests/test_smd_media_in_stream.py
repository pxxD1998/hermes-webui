        "  wrappedRemoteQueryPunctuation:renderModes(['**MEDIA:https://example.com/a.png?signature=value.**. ']),\n"
        "  quotedDouble:renderModes(['\\\"MEDIA:/tmp/report.xlsx\\\". ']),\n"
        "  quotedSingleSplit:renderModes([\\\"'MEDIA:/tmp/report.\\\", \\\"xlsx'.\\\"]),\n"
        "  entityQuotedDoubleSplit:renderModes(['&quot;', 'MEDIA:/tmp/report.xlsx&quot;. ']),\n"
        "  entityQuotedSingleEnd:renderModes(['&#39;MEDIA:/tmp/report.xlsx&#39;.']),\n"
        "  entityQuotedDoubleOpenerSplit:renderModes(['&quo', 't;MEDIA:/tmp/report.xlsx&quot;. ']),\n"
        "  quotedRemoteQuery:renderModes(['\\\"MEDIA:https://example.com/a.png?signature=value!\\\". ']),\n"
        "  quotedRemoteFragment:renderModes(['\\\"MEDIA:https://example.com/a.png#preview!\\\". ']),\n"

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
                    self.assertIn(".", result["text"])

    def test_real_smd_parser_preserves_quoted_remote_query_and_fragment_values(self):
