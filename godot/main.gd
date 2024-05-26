extends Node

func _process(delta):
	if Input.is_action_just_released("move_down"):
		$GodotGPTNPCHandler.send_character_message("knight", "hello", false)
		$GodotGPTNPCHandler.send_character_message("knight", "hello")

func _ready():
	$DialogueBox.hide()
	$GodotGPTNPCHandler.connect_to_host("127.0.0.1", 5000, true, false)


func _on_godot_gptnpc_handler_connected():
	pass # Replace with function body.

func _on_godot_gptnpc_handler_connection_error(error):
	pass # Replace with function body.


func _on_godot_gptnpc_handler_started_character_response_stream(response):
	print(response)

func _on_godot_gptnpc_handler_character_response_stream(response):
	print(response)

func _on_godot_gptnpc_handler_stopped_character_response_stream(response):
	print(response)
	






