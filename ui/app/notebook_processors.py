import json
import uuid

import nbformat
from nbconvert.preprocessors import Preprocessor


class PlotlyPreprocessor(Preprocessor):
    """Convert application/vnd.plotly.v1+json outputs to rendered HTML."""

    def preprocess_cell(self, cell, resources, cell_index):
        new_outputs = []
        needs_plotly = resources.get("needs_plotly", False)
        for output in cell.get("outputs", []):
            plotly_json = output.get("data", {}).get("application/vnd.plotly.v1+json")
            if plotly_json is not None:
                div_id = f"plotly-{uuid.uuid4().hex}"
                fig_json = json.dumps(plotly_json)
                html = (
                    f'<div id="{div_id}" style="width:100%;min-height:400px;"></div>'
                    f"<script>"
                    f"(function(){{"
                    f"  var fig = {fig_json};"
                    f'  Plotly.newPlot("{div_id}", fig.data, fig.layout, fig.config || {{}});'
                    f"}})();"
                    f"</script>"
                )
                output = nbformat.from_dict(
                    {
                        "output_type": output["output_type"],
                        "metadata": output.get("metadata", {}),
                        "data": {
                            "text/html": html,
                            "text/plain": "[Plotly figure]",
                        },
                    }
                )
                needs_plotly = True
            new_outputs.append(output)
        cell["outputs"] = new_outputs
        resources["needs_plotly"] = needs_plotly
        return cell, resources
