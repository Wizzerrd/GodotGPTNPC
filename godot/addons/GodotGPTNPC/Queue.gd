extends Object

class_name Queue

var stack1 = []
var stack2 = []

func enqueue(element):
	stack1.append(element)

func dequeue():
	if not len(stack2):
		while len(stack1):
			stack2.append(stack1.pop_back())
	if len(stack2):
		return stack2.pop_back()
	else:
		return null

func empty():
	return not (len(stack1) or len(stack2))

func peek():
	if stack2.empty():
		while not stack1.empty():
			stack2.append(stack1.pop_back())
	if not stack2.empty():
		return stack2[stack2.size() - 1]
	else:
		return null
		
func length():
	return len(stack1) + len(stack2)
