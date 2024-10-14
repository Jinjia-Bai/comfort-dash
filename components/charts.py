import numpy as np
import pandas as pd
import math
import plotly.graph_objs as go
from pythermalcomfort.psychrometrics import psy_ta_rh, p_sat, t_dp, t_wb, enthalpy, t_o
from pythermalcomfort import set_tmp, two_nodes
from pythermalcomfort.models import pmv, adaptive_en, adaptive_ashrae, cooling_effect
from pythermalcomfort.utilities import v_relative, clo_dynamic, units_converter

from scipy import optimize
from components.drop_down_inline import generate_dropdown_inline
from utils.my_config_file import (
    ElementsIDs,
    Models,
    Functionalities,
    UnitSystem,
    UnitConverter,
)
from utils.website_text import TextHome
from scipy.optimize import fsolve
from decimal import Decimal, ROUND_HALF_UP


def chart_selector(selected_model: str, function_selection: str, chart_selected: str):
    list_charts = list(Models[selected_model].value.charts)
    if function_selection == Functionalities.Compare.value:
        if selected_model == Models.PMV_ashrae.name:
            list_charts = list(Models[selected_model].value.charts_compare)

    list_charts = [chart.name for chart in list_charts]

    if chart_selected is not None:
        chart_selected_output = chart_selected
    else:
        chart_selected_output = list_charts[0]

    drop_down_chart_dict = {
        "id": ElementsIDs.chart_selected.value,
        "question": TextHome.chart_selection.value,
        "options": list_charts,
        "multi": False,
        "default": chart_selected_output,
    }

    return generate_dropdown_inline(
        drop_down_chart_dict, value=drop_down_chart_dict["default"], clearable=False
    )


def get_inputs(inputs):
    tr = inputs[ElementsIDs.t_r_input.value]
    t_db = inputs[ElementsIDs.t_db_input.value]
    met = inputs[ElementsIDs.met_input.value]
    clo = inputs[ElementsIDs.clo_input.value]
    v = inputs[ElementsIDs.v_input.value]
    rh = inputs[ElementsIDs.rh_input.value]

    return met, clo, tr, t_db, v, rh


def compare_get_inputs(inputs):
    met_2 = inputs[ElementsIDs.met_input_input2.value]
    clo_2 = inputs[ElementsIDs.clo_input_input2.value]
    tr_2 = inputs[ElementsIDs.t_r_input_input2.value]
    t_db_2 = inputs[ElementsIDs.t_db_input_input2.value]
    v_2 = inputs[ElementsIDs.v_input_input2.value]
    rh_2 = inputs[ElementsIDs.rh_input_input2.value]

    return met_2, clo_2, tr_2, t_db_2, v_2, rh_2


def find_tdb_for_pmv(
    target_pmv,
    tr,
    vr,
    rh,
    met,
    clo,
    wme=0,
    standard="ISO",
    units="SI",
    tol=1e-2,
    max_iter=100,
):
    """Find the t_db value for a given PMV using bisection method"""
    if units == UnitSystem.SI.value:
        low, high = 10, 40
    else:
        low, high = 50, 96.8
    iterations = 0

    while iterations < max_iter:
        t_db_guess = (low + high) / 2
        pmv_value = pmv(
            tdb=t_db_guess,
            tr=tr,
            vr=vr,
            rh=rh,
            met=met,
            clo=clo,
            wme=wme,
            standard=standard,
            units=units,
        )

        if abs(pmv_value - target_pmv) < tol:
            return round(t_db_guess, 2)
        elif pmv_value < target_pmv:
            low = t_db_guess
        else:
            high = t_db_guess

        iterations += 1

    raise ValueError(
        "Unable to find suitable t_db value within maximum number of iterations"
    )


def psy_ashrae_pmv(
    inputs: dict = None,
    model: str = "ASHRAE",
    units: str = "SI",
):

    p_tdb = float(inputs[ElementsIDs.t_db_input.value])
    tr = float(inputs[ElementsIDs.t_r_input.value])
    vr = float(
        v_relative(  # Ensure vr is scalar
            v=inputs[ElementsIDs.v_input.value], met=inputs[ElementsIDs.met_input.value]
        )
    )
    p_rh = float(inputs[ElementsIDs.rh_input.value])
    met = float(inputs[ElementsIDs.met_input.value])
    clo = float(
        clo_dynamic(  # Ensure clo is scalar
            clo=inputs[ElementsIDs.clo_input.value],
            met=inputs[ElementsIDs.met_input.value],
        )
    )
    # save original values for plotting
    if units == UnitSystem.IP.value:
        tdb = round(float(units_converter(tdb=p_tdb)[0]), 1)
        tr = round(float(units_converter(tr=tr)[0]), 1)
        vr = round(float(units_converter(vr=vr)[0]), 1)
    else:
        tdb = p_tdb

    traces = []

    # blue area
    rh_values = np.arange(0, 110, 10)
    pmv_targets = [-0.5, 0.5]
    tdb_array = np.zeros((len(pmv_targets), len(rh_values)))

    for j, pmv_target in enumerate(pmv_targets):
        for i, rh_value in enumerate(rh_values):
            tdb_solution = find_tdb_for_pmv(
                target_pmv=pmv_target,
                tr=tr,
                vr=vr,
                rh=rh_value,
                met=met,
                clo=clo,
                standard=model,
            )
            tdb_array[j, i] = tdb_solution

    # calculate hr

    lower_upper_tdb = np.append(tdb_array[0], tdb_array[1][::-1])
    lower_upper_tdb = [
        round(float(value), 1) for value in lower_upper_tdb.tolist()
    ]  # convert to list & round to 1 decimal

    rh_list = np.append(np.arange(0, 110, 10), np.arange(100, -1, -10))
    # define
    lower_upper_hr = []
    for i in range(len(rh_list)):
        lower_upper_hr.append(
            psy_ta_rh(tdb=lower_upper_tdb[i], rh=rh_list[i])["hr"] * 1000
        )

    lower_upper_hr = [
        round(float(value), 1) for value in lower_upper_hr
    ]  # convert to list & round to 1 decimal

    if units == UnitSystem.IP.value:
        lower_upper_tdb = list(
            map(
                lambda x: round(float(units_converter(tmp=x, from_units="si")[0]), 1),
                lower_upper_tdb,
            )
        )

    traces.append(
        go.Scatter(
            x=lower_upper_tdb,
            y=lower_upper_hr,
            mode="lines",
            line=dict(color="rgba(0,0,0,0)"),
            fill="toself",
            fillcolor="rgba(59, 189, 237, 0.7)",
            showlegend=False,
            hoverinfo="none",
        )
    )

    # current point
    # Red point
    psy_results = psy_ta_rh(tdb, p_rh)
    hr = round(float(psy_results["hr"]) * 1000, 1)
    t_wb = round(float(psy_results["t_wb"]), 1)
    t_dp = round(float(psy_results["t_dp"]), 1)
    h = round(float(psy_results["h"]) / 1000, 1)

    if units == UnitSystem.IP.value:
        t_wb = round(float(units_converter(tmp=t_wb, from_units="si")[0]), 1)
        t_dp = round(float(units_converter(tmp=t_dp, from_units="si")[0]), 1)
        h = round(float(h / 2.326), 1)  # kJ/kg => btu/lb
        tdb = p_tdb

    traces.append(
        go.Scatter(
            x=[tdb],
            y=[hr],
            mode="markers",
            marker=dict(
                color="red",
                size=6,
            ),
            showlegend=False,
            hoverinfo="none",
        )
    )

    # lines

    rh_list = np.arange(0, 110, 10, dtype=float).tolist()
    tdb_list = np.linspace(10, 36, 500, dtype=float).tolist()
    if units == UnitSystem.IP.value:
        tdb_list_conv = list(
            map(
                lambda x: round(float(units_converter(tmp=x, from_units="si")[0]), 1),
                tdb_list,
            )
        )
    else:
        tdb_list_conv = tdb_list

    for rh in rh_list:
        hr_list = np.array(
            [psy_ta_rh(tdb=t, rh=rh, p_atm=101325)["hr"] * 1000 for t in tdb_list]
        )  # kg/kg => g/kg
        trace = go.Scatter(
            x=tdb_list_conv,
            y=hr_list,
            mode="lines",
            line=dict(color="grey", width=1),
            hoverinfo="none",
            name=f"{rh}% RH",
            showlegend=False,
        )
        traces.append(trace)

    # add transparent grid
    x_range = (
        np.linspace(10, 36, 100)
        if units == UnitSystem.SI.value
        else np.linspace(50, 96.8, 100)
    )
    y_range = np.linspace(0, 30, 100)
    xx, yy = np.meshgrid(x_range, y_range)

    traces.append(
        go.Scatter(
            x=xx.flatten(),
            y=yy.flatten(),
            mode="markers",
            marker=dict(size=2, color="rgba(0,0,0,0)"),
            hoverinfo="x+y",
            name="Interactive Hover Area",
            showlegend=False,
        )
    )

    if units == UnitSystem.SI.value:
        temperature_unit = "°C"
        hr_unit = "g<sub>w</sub>/kg<sub>da</sub>"
        h_unit = "kJ/kg"
    else:
        temperature_unit = "°F"
        hr_unit = "lb<sub>w</sub>/klb<sub>da</sub>"
        h_unit = "btu/lb"

    # layout
    layout = go.Layout(
        hovermode="closest",
        xaxis=dict(
            title=(
                "Dry-bulb Temperature [°C]"
                if units == UnitSystem.SI.value
                else "operative Temperature [°F]"
            ),
            range=[10, 36] if units == UnitSystem.SI.value else [50, 96.8],
            dtick=2,
            showgrid=True,
            showline=True,
            linewidth=1.5,
            linecolor="lightgrey",
        ),
        yaxis=dict(
            title=(
                "Humidity Ratio [g<sub>w</sub>/kg<sub>da</sub>]"
                if units == UnitSystem.SI.value
                else "Humidity ratio [lb<sub>w</sub>/klb<sub>da</sub>]"
            ),
            range=[0, 30],
            dtick=5,
            showgrid=True,
            showline=True,
            linewidth=1.5,
            linecolor="lightgrey",
            side="right",
        ),
        annotations=[
            dict(
                x=14 if units == UnitSystem.SI.value else 57.2,
                y=28,
                xref="x",
                yref="y",
                text=(
                    f"t<sub>db</sub>: {tdb:.1f} {temperature_unit}<br>"
                    f"rh: {p_rh:.1f} %<br>"
                    f"W<sub>a</sub>: {hr} {hr_unit}<br>"
                    f"t<sub>wb</sub>: {t_wb} {temperature_unit}<br>"
                    f"t<sub>dp</sub>: {t_dp} {temperature_unit}<br>"
                    f"h: {h} {h_unit}"
                ),
                showarrow=False,
                align="left",
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="rgba(0,0,0,0)",
                font=dict(size=14),
            )
        ],
        showlegend=True,
        plot_bgcolor="white",
    )

    fig = go.Figure(data=traces, layout=layout)
    return fig


def generate_tdb_hr_chart(
    inputs: dict = None,
    model: str = "ISO",
    units: str = "SI",
):

    p_tdb = inputs[ElementsIDs.t_db_input.value]
    p_tr = inputs[ElementsIDs.t_r_input.value]
    p_v = inputs[ElementsIDs.v_input.value]
    p_rh = inputs[ElementsIDs.rh_input.value]
    p_met = inputs[ElementsIDs.met_input.value]
    p_clo_d = inputs[ElementsIDs.clo_input.value]

    traces = []

    # green area
    rh = np.arange(0, 101, 20)
    pmv_list = [-0.7, -0.5, -0.2, 0.2, 0.5, 0.7]
    v_r = v_relative(v=p_v, met=p_met)
    tdb_dict = {}
    for j in range(len(pmv_list)):
        tdb_dict[j] = []
        for i in range(len(rh)):
            solution = fsolve(
                lambda x: find_tdb_for_pmv(
                    t_db_x=x,
                    t_r=p_tr,
                    v_r=v_r,
                    r_h=rh[i],
                    met=p_met,
                    clo_d=p_clo_d,
                    model=model,
                    pmv_y=pmv_list[j],
                ),
                22,
            )
            tdb_solution = Decimal(solution[0]).quantize(
                Decimal("0.0"), rounding=ROUND_HALF_UP
            )  # ℃
            tdb_dict[j].append(float(tdb_solution))

    # hr
    iii_lower_upper_tdb = np.append(np.array(tdb_dict[0]), np.array(tdb_dict[5])[::-1])
    ii_lower_upper_tdb = np.append(np.array(tdb_dict[1]), np.array(tdb_dict[4])[::-1])
    i_lower_upper_tdb = np.append(np.array(tdb_dict[2]), np.array(tdb_dict[3])[::-1])
    rh_list = np.append(np.arange(0, 101, 20), np.arange(100, -1, -20))
    # define
    iii_lower_upper_hr = []
    ii_lower_upper_hr = []
    i_lower_upper_hr = []
    for i in range(len(rh_list)):
        iii_lower_upper_hr.append(
            psy_ta_rh(tdb=iii_lower_upper_tdb[i], rh=rh_list[i], p_atm=101325)["hr"]
            * 1000
        )
        ii_lower_upper_hr.append(
            psy_ta_rh(tdb=ii_lower_upper_tdb[i], rh=rh_list[i], p_atm=101325)["hr"]
            * 1000
        )
        i_lower_upper_hr.append(
            psy_ta_rh(tdb=i_lower_upper_tdb[i], rh=rh_list[i], p_atm=101325)["hr"]
            * 1000
        )

    # traces[0]
    traces.append(
        go.Scatter(
            x=iii_lower_upper_tdb,
            y=iii_lower_upper_hr,
            mode="lines",
            line=dict(color="rgba(0,0,0,0)"),
            fill="toself",
            fillcolor="rgba(28,128,28,0.2)",
            showlegend=False,
            hoverinfo="none",
        )
    )
    # category II
    traces.append(
        go.Scatter(
            x=ii_lower_upper_tdb,
            y=ii_lower_upper_hr,
            mode="lines",
            line=dict(color="rgba(0,0,0,0)"),
            fill="toself",
            fillcolor="rgba(28,128,28,0.3)",
            showlegend=False,
            hoverinfo="none",
        )
    )
    # category I
    traces.append(
        go.Scatter(
            x=i_lower_upper_tdb,
            y=i_lower_upper_hr,
            mode="lines",
            line=dict(color="rgba(0,0,0,0)"),
            fill="toself",
            fillcolor="rgba(28,128,28,0.4)",
            showlegend=False,
            hoverinfo="none",
        )
    )

    # Red point
    red_point_x = p_tdb
    red_point_y = (
        psy_ta_rh(tdb=p_tdb, rh=p_rh, p_atm=101325)["hr"] * 1000
    )  # kg/kg => g/kg
    traces.append(
        go.Scatter(
            x=[red_point_x],
            y=[red_point_y],
            mode="markers",
            marker=dict(
                color="red",
                size=4,
            ),
            showlegend=False,
        )
    )

    # line
    rh_list = np.arange(0, 101, 10)
    tdb = np.linspace(10, 36, 500)
    for rh in rh_list:
        hr_list = np.array(
            [psy_ta_rh(tdb=t, rh=rh, p_atm=101325)["hr"] * 1000 for t in tdb]
        )  # kg/kg => g/kg
        trace = go.Scatter(
            x=tdb,
            y=hr_list,
            mode="lines",
            line=dict(color="grey", width=1),
            hoverinfo="x+y",
            name=f"{rh}% RH",
            showlegend=False,
        )
        traces.append(trace)
    tdb = inputs[ElementsIDs.t_db_input.value]
    rh = inputs[ElementsIDs.rh_input.value]
    tr = inputs[ElementsIDs.t_r_input.value]
    psy_results = psy_ta_rh(tdb, rh)

    ##title
    layout = go.Layout(
        xaxis=dict(
            title=(
                "Dry-bulb Temperature [°C]"
                if units == UnitSystem.SI.value
                else "Dry-bulb Temperature [°F]"
            ),
            range=[10, 36],
            dtick=2,
            showgrid=True,
            showline=True,
            linewidth=1.5,
            linecolor="lightgrey",
        ),
        yaxis=dict(
            title="Humidity Ratio [g<sub>w</sub>/kg<sub>da</sub>]",
            range=[0, 30],
            dtick=5,
            showgrid=True,
            showline=True,
            linewidth=1.5,
            linecolor="lightgrey",
            side="right",
        ),
        showlegend=True,
        plot_bgcolor="white",
        annotations=[
            dict(
                x=14,
                y=28,
                xref="x",
                yref="y",
                text=(
                    f"t<sub>db</sub>: {tdb:.1f} °C<br>"
                    f"rh: {rh:.1f} %<br>"
                    f"W<sub>a</sub>: {psy_results.hr * 1000:.1f} g<sub>w</sub>/kg<sub>da</sub><br>"
                    f"t<sub>wb</sub>: {psy_results.t_wb:.1f} °C<br>"
                    f"t<sub>dp</sub>: {psy_results.t_dp:.1f} °C<br>"
                    f"h: {psy_results.h / 1000:.1f} kJ/kg"
                ),
                showarrow=False,
                align="left",
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="rgba(0,0,0,0)",
                font=dict(size=14),
            )
        ],
    )

    fig = go.Figure(data=traces, layout=layout)
    return fig
