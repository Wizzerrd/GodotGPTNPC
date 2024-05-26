extends Area2D

signal start_conversation
signal end_conversation

var player
var talking = false
var velocity = Vector2.ZERO

func _ready():
	$BasicMobSprite.choose_type("knight")
	$Exclamation.hide()
	player = get_parent().get_node("Player")
	
func _physics_process(delta):
	player = get_parent().get_node("Player")
	if player: z_index = position.y - player.global_position.y
	if player: $Rotation.look_at(player.global_position)
	$BasicMobSprite.choose_animation(velocity, $Rotation.rotation_degrees)
	if Input.is_action_just_pressed("talk") and $Exclamation.visible and not talking: 
		start_conversation.emit()
		talking = true
	if Input.is_action_just_pressed("end_conversation") and talking:
		end_conversation.emit()
		talking = false

func _on_body_entered(body):
	$Exclamation.show()

func _on_body_exited(body):
	if body == player: $Exclamation.hide()
