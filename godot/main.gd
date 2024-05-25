extends Node

func _process(delta):
	if Input.is_action_just_released("move_down"):
		$GodotGPTNPCHandler.send_character_message("knight", "hello", false)
		#$GodotGPTNPCHandler.send_character_message("knight", "how are you?")

func _ready():
	$DialogueBox.hide()
	$GodotGPTNPCHandler.connect_to_host("127.0.0.1", 5000, true, false)
	
