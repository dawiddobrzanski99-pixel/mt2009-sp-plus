import os


def AppendFile(fileDirectory, text):
	if CreateIfDirectoryDoesNotExist(fileDirectory):
		a_file = open(fileDirectory, "a")
		a_file.write(text)
		a_file.close()


def WriteFile(fileDirectory, text):
	if CreateIfDirectoryDoesNotExist(fileDirectory):
		a_file = open(fileDirectory, "w")
		a_file.write(text)
		a_file.close()


def CreateIfDirectoryDoesNotExist(fileDirectory):
	directory = os.path.dirname(fileDirectory)
	# print directory
	if not os.path.exists(directory):
		try:
			os.makedirs(directory)
			return True
		except:
			return False
	else:
		return True


def DeleteLines(fileDirectory, lineIndexStart, lineIndexEnd, lineSeperator):
	try:
		a_file = open(fileDirectory, "r")
	except:
		return False

	text = a_file.read()
	a_file.close()

	# exclude lines from file
	idx = 0
	newText = ""
	for line in text.split(lineSeperator):
		# print line
		if idx < lineIndexStart or idx > lineIndexEnd:
			newText += line + lineSeperator
		idx += 1

	newText = newText[:-1]  # remove last seperator

	new_file = open(fileDirectory, "w+")
	new_file.write(newText)
	new_file.close()

	return True

def DeleteFile(fileDirectory):
	try:
		if os.path.isfile(fileDirectory):
			os.remove(fileDirectory)
	except Exception as e:
		print("Error occurred while trying to delete the file: {}".format(e))


def GetLineList(fileDirectory, lineSeperator):
	text = GetFileContent(fileDirectory)
	return text.split(lineSeperator)


def GetFileContent(fileDirectory):
	try:
		a_file = open(fileDirectory, "r")
	except:
		return ""

	text = a_file.read()
	if hasattr(a_file, 'close'):
		a_file.close()
	return text
