                    self.assertNotIn('data-ref="/tmp/report.xlsx%22"', result["html"])
                    self.assertNotIn("data-ref=\"/tmp/report.xlsx'\"", result["html"])
                    expected_quote = "'" if case_name in ("quotedSingleSplit", "entityQuotedSingleEnd") else '"'
                    self.assertTrue(
                        result["text"].rstrip().endswith(f"{expected_quote}."),
                        result["text"],
                    )
