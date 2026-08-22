    def test_real_smd_parser_detaches_balanced_quotes_in_safe_fade_split_and_tail_paths(self):
        for case_name in (
            "quotedDouble",
            "quotedSingleSplit",
            "entityQuotedDoubleSplit",
            "entityQuotedSingleEnd",
            "entityQuotedDoubleOpenerSplit",
        ):
            for mode, result in self.cases["boundaries"][case_name].items():
