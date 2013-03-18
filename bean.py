# Bean is a tiny little worker friend (rqworker) that pulls tasks off the RQ redis work
# queue and crunches a job -- it's able to preload the opencv library ahead of time so
# we save some cycles and memory. Isn't it adorable?
# Taken from http://python-rq.org/docs/workers/
#
# Daniel Guilak <daniel.guilak@gmail.com> and Josef Lange <josef.d.lange@gmail.com>
# http://github.com/expresso-math/

import sys
from rq import Queue, Connection, Worker

# Preloading libraries

# It seems as though we'll have to have a python file with function definitions on both
# barista and roaster, otherwise bean will have no idea what to run -- you can't pass
# a function by name, apparently. Can still preload, though!

# REPLY: I think if you pass the function name with module name as well, it can figure out what it's looking for.
import roaster


# Provide queue names to listen to as arguments to this script,
# similar to rqworker
with Connection():
    qs = map(Queue, sys.argv[1:]) or [Queue()]

    w = Worker(qs)
    w.work()
