@tool 
extends EditorPlugin

func _enter_tree():
	add_custom_type("GodotGPTNPCHandler", "Node", preload("GodotGPTNPCHandler.gd"), preload("icon.png"))
	pass

func _exit_tree():
	remove_custom_type("GodotGPTNPCHandler")
	pass
