ReedwakeDelta_EventScript_Lab::
	lockall
	msgbox ReedwakeDelta_Text_Offer, MSGBOX_YESNO
	goto ReedwakeDelta_EventScript_Select

ReedwakeDelta_EventScript_LockmereLab::
	lockall
	msgbox ReedwakeDelta_Text_LockmereOffer, MSGBOX_YESNO

ReedwakeDelta_EventScript_Select:
	goto_if_eq VAR_RESULT, NO, ReedwakeDelta_EventScript_Close
	special ChoosePartyMon
	waitstate
	goto_if_eq VAR_0x8004, PARTY_NOTHING_CHOSEN, ReedwakeDelta_EventScript_Close
	specialvar VAR_RESULT, ReedwakeDelta_CheckSelected
	goto_if_eq VAR_RESULT, 2, ReedwakeDelta_EventScript_TrialRequired
	goto_if_eq VAR_RESULT, 3, ReedwakeDelta_EventScript_AlreadyConverted
	goto_if_eq VAR_RESULT, 4, ReedwakeDelta_EventScript_GrassTrial
	goto_if_eq VAR_RESULT, 5, ReedwakeDelta_EventScript_FireTrial
	goto_if_eq VAR_RESULT, 6, ReedwakeDelta_EventScript_WaterTrial
	goto_if_eq VAR_RESULT, 7, ReedwakeDelta_EventScript_SiltmoleTrial
	goto_if_eq VAR_RESULT, 8, ReedwakeDelta_EventScript_GategrubTrial
	goto_if_eq VAR_RESULT, 9, ReedwakeDelta_EventScript_LockmoleTrial
	goto_if_ne VAR_RESULT, 1, ReedwakeDelta_EventScript_Unsupported
	msgbox ReedwakeDelta_Text_Confirm, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, NO, ReedwakeDelta_EventScript_Close
	specialvar VAR_RESULT, ReedwakeDelta_ConvertSelected
	goto_if_eq VAR_RESULT, FALSE, ReedwakeDelta_EventScript_Unsupported
	msgbox ReedwakeDelta_Text_Success, MSGBOX_DEFAULT
	goto ReedwakeDelta_EventScript_Close

ReedwakeDelta_EventScript_TrialRequired:
	msgbox ReedwakeDelta_Text_TrialRequired, MSGBOX_DEFAULT
	goto ReedwakeDelta_EventScript_Close

ReedwakeDelta_EventScript_AlreadyConverted:
	msgbox ReedwakeDelta_Text_AlreadyConverted, MSGBOX_DEFAULT
	goto ReedwakeDelta_EventScript_Close

ReedwakeDelta_EventScript_GrassTrial:
	msgbox ReedwakeDelta_Text_GrassTrial, MSGBOX_DEFAULT
	goto ReedwakeDelta_EventScript_Close

ReedwakeDelta_EventScript_FireTrial:
	msgbox ReedwakeDelta_Text_FireTrial, MSGBOX_DEFAULT
	goto ReedwakeDelta_EventScript_Close

ReedwakeDelta_EventScript_WaterTrial:
	msgbox ReedwakeDelta_Text_WaterTrial, MSGBOX_DEFAULT
	goto ReedwakeDelta_EventScript_Close

ReedwakeDelta_EventScript_SiltmoleTrial:
	msgbox ReedwakeDelta_Text_SiltmoleTrial, MSGBOX_DEFAULT
	goto ReedwakeDelta_EventScript_Close

ReedwakeDelta_EventScript_GategrubTrial:
	msgbox ReedwakeDelta_Text_GategrubTrial, MSGBOX_DEFAULT
	goto ReedwakeDelta_EventScript_Close

ReedwakeDelta_EventScript_LockmoleTrial:
	msgbox ReedwakeDelta_Text_LockmoleTrial, MSGBOX_DEFAULT
	goto ReedwakeDelta_EventScript_Close

ReedwakeDelta_EventScript_Unsupported:
	msgbox ReedwakeDelta_Text_Unsupported, MSGBOX_DEFAULT

ReedwakeDelta_EventScript_Close:
	releaseall
	end

ReedwakeDelta_Text_Offer:
	.string "BRACKENHAVEN RESONANCE LAB\p"
	.string "Choose a POKéMON for a\n"
	.string "DELTA experiment?$"

ReedwakeDelta_Text_LockmereOffer:
	.string "LOCKMERE FIELD STATION\p"
	.string "Choose a POKéMON for a\n"
	.string "DELTA experiment?$"

ReedwakeDelta_Text_Confirm:
	.string "Change {STR_VAR_1} to its DELTA form?\p"
	.string "This change is permanent.$"

ReedwakeDelta_Text_Success:
	.string "{STR_VAR_1} took on its DELTA form!$"

ReedwakeDelta_Text_TrialRequired:
	.string "BULBASAUR's trial is still open.\n"
	.string "Check its FIELD NOTES for clues.$"

ReedwakeDelta_Text_AlreadyConverted:
	.string "This POKéMON is already in its\n"
	.string "DELTA form.$"

ReedwakeDelta_Text_GrassTrial:
	.string "We need a reading from this family.\p"
	.string "On BRACKEN TRAIL, use a GRASS move\n"
	.string "with it and win the wild battle.$"

ReedwakeDelta_Text_FireTrial:
	.string "We need a reading from this family.\p"
	.string "At TIDE REACH, use a FIRE move\n"
	.string "with it and win the wild battle.$"

ReedwakeDelta_Text_WaterTrial:
	.string "We need a reading from this family.\p"
	.string "On REEDBANK PATH, use a WATER move\n"
	.string "with it and win the wild battle.$"

ReedwakeDelta_Text_SiltmoleTrial:
	.string "Take SILTMOLE to GATEWORKS TUNNEL.\p"
	.string "Use a GROUND move with it and\n"
	.string "win the wild battle.$"

ReedwakeDelta_Text_GategrubTrial:
	.string "Take GATEGRUB to GATEWORKS TUNNEL.\p"
	.string "Use a ROCK move while it's holding\n"
	.string "an ORAN BERRY. Win that battle.$"

ReedwakeDelta_Text_LockmoleTrial:
	.string "Take LOCKMOLE to LOCKMERE CUT.\p"
	.string "Use a STEEL move with it and\n"
	.string "win the wild battle.$"

ReedwakeDelta_Text_Unsupported:
	.string "The lab has no recipe for this\n"
	.string "POKéMON yet.$"
