Lockmere_ApplyWaterLevel:
	goto_if_lt VAR_LOCKMERE_WATER_LEVEL, 1, Lockmere_MapReady
	setmetatile 5, 12, @CROSSING@, 0
	setmetatile 6, 12, @CROSSING@, 0
	goto_if_lt VAR_LOCKMERE_WATER_LEVEL, 2, Lockmere_MapReady
	setmetatile 5, 7, @CROSSING@, 0
	setmetatile 6, 7, @CROSSING@, 0

Lockmere_MapReady:
	return

Lockmere_OpenIntake::
	lockall
	goto_if_ge VAR_LOCKMERE_WATER_LEVEL, 1, Lockmere_IntakeOpen
	msgbox Lockmere_Text_ConfirmIntake, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, NO, Lockmere_Release
	setvar VAR_LOCKMERE_WATER_LEVEL, 1
	call Lockmere_ApplyWaterLevel
	special DrawWholeMapView
	msgbox Lockmere_Text_LowerCrossing, MSGBOX_DEFAULT
	goto Lockmere_Release

Lockmere_IntakeOpen:
	msgbox Lockmere_Text_IntakeOpen, MSGBOX_DEFAULT
	goto Lockmere_Release

Lockmere_ReadGauge::
	lockall
	goto_if_ge VAR_LOCKMERE_WATER_LEVEL, 2, Lockmere_GaugeClear
	msgbox Lockmere_Text_GaugeHigh, MSGBOX_DEFAULT
	goto Lockmere_Release

Lockmere_GaugeClear:
	msgbox Lockmere_Text_GaugeClear, MSGBOX_DEFAULT
	goto Lockmere_Release

Lockmere_FillValve::
	lockall
	goto_if_ge VAR_LOCKMERE_WATER_LEVEL, 2, Lockmere_GaugeClear
	msgbox Lockmere_Text_FillValve, MSGBOX_DEFAULT
	goto Lockmere_Release

Lockmere_ReliefValve::
	lockall
	goto_if_lt VAR_LOCKMERE_WATER_LEVEL, 1, Lockmere_ReleaseStuck
	goto_if_ge VAR_LOCKMERE_WATER_LEVEL, 2, Lockmere_GaugeClear
	msgbox Lockmere_Text_ConfirmRelief, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, NO, Lockmere_Release
	setvar VAR_LOCKMERE_WATER_LEVEL, 2
	call Lockmere_ApplyWaterLevel
	special DrawWholeMapView
	msgbox Lockmere_Text_UpperCrossing, MSGBOX_DEFAULT
	goto Lockmere_Release

Lockmere_ReleaseStuck:
	msgbox Lockmere_Text_ServiceLadder, MSGBOX_DEFAULT
	warp MAP_RUSTBORO_CITY_GYM, 5, 17
	waitstate

Lockmere_Release:
	releaseall
	end

Lockmere_Text_ConfirmIntake:
	.string "INTAKE VANE\p"
	.string "Open the lower sluice?$"

Lockmere_Text_IntakeOpen:
	.string "The intake is open. The lower\n"
	.string "footbridge is clear.$"

Lockmere_Text_LowerCrossing:
	.string "The intake clicks into place. Water\n"
	.string "drops below the lower footbridge.$"

Lockmere_Text_GaugeHigh:
	.string "UPPER CHAMBER: HIGH PRESSURE\p"
	.string "The east wheel vents the chamber.\n"
	.string "The west wheel fills it.$"

Lockmere_Text_GaugeClear:
	.string "UPPER CHAMBER: DRAINED\p"
	.string "Both crossings are clear.$"

Lockmere_Text_FillValve:
	.string "WEST WHEEL: FILL\p"
	.string "The needle is already in the red.\n"
	.string "Opening this wheel would add water.$"

Lockmere_Text_ConfirmRelief:
	.string "EAST WHEEL: RELIEF\p"
	.string "Vent the upper chamber?$"

Lockmere_Text_UpperCrossing:
	.string "Water rushes into the bypass.\n"
	.string "The upper footbridge is clear!$"

Lockmere_Text_ServiceLadder:
	.string "The intake below is shut. Take the\n"
	.string "service ladder back to the entrance.$"

Lockmere_FieldStation::
	goto_if_set FLAG_BADGE01_GET, ReedwakeDelta_EventScript_LockmereLab
	msgbox Lockmere_Text_StationLocked, MSGBOX_SIGN
	end

Lockmere_Text_StationLocked:
	.string "LOCKMERE FIELD STATION\p"
	.string "Certified surveyors only.$"
