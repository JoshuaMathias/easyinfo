"""
Easy debug printing, timing, and variable attributes (length, width) for Python.

"""
import sys
import inspect
import time
from IPython.core.display import display, HTML

# Confounding variable names that we don't want from the stack.
# Not a comprehensive or generalized list
default_var_names = {'var', 'kwargs', 'script_name', 'mod_spec', 'interactivity', 'fd_obj', '_i10', '_i5', '_ih', 'loader', 'ncallbacks', '_exit_code', 'fd', 'parent', 'vname', 'metadata', 'pkg_name', '_i16', '_ii', '_i1', '__builtins__', 'msg_id', 'handler_func', 'cached'}

# Return the frame num_back frames ago.
def prev_frame(num_back=1):
  curr_frame = inspect.currentframe()
  for _ in range(num_back):
    curr_frame = curr_frame.f_back
  return curr_frame

# Print name of variable with value
def vname(var, num_back=2, func_name='vname'):
        """
        Gets the name of var. Does it from the out most frame inner-wards.
        :param var: variable to get name from.
        :return: string
        """
#         for fi in reversed(inspect.stack()):
#             names = [var_name for var_name, var_val in fi.frame.f_locals.items() if var_val is var and var_name not in default_var_names and var_name[0] != '_']
#             if len(names) > 0:
#                 return names[0]
        code = inspect.getframeinfo(prev_frame(num_back))[3][0]
        var_start = code.find(func_name+'(') + len(func_name) + 1 # +1 for (
        var_end = code.find(')', var_start)
        var_name = code[var_start:var_end]
        return var_name

def vline(num_back=2): # Credit to http://code.activestate.com/recipes/145297-grabbing-the-current-line-number-easily/
    """Returns the current line number in our program."""
    return prev_frame(num_back).f_lineno
      
# Print to standard error.
def eprint(*args, **kwargs):
  """Gets and prints the spreadsheet's header columns

  Parameters
  ----------
  file_loc : str
      The file location of the spreadsheet
  print_cols : bool, optional
      A flag used to print the columns to the console (default is False)

  Returns
  -------
  list
      a list of strings representing the header columns
  """
  print(args, file=sys.stderr, **kwargs)

def vstr(var, name=None, val=None, func_name='vstr', num_back=3):
  if not val:
    val = var
  msg = None
  if not name:
    name = vname(var, num_back, func_name)
  msg = name + ": " + str(val)
  return msg
  
def vprint(var, name=None, val=None, **kwargs):
  msg = vstr(var, name, val, func_name='vprint', num_back=4)
  print(msg, **kwargs)
  
def lstr(var, name=None, val=None, max_depth=10, func_name='vstr', num_back=3):
  attr_name = 'len'
  if not val:
    if hasattr(var, '__len__'):
      val = str(len(var))
      if len(var) > 0 and not isinstance(var[0], str):
        inner_var = var[0]
        depth = 0
        var_len = vlen(inner_var)
        attr_name = 'shape'
        while var_len > 1 and not isinstance(inner_var, str):
          if hasattr(inner_var, 'shape'):
            for axis in inner_var.shape:
              val += " x "+str(axis)
            break
          val += " x "+str(vlen(inner_var))
          if depth >= max_depth:
            break
          try:
            inner_var = inner_var[0]
          except TypeError:
            if vwid(inner_var):
              val += " x "+str(vwid(inner_var))
            break
          var_len = vlen(inner_var)
    elif hasattr(var, 'shape'):
      val = var.shape
      attr_name = 'shape'
    elif hasattr(var, 'size'):
      val = var.size
      attr_name = 'size'
    else:
      val = var
  if not name:
    name = vname(var, num_back, func_name)
  msg =  name + " (line " + "<a href='#'>"+str(vline(num_back))+"</a>" + ") " + attr_name + ": " + str(val)
  display(HTML(msg))
  return msg
  
# Print len
def lprint(var, name=None, val=None, **kwargs):
  msg = lstr(var, name, val, func_name='lprint', num_back=4)
  print(msg, **kwargs)

# Get str of all printing functions output
def astr(var, name=None, val=None):
  msg = lstr(var, name, val) + "\n" + vstr(var, "\t", val)
  return msg

# Call all printing functions for variable
def aprint(var, name=None, val=None, **kwargs):
  msg = astr(var, name, val)
  print(msg, **kwargs)

def vlen(var):
  try:
    if var is None:
      return 0
    elif hasattr(var, 'shape'):
      val = var.shape
    elif hasattr(var, '__len__'):
      val = len(var)
    elif hasattr(var, 'size'):
      val = var.size
    else:
      return 0
    if hasattr(val, '__len__'):
      if len(val):
        val = val[0]
      else:
        return 0
  except TypeError: # e.g. set that doesn't support indexing
    return 0
  return val

def vwid(var):
  try:
    if var is None:
      return 0
    elif hasattr(var, 'shape'):
      val = var.shape
    elif hasattr(var, '__len__'):
      if len(var) > 0:
        val = vlen(var[0])
      else:
        val = 0
    elif hasattr(var, 'size'):
      val = var.size
    else:
      return 0
  except TypeError: # e.g. set that doesn't support indexing
    return 0
  return val

_start_time = time.time()
_start_stack = [_start_time]
_last_time = None
_start_ids = {} # key: id, value: (start_time, last_time)

# id: Dictionary key, to track which start time and last time to use with end()
def start(id=None):
  """Gets and prints the spreadsheet's header columns

  Parameters
  ----------
  file_loc : str
      The file location of the spreadsheet
  print_cols : bool, optional
      A flag used to print the columns to the console (default is False)

  Returns
  -------
  list
      a list of strings representing the header columns
  """
  global _start_time, _last_time
  _start_time = time.time()
  _last_time = None

# msg: message to print before time. If only id is provided, 
# use id for msg. If neither is provided, use "Total time"
# id: 
def end(msg=None):
  end_time = time.time()
  global _start_time, _last_time
  total_time = end_time - _start_time
  if not msg:
    msg = 'Total time'
  if _last_time:
    since_time = end_time - _last_time
    msg += ': '+str(total_time)+' Time since last: '+str(since_time)
    print(msg)
  else:
    vprint(total_time, name=msg)
  _last_time = time.time()

# Return an int, removing any non-digit chars other than . or -
def to_int(text):
  text_digits = ""
  for c in text:
    if c.isdigit() or c == '.' or c == '-':
      text_digits += c
  if text_digits:
    return int(text_digits)
  else:
    return False