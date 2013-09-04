## dtrace-objc-leakobj

Objective-C is full of objects that you can't just pull from within DTrace and get information about. Even `NSString`s!
Creative hackers end up writing stuff like this:

```sh
dtrace -p 9508 -n 'objc$target::*postNotification*:entry {
	this->notification = copyinstr(*(user_addr_t*)copyin(arg2+2*sizeof(user_addr_t), sizeof(user_addr_t)));
	@[this->notification] = count();
}
tick-1s {
	printa(@); trunc(@);
}'
```

But this certainly doesn't scale beyond constant `CFString`s and extending the script to handle mutable
and variable-sized strings is real wizardry (go read a nodejs ustack helper for example).
And of course no way to get info on random objects!

Let's tackle the problem in a different way: let's automatically generate
probes that leak object's `-description` as a regular C string so we can `copyinstr` it.

### Getting started

```sh
% git clone https://github.com/proger/dtrace-objc-leakobj.git
% git clone https://github.com/proger/darwinkit.git
% ln -s darwinkit/lldb-run.py ~/local/bin/lldb-run # somewhere in your $PATH
% cd dtrace-objc-leakobj
% pip install -r pip.requirements # make sure you have this stuff
```

Generate the [NSNotificationCenter](https://developer.apple.com/library/ios/DOCUMENTATION/Cocoa/Reference/Foundation/Classes/NSNotificationCenter_Class/Reference/Reference.html)
sample and try to run it against a running `java` process with AppKit UI (find `ui.clj` in [darwinkit](https://github.com/proger/darwinkit)):

```sh
% make
```

### Demo

```sh
% make
rm -rf leaks
python leakexpand.py leakspecs/nsnotifications.yaml
make -C leaks/nsnotifications
dtrace -h -s nsnotifications.provider.d
clang -framework Foundation -shared -flat_namespace nsnotifications.m -o nsnotifications.dylib
make -C leaks/nsnotifications apply PID=$(pgrep -f clojure.main)
cat nsnotifications.lldb | lldb-run 16248	# lldb-run is in https://github.com/proger/darwinkit
attach: success
expr (void*)dlopen("/tank/proger/dev/dtrace-objc-leakobj/leaks/nsnotifications/nsnotifications.dylib", 0x2|0x8): <Status:  Success
Output Message:
(void *) $0 = 0x00007fba6dbaf100>
expr (void)hook_nsnotifications_apply(): <Status:  Success
Error Message:
<no result>>
sudo dtrace -m nsnotifications.dylib -l
   ID   PROVIDER            MODULE                          FUNCTION NAME
 6761 nsnotifications16248 nsnotifications.dylib newimp$$NSNotificationCenter$$postNotificationName$_object$_ notification-post
 6762 nsnotifications16248 nsnotifications.dylib newimp$$NSNotificationCenter$$postNotification$_ notification-post
 6763 nsnotifications16248 nsnotifications.dylib newimp$$NSNotificationCenter$$postNotificationName$_object$_userInfo$_ notification-post


% dtrace -q -n 'nsnotifications*:::notification-post { printf("%s %s\n", copyinstr(arg0), copyinstr(arg1)) }'
<CFNotificationCenter 0x7fba69504110 [0x7fff793ccfd0]> NSWindowDidMoveNotification
<CFNotificationCenter 0x7fba69504110 [0x7fff793ccfd0]> NSWindowDidMoveNotification
<CFNotificationCenter 0x7fba69504110 [0x7fff793ccfd0]> NSApplicationWillUpdateNotification
<CFNotificationCenter 0x7fba69504110 [0x7fff793ccfd0]> NSApplicationWillUpdateNotification
<CFNotificationCenter 0x7fba69504110 [0x7fff793ccfd0]> NSWindowDidUpdateNotification
<CFNotificationCenter 0x7fba69504110 [0x7fff793ccfd0]> NSWindowDidUpdateNotification
<CFNotificationCenter 0x7fba69504110 [0x7fff793ccfd0]> NSApplicationDidUpdateNotification
<CFNotificationCenter 0x7fba69504110 [0x7fff793ccfd0]> NSApplicationDidUpdateNotification
<CFNotificationCenter 0x7fba69504110 [0x7fff793ccfd0]> NSWindowDidMoveNotification
<CFNotificationCenter 0x7fba69504110 [0x7fff793ccfd0]> NSWindowDidMoveNotification
```
