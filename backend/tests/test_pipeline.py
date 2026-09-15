from app.pipeline import run_full_pipeline


def test_valid_program_all_phases_succeed():
    result = run_full_pipeline(
        """
        int inc(int a) { return a + 1; }
        void main() {
          int x = 0;
          while (x < 3) {
            x = inc(x);
          }
        }
        """
    )
    assert all(result[phase]["success"] for phase in ["lex", "parse", "semantic", "tac", "optimize"])


def test_semantic_error_keeps_partial_results():
    result = run_full_pipeline("void main() { int x = true; }")
    assert result["lex"]["success"]
    assert result["parse"]["success"]
    assert not result["semantic"]["success"]
    assert result["tac"]["data"] is None
    assert result["optimize"]["data"] is None
