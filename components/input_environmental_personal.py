from utils.my_config_file import (
    ModelInputsAdaptiveAshrae55,
    ModelInputsInfo,
    ModelInputsPmvAshrae55,
    ModelInputsAdaptiveEN16798,
    ModelInputsPmvEN16798,
    ModelInputsSelectionOperativeTemperaturePmvEN16798,
    MODELS,
)
import dash_mantine_components as dmc
from components.dropdowns import (
    Ash55_air_speed_selection, 
    En16798_air_speed_selection, 
    En16798_relative_humidity_selection,
    En16798_relative_metabolic_selection,
    En16798_relative_clothing_selection,
)


def input_environmental_personal(selected_model):
    inputs = []

    model_inputs = ModelInputsPmvAshrae55()
    if selected_model == MODELS.Adaptive_EN.value:

        model_inputs = ModelInputsAdaptiveEN16798()
    elif selected_model == MODELS.PMV_ashrae.value:
        model_inputs = ModelInputsPmvAshrae55()

    elif selected_model == MODELS.Adaptive_ashrae.value:
        model_inputs = ModelInputsAdaptiveAshrae55()

    elif selected_model == MODELS.PMV_EN.value:
        model_inputs = ModelInputsPmvEN16798()

    for var_name, values in dict(model_inputs).items():
        input_filed = dmc.NumberInput(
            label=values.name,
            description=f"From {values.min} to {values.max}",
            value=values.value,
            min=values.min,
            max=values.max,
            step=values.step,
        )
        inputs.append(input_filed)

    if selected_model == MODELS.Adaptive_ashrae.value:
        inputs.append(Ash55_air_speed_selection())

    if selected_model == MODELS.Adaptive_EN.value:
        inputs.append(En16798_air_speed_selection())


    #input right
    inputs_right = []
    
    model_inputs = ModelInputsPmvAshrae55()
    if selected_model == MODELS.PMV_EN.value:
        inputs_right.append(dmc.Space(h=40))
        inputs_right.append(dmc.Checkbox(label=ModelInputsSelectionOperativeTemperaturePmvEN16798.o_1.value, checked=False,style={"margin-left": "25px"}))
        inputs_right.append(dmc.Space(h=243))
        inputs_right.append(En16798_relative_humidity_selection())
        inputs_right.append(dmc.Space(h=26))
        inputs_right.append(En16798_relative_metabolic_selection())
        inputs_right.append(dmc.Space(h=45))
        inputs_right.append(En16798_relative_clothing_selection())

    elif selected_model == MODELS.Adaptive_EN.value:
        inputs_right.append(dmc.Space(h=40))
        inputs_right.append(dmc.Checkbox(label=ModelInputsSelectionOperativeTemperaturePmvEN16798.o_1.value, checked=False,style={"margin-left": "25px"}))
        
    if selected_model == MODELS.PMV_ashrae.value:
        inputs_right.append(dmc.Space(h=40))
        inputs_right.append(dmc.Checkbox(label=ModelInputsSelectionOperativeTemperaturePmvEN16798.o_1.value, checked=False,style={"margin-left": "25px"}))

    elif selected_model == MODELS.Adaptive_ashrae.value:
        inputs_right.append(dmc.Space(h=40))
        inputs_right.append(dmc.Checkbox(label=ModelInputsSelectionOperativeTemperaturePmvEN16798.o_1.value, checked=False,style={"margin-left": "25px"}))




    return dmc.Paper(
        children=[
        dmc.Text("Inputs", mb="xs", fw=700),
        dmc.Grid(
            children=[
                dmc.GridCol(
                    dmc.Stack(inputs,gap="xs"),  
                    span={"base": 12, "sm": 5}
                ),
                dmc.GridCol(
                    dmc.Stack(inputs_right,gap="xs"),
                    span={"base": 12, "sm": 7}
                ),
            ],
            gutter="md",  
        ),
    ],
        shadow="md",
        p="md",
    )
