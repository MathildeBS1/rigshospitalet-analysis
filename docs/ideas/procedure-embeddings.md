# Procedure Text Embeddings

Embed `procedure_text_id` and/or `diagnosis_code_text` (Danish free text) with a multilingual sentence model to capture complexity signal not already in specialty/diagnosis_group.

**Why:** Two procedures in the same specialty can differ wildly in complexity (e.g. brain tumour vs. routine biopsy both under neurosurgery). The text name may carry that signal.

**Use:** Add embeddings as a feature block in the prep time regression and test whether they improve it over structured features alone. If yes, use them as the basis for clustering.
