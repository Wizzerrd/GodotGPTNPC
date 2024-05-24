extends Node

func _process(delta):
	if Input.is_action_just_released("move_down"):
		post_message("hello")

func _ready():
	$DialogueBox.hide()
	$GodotGPTNPCHandler.connect_to_host("127.0.0.1", "", 5000, true, false)
	
func post_message(message: String):
	var url = "http://127.0.0.1/characters/me/messages"
	var headers = ["Content-Type: application/json", "Accept: text/event-stream"]
	var method = HTTPClient.METHOD_POST
	var body = JSON.stringify({"message":message})
	$GodotGPTNPCHandler.set_outgoing_request(method, url, headers, body)
