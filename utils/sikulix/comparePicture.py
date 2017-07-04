def comparePicture(src, dst):
	sikuliEnv = os.environ.copy()
	sikuliEnv['sikuli_parent_image'] = src
	sikuliEnv['sikuli_sub_image'] = dst
	sikuliEnv['sikuli_action'] = 'find'

	cmd = r'C:\tools\sikuliX1.11\runsikulix.cmd -r C:\tools\sikuliX1.11\handleSubImage.sikuli'
	p = subprocess.Popen(cmd,
                        env = sikuliEnv,
                        stdout = subprocess.PIPE,
                        stderr = subprocess.PIPE,
                        shell = True)
	output,err = p.communicate()
	print output
	if output.find("[info] Exit code: 0") != -1:
		return True
	else:
		return False
