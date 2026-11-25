Seedvault_PrepareClearedRoom:
	setvar VAR_SEEDVAULT_A, 1
	setvar VAR_SEEDVAULT_B, 1
	setvar VAR_SEEDVAULT_C, 1
	return

Seedvault_ServiceExit:
	lockall
	msgbox Seedvault_Text_ServiceExit, MSGBOX_DEFAULT
	warp MAP_DEWFORD_TOWN_GYM, 5, 26
	waitstate
	releaseall
	end

Seedvault_CheckReceiver::
	lockall
	goto_if_eq VAR_SEEDVAULT_LIT, 1, Seedvault_ReceiverLit
	msgbox Seedvault_Text_ReceiverDark, MSGBOX_DEFAULT
	goto Seedvault_Release

Seedvault_ReceiverLit:
	msgbox Seedvault_Text_ReceiverLit, MSGBOX_DEFAULT

Seedvault_Release:
	releaseall
	end

Seedvault_FieldStation::
	goto_if_set FLAG_BADGE02_GET, ReedwakeDelta_EventScript_SeedvaultLab
	msgbox Seedvault_Text_StationLocked, MSGBOX_SIGN
	end

Seedvault_Text_ReceiverDark:
	.string "GERMINATION RECEIVER: DARK\p"
	.string "The mirror arrows show where the light\n"
	.string "will go next. Follow the lit beam.$"

Seedvault_Text_ReceiverLit:
	.string "GERMINATION RECEIVER: ACTIVE\p"
	.string "The inner gate is open.$"

Seedvault_Text_StationLocked:
	.string "SEEDVAULT FIELD STATION\p"
	.string "Certified surveyors only.$"

Seedvault_Text_ServiceExit:
	.string "The receiver is still dark. Use the\n"
	.string "service walk to return to the mirrors.$"

Seedvault_Text_MirrorFixed:
	.string "The mirror has been set in its berth.$"

Seedvault_Text_ReflectionChanged:
	.string "The prism creaks into a new position.$"

Seedvault_TurnMirrorA::
	lockall
	goto_if_set FLAG_BADGE02_GET, Seedvault_MirrorFixed
	goto_if_eq VAR_SEEDVAULT_A, 0, Seedvault_TurnAOne
	setvar VAR_SEEDVAULT_A, 0
	goto Seedvault_ApplyTurn

Seedvault_TurnAOne:
	setvar VAR_SEEDVAULT_A, 1
	goto Seedvault_ApplyTurn

Seedvault_TurnMirrorB::
	lockall
	goto_if_set FLAG_BADGE02_GET, Seedvault_MirrorFixed
	goto_if_eq VAR_SEEDVAULT_B, 0, Seedvault_TurnBOne
	setvar VAR_SEEDVAULT_B, 0
	goto Seedvault_ApplyTurn

Seedvault_TurnBOne:
	setvar VAR_SEEDVAULT_B, 1
	goto Seedvault_ApplyTurn

Seedvault_TurnMirrorC::
	lockall
	goto_if_set FLAG_BADGE02_GET, Seedvault_MirrorFixed
	goto_if_eq VAR_SEEDVAULT_C, 0, Seedvault_TurnCOne
	setvar VAR_SEEDVAULT_C, 0
	goto Seedvault_ApplyTurn

Seedvault_TurnCOne:
	setvar VAR_SEEDVAULT_C, 1
	goto Seedvault_ApplyTurn

Seedvault_ApplyTurn:
	playse SE_SWITCH
	call Seedvault_TraceLight
	special DrawWholeMapView
	goto_if_eq VAR_SEEDVAULT_LIT, 1, Seedvault_ReceiverLit
	msgbox Seedvault_Text_ReflectionChanged, MSGBOX_DEFAULT
	goto Seedvault_Release

Seedvault_MirrorFixed:
	msgbox Seedvault_Text_MirrorFixed, MSGBOX_DEFAULT
	goto Seedvault_Release
