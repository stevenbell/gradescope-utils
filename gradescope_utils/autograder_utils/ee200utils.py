import re
import subprocess as sp
import signal
import os.path

# Small functions that get used repeatedly in creating and running tests
# on student C/C++ code.

def test_build(test, target, wdir, makefile='test_makefile', maketarget=None):
  """ Try building `target` in `wdir` using a `makefile` and send
      any output to the console.  Fail `test` if there is a problem.
      """
  # If the user didn't specify a separate makefile target, then just use the
  # name of the output file.  This is the normal case, except for phony targets.
  if maketarget is None:
    maketarget = target

  # If the target already exists, remove it
  # Simpler to put this here than require every makefile to have a `clean` command
  if os.path.isfile(wdir + target):
    os.remove(wdir + target)
    print("Removing submitted binary...")

  try:
    log = sp.check_output(["make", "-f", wdir + makefile, "--silent", "--always-make", "-C", wdir, maketarget], stderr = sp.STDOUT)

  except sp.CalledProcessError as e:
    test.fail("Failed to compile. Output is: {}".format(e.output.decode('utf-8')))

  if len(log.strip()) > 0:
    print("g++ output:\n{}".format(log.decode('utf-8')))

  # check that the output exists
  val = os.path.isfile(wdir + target)
  test.assertTrue(val, "Make/gcc/g++ didn't produce a binary")

  # Otherwise, we're all good
  print('Compiled successfully!')


def safe_run(test, command, timeout=5, **kwargs):
    """ Wrapper around check_output which fails the test if the code segfaults or
        takes too long.  A brief informative message is logged with the failure."""
    try:
        result = sp.check_output(command, timeout=timeout, **kwargs)

    except sp.CalledProcessError as e:
        if e.returncode == -signal.SIGSEGV:
            test.fail("Program segfaulted")
        else:
            # We don't know what students will return from main, so assume
            # anything other than a segfault is ok.
            result = e.output
    except sp.TimeoutExpired as e:
            test.fail("Program timed out after {} seconds".format(timeout))

    return result.decode('utf-8')

def harness_run(test, command, timeout=5, **kwargs):
    """Equivalent to safe_run, except that it prints different error messages.
       This function should be used for test harness operations, while safe_run
       should be used any time we're calling student code."""
    try:
        result = sp.check_output(command, timeout=timeout, **kwargs)

    except sp.CalledProcessError as e:
        if e.returncode == -signal.SIGSEGV:
            test.fail("Test harness segfaulted - check with teaching staff")
        else:
            test.fail("Test harness call failed - check with teaching staff")
    except TimeoutExpired as e:
            test.fail("Test harness timed out - check with teaching staff")

    return result.decode('utf-8')


def findString(haystack):
    matches = re.findall('###.*###', haystack)

    # There should be exactly one match, or we're hosed
    if len(matches) != 1:
        return None

    # Strip off the ###
    return matches[0][3:-3]

def findInteger(haystack):
    matches = re.findall('###[+-]?\d+###', haystack)

    # There should be exactly one match, or we're hosed
    if len(matches) != 1:
        return None

    # Strip off the ### and convert to an integer
    return int(matches[0][3:-3])

def findDouble(haystack):
    matches = re.findall('###[+-]?\d+\.\d+###', haystack)

    # There should be exactly one match, or we're hosed
    if len(matches) != 1:
        return None

    # Strip off the ### and convert to an integer
    return float(matches[0][3:-3])

