import nbformat
from app.notebook_processors import PlotlyPreprocessor


class TestPlotlyPreprocessor:
    def test_converts_plotly_output(self):

        cell = nbformat.from_dict(
            {
                "cell_type": "code",
                "source": "",
                "metadata": {},
                "outputs": [
                    {
                        "output_type": "display_data",
                        "metadata": {},
                        "data": {
                            "application/vnd.plotly.v1+json": {
                                "data": [],
                                "layout": {},
                            }
                        },
                    }
                ],
            }
        )

        preprocessor = PlotlyPreprocessor()
        result_cell, resources = preprocessor.preprocess_cell(cell, {}, 0)

        assert resources.get("needs_plotly") is True
        output = result_cell["outputs"][0]
        assert "text/html" in output["data"]
        html = output["data"]["text/html"]
        assert "Plotly.newPlot" in html
        assert "<div id=" in html

    def test_non_plotly_output_unchanged(self):

        cell = nbformat.from_dict(
            {
                "cell_type": "code",
                "source": "",
                "metadata": {},
                "outputs": [
                    {
                        "output_type": "stream",
                        "name": "stdout",
                        "text": "hello\n",
                    }
                ],
            }
        )

        preprocessor = PlotlyPreprocessor()
        result_cell, resources = preprocessor.preprocess_cell(cell, {}, 0)

        assert not resources.get("needs_plotly")
        assert result_cell["outputs"][0]["output_type"] == "stream"

    def test_empty_outputs_no_plotly_flag(self):

        cell = nbformat.from_dict(
            {
                "cell_type": "code",
                "source": "",
                "metadata": {},
                "outputs": [],
            }
        )

        preprocessor = PlotlyPreprocessor()
        _, resources = preprocessor.preprocess_cell(cell, {}, 0)
        assert not resources.get("needs_plotly")
