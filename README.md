dtrace-objc-leakobj
===================

Objective-C is full of objects that you can't just pull from within DTrace and get information about. Even `NSString`s!
Creative hackers end up writing stuff like this:

	dtrace -p 9508 -n 'objc$target::*postNotification*:entry { this->notification = copyinstr(*(user_addr_t*)copyin(arg2+2*sizeof(user_addr_t), sizeof(user_addr_t))); @[this->notification] = count(); }' -n 'tick-1s {printa(@); trunc(@); }'

But this certainly doesn't scale beyond constant `CFString`s and extending the script to handle mutable and variable-sized strings is real wizardry (go read nodejs ustack helper for example).
And of course no way to get info on random objects!

Let's tackle the problem in a different way: let's automatically generate probes that leak object's `-description` as a regular C string so we can `copyinstr` it.

Getting started
===============

	git clone https://github.com/proger/dtrace-objc-leakobj.git
	git clone https://github.com/proger/darwinkit.git
	ln -s darwinkit/lldb-run.py ~/local/bin/lldb-run # somewhere in your $PATH
	cd dtrace-objc-leakobj
	pip install -r pip.requirements # make sure you have this stuff
	make # generates the NSNotificationCenter sample and tries to run it against a running java process with AppKit UI (find `ui.clj` in `darwinkit`)
