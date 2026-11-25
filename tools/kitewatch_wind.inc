Kitewatch_TurnDial::
	lockall
	goto_if_set FLAG_BADGE03_GET, Kitewatch_DialLocked
	goto_if_eq VAR_KITEWATCH_WIND, 1, Kitewatch_TurnEast
	setvar VAR_KITEWATCH_WIND, 1
	call Kitewatch_ShowWind
	msgbox Kitewatch_Text_WestWind, MSGBOX_DEFAULT
	goto Kitewatch_Release

Kitewatch_TurnEast:
	setvar VAR_KITEWATCH_WIND, 0
	call Kitewatch_ShowWind
	msgbox Kitewatch_Text_EastWind, MSGBOX_DEFAULT
	goto Kitewatch_Release

Kitewatch_ShowWind:
	playse SE_SWITCH
	call Kitewatch_ApplyWind
	special DrawWholeMapView
	return

Kitewatch_DialLocked:
	msgbox Kitewatch_Text_DialLocked, MSGBOX_DEFAULT

Kitewatch_Release:
	releaseall
	end

Kitewatch_ReturnToEntrance:
	lockall
	msgbox Kitewatch_Text_ReturnToEntrance, MSGBOX_DEFAULT
	warp MAP_MAUVILLE_CITY_GYM, 4, 19
	waitstate
	releaseall
	end

Kitewatch_FieldStation::
	goto_if_set FLAG_BADGE03_GET, ReedwakeDelta_EventScript_KitewatchLab
	msgbox Kitewatch_Text_StationLocked, MSGBOX_SIGN
	end

Kitewatch_Text_WestWind:
	.string "The platforms glide to the west.$"

Kitewatch_Text_EastWind:
	.string "The platforms glide to the east.$"

Kitewatch_Text_DialLocked:
	.string "VENN has secured the crossings at\n"
	.string "their landings.$"

Kitewatch_Text_ReturnToEntrance:
	.string "PELL's certification is needed here.\p"
	.string "Use the service lift to return to the\n"
	.string "entrance.$"

Kitewatch_Text_StationLocked:
	.string "KITEWATCH FIELD STATION\p"
	.string "Certified surveyors only.$"
