#!/usr/bin/env python
from api_types import DEFAULT_DATASET
from flask import Flask, render_template, request, redirect, url_for

import api
import dataset
import filters


app = Flask(__name__, static_folder="public", template_folder="views")


app.jinja_env.filters["diff_classname"] = filters.diff_classname_filter


################################################################################
# Home page reroute
################################################################################
@app.route("/")
def home():
    """Reroute home URL to license lookup form"""
    return redirect(url_for("license_page"))


################################################################################
# Licenses
################################################################################
LICENSE_CONTEXT = {
    "title": "Seattle Public Vehicle Lookup",
    "entities": [
        {
            "entity_name": "License (wildcard)",
            "query_param": "license",
        }
    ],
    "data_source": "https://data.seattle.gov/City-Business/Active-Fleet-Complement/enxu-fgzb",
    "lookup_url": "license",
}


@app.route("/license")
def license_page():
    """License lookup form render"""
    # Check for badge query params and load if it exists.
    license = request.args.get("license")
    html = dataset.license_lookup(license)

    # Return the basic lookup form if not
    return render_template("index.html", **LICENSE_CONTEXT, entity_html=html)


################################################################################
# Names
################################################################################
NAME_CONTEXT = {
    "title": "Officer Name Lookup",
    "data_source": "https://data.seattle.gov/City-Business/City-of-Seattle-Wage-Data/2khk-5ukd",
    "lookup_url": "name",
}


@app.route("/name")
def name_page():
    """Officer name lookup form render"""
    params = request.args.copy()
    # Pop the parameters we know will be present
    strict_search = False
    dataset_select = params.pop("dataset_select", DEFAULT_DATASET)
    datasets = api.get_datasets()
    metadata = datasets.get(dataset_select, "")
    entities = api.get_query_fields(metadata)
    if not metadata:
        # This shouldn't happen, but return *something* if the dataset is borked.
        html = f"<p><b>No data for dataset {dataset_select}</b></p>"
    elif all(val == "" for val in params.values()):
        # If all parameters are emtpy, it was probably a dataset switch.
        # Don't call the backend API unless we have something.
        html = ""
    else:
        html, strict_search = dataset.name_lookup(metadata, entities, **request.args)

    return render_template(
        "index.html",
        **NAME_CONTEXT,
        datasets=datasets.values(),
        entities=entities,
        strict_entities=[entity for entity in entities if not entity["is_fuzzy"]],
        entity_html=html,
        strict_search=strict_search,
        dataset_select=dataset_select,
    )


################################################################################
# Historical
################################################################################
HISTORICAL_CONTEXT = {
    "data_source": "https://data.seattle.gov/City-Business/City-of-Seattle-Wage-Data/2khk-5ukd",
}


@app.route("/historical-officers/<badge>")
def historical_page(badge):
    """Historical officer name lookup form render"""
    datasets = api.get_datasets()
    metadata = datasets.get("spd", "")
    if not metadata:
        # This shouldn't happen, but return *something* if the dataset is borked.
        html = "<p><b>No data for dataset historical SPD</b></p>"
    else:
        # throw away the strict_search value as historical search is always strict
        html, _ = dataset.name_lookup(
            metadata, entities=[], historical=True, badge=badge
        )

    return render_template(
        "historical.html",
        **HISTORICAL_CONTEXT,
        entity_html=html,
        badge=badge,
    )


################################################################################
# Old compatibility endpoints
################################################################################
@app.route("/license-lookup/<license>")
def license_lookup(license):
    # LEGACY DO NOT TOUCH
    html = dataset.license_lookup(license)
    return render_template("index.html", **LICENSE_CONTEXT, entity_html=html)


@app.route("/badge-lookup/<badge>")
def badge_lookup(badge):
    # LEGACY DO NOT TOUCH
    html = dataset.name_lookup(None, None, badge)
    return render_template("index.html", **NAME_CONTEXT, entity_html=html)


@app.route("/name-lookup/<name>")
def name_lookup(name):
    # LEGACY DO NOT TOUCH
    html = dataset.name_lookup(name, None, None)
    return render_template("index.html", **NAME_CONTEXT, entity_html=html)


if __name__ == "__main__":
    app.run()
