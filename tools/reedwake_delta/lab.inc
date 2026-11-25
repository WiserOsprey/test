ReedwakeDelta_EventScript_Lab::
	lockall
	msgbox ReedwakeDelta_Text_Offer, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, NO, ReedwakeDelta_EventScript_Close
	special ChoosePartyMon
	waitstate
	goto_if_eq VAR_0x8004, PARTY_NOTHING_CHOSEN, ReedwakeDelta_EventScript_Close
	specialvar VAR_RESULT, ReedwakeDelta_CheckSelected
	goto_if_eq VAR_RESULT, 2, ReedwakeDelta_EventScript_TrialRequired
	goto_if_eq VAR_RESULT, 3, ReedwakeDelta_EventScript_AlreadyConverted
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

ReedwakeDelta_EventScript_Unsupported:
	msgbox ReedwakeDelta_Text_Unsupported, MSGBOX_DEFAULT

ReedwakeDelta_EventScript_Close:
	releaseall
	end

ReedwakeDelta_Text_Offer:
	.string "BRACKENHAVEN RESONANCE LAB\p"
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

ReedwakeDelta_Text_Unsupported:
	.string "The lab has no recipe for this\n"
	.string "POKéMON yet.$"
