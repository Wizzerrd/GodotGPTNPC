extends Node

func _process(delta):
	pass

func _ready():
	$DialogueBox.hide()
	$GodotGPTNPCHandler.connect_to_host("127.0.0.1", 5000, true, false)

func _on_npc_start_conversation():
	$Player.talking = true
	$DialogueBox.show()

func _on_npc_end_conversation():
	$Player.talking = false
	$DialogueBox.hide()

func _on_dialogue_box_send_message(message):
	$GodotGPTNPCHandler.send_character_message("knight", message)
	
### GPT NPC Signal Listeners ###

func _on_godot_gptnpc_handler_connected():
	pass # Replace with function body.

func _on_godot_gptnpc_handler_connection_error(error):
	pass # Replace with function body.

func _on_godot_gptnpc_handler_started_character_response_stream(response):
	$DialogueBox.add_message("Knight")
	print(response)

func _on_godot_gptnpc_handler_character_response_stream(response):
	$DialogueBox.update_last_message(response["content"])
	print(response)

func _on_godot_gptnpc_handler_stopped_character_response_stream(response):
	$DialogueBox.waiting = false
	print(response)
	





