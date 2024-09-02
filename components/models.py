import pythermalcomfort.models as ptcm

def CalculatePHS(AIR_TEMPERATURE, MRT, AIR_SPEED, RH, MET, CLOTHING, POSTURE, WME):
    print(f"Calculating PHS with: AIR_TEMPERATURE={AIR_TEMPERATURE}, MRT={MRT}, AIR_SPEED={AIR_SPEED}, RH={RH}, MET={MET}, CLOTHING={CLOTHING}, POSTURE={POSTURE}, WME={WME}")
    POSTURE = int(POSTURE)
    result = ptcm.phs(tdb=AIR_TEMPERATURE, tr=MRT, rh=RH, v=AIR_SPEED, met=MET, clo=CLOTHING, posture=POSTURE, wme=WME)
    print(f"phs result: {result}")
    t_re = result['t_re']
    d_lim_loss_50 = result['d_lim_loss_50']
    d_lim_loss_95 = result['d_lim_loss_95']
    return t_re, d_lim_loss_50, d_lim_loss_95

