#文本匹配，发现匹配时就输出当前的匹配行前N行文本和当前行

from collections import deque

def search(lines, pattern, history=5):
	previous_lines = deque(maxlen=history)
	for line in lines:
		if pattern in line:
			yield line, previous_lines
		previous_lines.append(line)

if __name__ == '__main__':
	with open('saveLastNLines_data.log') as f:
		for line, prevlines in search(f, 'python', 3):
			for pline in prevlines:
				print(pline, end='')
			print(line, end='') #没有end=''，会打印空行
			print('-'*20)
