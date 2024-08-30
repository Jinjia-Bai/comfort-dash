from pythermalcomfort.models import adaptive_ashrae, adaptive_en, phs

#from pythermalcomfort.utilities import running_mean_outdoor_temperature

#t_running_mean = running_mean_outdoor_temperature(temp_array, alpha=0.8, units='IS')

#results = adaptive_ashrae(tdb=AIR_TEMPERATURE, tr=MRT, t_running_mean=RUNNING_MEAN_OUTDOOR_TEMPERATURE, v=ElementsIDs.SPEED_SELECTION)
#print(results)

#results = adaptive_en(tdb=AIR_TEMPERATURE, tr=MRT, t_running_mean=RUNNING_MEAN_OUTDOOR_TEMPERATURE, v=ElementsIDs.SPEED_SELECTION)
#print(results)

def CalculatePHS(AIR_TEMPERATURE, MRT, AIR_SPEED, RH, MET, COLTHING, POSTURE, WME):
    result = phs(tdb=AIR_TEMPERATURE, tr=MRT, rh=RH, v=AIR_SPEED, met=MET, clo=COLTHING, posture=POSTURE, wme=WME)
    print(f"phs result: {result}")
    t_re = result['t_re']
    d_lim_loss_50 = result['d_lim_loss_50']
    d_lim_loss_95 = result['d_lim_loss_95']
    return t_re, d_lim_loss_50, d_lim_loss_95

