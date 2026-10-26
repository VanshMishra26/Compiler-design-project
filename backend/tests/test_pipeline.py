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


def test_complex_uploaded_c_source_produces_later_phases():
    result = run_full_pipeline(
        """
        #include <stdio.h>
        int main(void) {
          int values[3] = {1, 2, 3};
          int i, sum = 0;
          for (i = 0; i < 3; i++) {
            sum += values[i];
          }
          printf("%d", sum);
          return 0;
        }
        """
    )

    assert all(result[phase]["success"] for phase in ["lex", "parse", "semantic", "tac", "optimize"])
    assert result["ast"]
    assert result["semantic"]["data"]["symbolTable"]
    assert result["tac"]["data"]["instructions"]


def test_typedef_style_identifier_types_are_parsed_in_function_body():
    result = run_full_pipeline(
        """
        int main(void) {
          size_t count = 3;
          return count;
        }
        """
    )

    assert result["parse"]["success"]
    assert result["semantic"]["success"]
