Coilmarket_ParkGrid:
	setvar VAR_COILMARKET_SWITCHES, 5
	return

Coilmarket_GridChanged:
	playse SE_SELECT
	call Coilmarket_RefreshGrid
	special DrawWholeMapView
	call Coilmarket_DisplayMeter
	releaseall
	end

Coilmarket_GridLocked:
	msgbox Coilmarket_Text_GridLocked, MSGBOX_DEFAULT
	releaseall
	end

Coilmarket_ReadMeter::
	lockall
	call Coilmarket_DisplayMeter
	releaseall
	end

Coilmarket_ReturnToEntrance:
	lockall
	msgbox Coilmarket_Text_ReturnToEntrance, MSGBOX_DEFAULT
	warp MAP_LAVARIDGE_TOWN_GYM_1F, 13, 17
	waitstate
	releaseall
	end

Coilmarket_FieldStation::
	lockall
	goto_if_set FLAG_BADGE04_GET, ReedwakeDelta_EventScript_CoilmarketLab
	msgbox Coilmarket_Text_FieldStation, MSGBOX_DEFAULT
	releaseall
	end

Coilmarket_Text_GridLocked:
	.string "The grid is set for regular service.$"

Coilmarket_Text_ReturnToEntrance:
	.string "BRIN: The tram needs a clear signal.\n"
	.string "Take the lift back to the switches.$"

Coilmarket_Text_FieldStation:
	.string "The field station opens after your\n"
	.string "certification battle with BRIN.$"
