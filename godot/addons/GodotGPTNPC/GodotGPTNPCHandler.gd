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
var response_body = PackedByteArray()
var request_queue = Queue.new()

var process_id

func connect_to_host(domain : String, port : int = -1, use_ssl : bool = false, verify_host : bool = true):
	self.domain = domain
	self.port = port
	self.use_ssl = use_ssl
	self.verify_host = verify_host
	told_to_connect = true

func attempt_to_connect():
	var err = httpclient.connect_to_host(domain, port)
	if err == OK:
		connected.emit()
		establishing_connection = false
		is_connected = true
	else: connection_error.emit(str(err))

func attempt_to_request(httpclient_status):
	if httpclient_status == HTTPClient.STATUS_CONNECTING or httpclient_status == HTTPClient.STATUS_RESOLVING:
		return
	if httpclient_status == HTTPClient.STATUS_CONNECTION_ERROR: 
		is_connected = false
		attempt_to_connect()
		
	if httpclient_status == HTTPClient.STATUS_CONNECTED:
		var outgoing_request = request_queue.dequeue()
		var err = httpclient.request(outgoing_request["method"], outgoing_request["url"], outgoing_request["headers"], outgoing_request["body"])
		if err == OK: request_in_progress = true

func _process(delta):
	if !told_to_connect:
		return
		
	if !is_connected:
		if !establishing_connection:
			attempt_to_connect()
			establishing_connection = true
		
	httpclient.poll()
	var httpclient_status = httpclient.get_status()

	if not request_queue.empty():
			if !request_in_progress:
				attempt_to_request(httpclient_status)
		
	var httpclient_has_response = httpclient.has_response()
		
	if httpclient_has_response or httpclient_status == HTTPClient.STATUS_BODY:
		var headers = httpclient.get_response_headers_as_dictionary()
		httpclient.poll()
		var chunk = httpclient.read_response_body_chunk()
		if(chunk.size() == 0):
			pass
			#return
		else:
			var body = JSON.parse_string(chunk.get_string_from_utf8())
			if "stream-status" in body:
				var stream_status = body["stream-status"]
				var content = body["content"]
				print(content)
				if stream_status == "stopping":
					request_in_progress = false

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
