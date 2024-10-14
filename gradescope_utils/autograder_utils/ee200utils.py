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

def test_coverage(test, source, target, wdir, makefile='test_makefile'):
  """ Runs gcov (generally on the student's test code) and fails the test if
      there is less than 100% coverage on the file under test. """
  try:
    log = sp.check_output(["make", "-f", wdir + makefile, "CFLAGS=-O0 --coverage", "--silent", "--always-make", "-C", wdir, target], stderr = sp.STDOUT)

  except sp.CalledProcessError as e:
    test.fail("Failed to compile for test coverage. Output is: {}".format(e.output.decode('utf-8')))

  safe_run(test, [wdir + target], cwd=wdir)

  # Somewhere around gcc 11, the naming of the gcov output files changed. As of gcc 11,
  # `gcc source1.c source2.c -o binary` generates files like binary-source1.gcda
  # See https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html
  gcov_name = f"{target}-{source}"

  result = harness_run(test, ["gcov", gcov_name], cwd=wdir)
  pctmatch = re.search(r'\d+\.?\d+\%', result)
  if pctmatch.group() != "100.00%":
    try:
      # If we didn't get 100% coverage, try to print the full coverage report
      gcov_file = open(wdir + source + ".gcov")
      print(gcov_file.read())
      print("\n\n")
    except Exception as e:
      print("Failed to open coverage report; only summary will be shown.")

    test.fail("Test coverage is only " + pctmatch.group())

  print("Test coverage is 100%!\n(Remember, this doesn't mean your code is correct, or that you're testing everything you should.  It does mean that your tests exercise every path through your program.)")


def run_valgrind(test, command, **kwargs):
  if not type(command) is list:
    command = [command]
  try:
    log = sp.check_output(["valgrind", "--tool=memcheck", "--leak-check=yes", "--error-exitcode=4"] + command, stderr = sp.STDOUT, **kwargs)

  except sp.CalledProcessError as e:
    test.fail("Valgrind reported errors:\n {}".format(e.output.decode('utf-8')))

  print("Valgrind clean!")


def safe_run(test, command, timeout=5, **kwargs):
    """ Wrapper around check_output which fails the test if the code segfaults or
        takes too long.  A brief informative message is logged with the failure."""
    try:
        result = sp.check_output(command, timeout=timeout, **kwargs)

    except sp.CalledProcessError as e:
        if e.returncode == -signal.SIGSEGV:
            test.fail("Program segfaulted")
        elif e.returncode == -signal.SIGABRT:
            test.fail("Program was aborted (assert failed or memory was corrupted)")
        else:
            # We don't know what students will return from main, so assume
            # anything other than a segfault/abort is ok.
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
    except sp.TimeoutExpired as e:
            test.fail("Test harness timed out - check with teaching staff")

    return result.decode('utf-8')


def findString(haystack):
    matches = re.findall(r'###(?:.|\s)*?###', haystack) # (?: non-capturing, *? non-greedy

    # There should be exactly one match, or we're hosed
    if len(matches) != 1:
        return None

    # Strip off the ###
    return matches[0][3:-3]

def findInteger(haystack):
    matches = re.findall(r'###[+-]?\d+###', haystack)

    # There should be exactly one match, or we're hosed
    if len(matches) != 1:
        return None

    # Strip off the ### and convert to an integer
    return int(matches[0][3:-3])

def findDouble(haystack):
    matches = re.findall(r'###[+-]?\d+\.\d+###', haystack)

    # There should be exactly one match, or we're hosed
    if len(matches) != 1:
        return None

    # Strip off the ### and convert to an integer
    return float(matches[0][3:-3])

