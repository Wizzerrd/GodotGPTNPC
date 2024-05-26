extends Node

signal new_sse_event(headers, event, data)
signal connected
signal connection_error(error)

var httpclient = HTTPClient.new()
var is_connected = false

var domain
var port
var use_ssl
var verify_host
var told_to_connect = false
var establishing_connection = false
var request_in_progress = false
var timed_out = false
var response_body = PackedByteArray()
var request_queue = Queue.new()

var process_id

func check_if_connected():
	if !told_to_connect:
		return
	if !is_connected:
		if !establishing_connection:
			attempt_to_connect()
			return
		elif timed_out:
			print("Connection timed out")
			told_to_connect = false
			establishing_connection = false
			return
		else:
			if $Timeout.is_stopped(): 
				$Timeout.start()
				return
			else:
				httpclient.poll()
				if httpclient.get_status() == HTTPClient.STATUS_CONNECTED:
					print("Connected to host!")
					$Timeout.stop()
					is_connected = true
					establishing_connection = false
				return
	return true

func connect_to_host(domain : String, port : int = -1, use_ssl : bool = false, verify_host : bool = true):
	self.domain = domain
	self.port = port
	self.use_ssl = use_ssl
	self.verify_host = verify_host
	told_to_connect = true

func attempt_to_connect():
	print("Attempting to connect to host at " + domain + ":" + str(port)+ "...")
	establishing_connection = true
	httpclient.connect_to_host(domain, port)

func attempt_to_request(httpclient_status):
	if httpclient_status == HTTPClient.STATUS_CONNECTING or httpclient_status == HTTPClient.STATUS_RESOLVING:
		return
	if httpclient_status == HTTPClient.STATUS_CONNECTED:
		var outgoing_request = request_queue.dequeue()
		var err = httpclient.request(outgoing_request["method"], outgoing_request["url"], outgoing_request["headers"], outgoing_request["body"])
		if err == OK: request_in_progress = true

func stream_response(httpclient_status):
	var chunk = httpclient.read_response_body_chunk()
	if(chunk.size() != 0):
		var body = JSON.parse_string(chunk.get_string_from_utf8())
		print(body)
		if "stream-status" in body:
			var stream_status = body["stream-status"]
			var content = body["content"]
			print(content)
			if stream_status == "stopping":
				request_in_progress = false

func _process(delta):
	if !check_if_connected(): return		
	httpclient.poll()
	var httpclient_status = httpclient.get_status()
	
	if httpclient_status == HTTPClient.STATUS_CONNECTION_ERROR: 
		is_connected = false
		attempt_to_connect()
		
	if not request_queue.empty():
			if !request_in_progress:
				attempt_to_request(httpclient_status)
	var httpclient_has_response = httpclient.has_response()
	if httpclient_has_response or httpclient_status == HTTPClient.STATUS_BODY: stream_response(httpclient_status)

func send_character_message(character_ref, message, streaming=true):
	var url = "http://" + domain +"/characters/" + character_ref + "/messages"
	var body = JSON.stringify({"message":message, "streaming":streaming})
	var headers = ["Content-Type: application/json", "Accept: text/event-stream"]
	var method = HTTPClient.METHOD_POST
	set_outgoing_request(method, url, headers, body)

func set_outgoing_request(method, url, headers, body):
	var req = {"method":method, "url":url, "headers":headers, "body":body}
	request_queue.enqueue(req)

func _exit_tree():
	if httpclient:
		httpclient.close()

func _notification(what):
	if what == NOTIFICATION_WM_CLOSE_REQUEST:
		if httpclient:
			httpclient.close()
		get_tree().quit()

func _on_timeout():
	timed_out = true # Replace with function body.
